"""Ansible Inventory class to generate final hostvars based on group_vars and host_vars."""
from ansible.inventory.manager import InventoryManager  # pylint: disable=import-error
from ansible.parsing.dataloader import DataLoader  # pylint: disable=import-error
from ansible.vars.manager import VariableManager  # pylint: disable=import-error
from ansible.template import Templar  # pylint: disable=import-error


# Referenced https://github.com/fgiorgetti/qpid-dispatch-tests/ for the below class
class AnsibleInventory:
    """AnsibleInventory."""

    def __init__(self, inventory=None, extra_vars=None):
        """Imitates Ansible Inventory Loader.

        Args:
            inventory (str): Path to Ansible Inventory files.
            extra_vars (dict): Extra Vars passed at run time.
        """
        self.inventory = inventory
        self.loader = DataLoader()
        self.inv_mgr = InventoryManager(loader=self.loader, sources=self.inventory)
        self.var_mgr = VariableManager(loader=self.loader, inventory=self.inv_mgr)
        # TODO As of Ansible==2.8.0 the extra_vars property cannot be set to VariableManager
        #      This needs to be investigated and fixed properly
        self.extra_vars = extra_vars or {}

    def get_hosts_containing(self, var=None):
        """Gets hosts that have a value for ``var``.

        If ``var`` is None, then all hosts in the inventory will be returned.

        Args:
            var (str): The variable to use to restrict hosts.

        Returns:
            list: All ansible.inventory.host.Host objects that define ``var``.
        """
        all_hosts = self.inv_mgr.get_hosts()
        if var is None:
            return all_hosts

        # Only add hosts that define the variable.
        hosts_with_var = [host for host in all_hosts if var in self.var_mgr.get_vars(host=host)]
        return hosts_with_var

    def get_host_vars(self, host):
        """Retrieves Jinja2 rendered variables for ``host``.

        Args:
            host (ansible.inventory.host.Host): The host to retrieve variable data from.

        Returns:
            dict: The variables defined by the ``host`` in Ansible Inventory.
        """
        data = self.var_mgr.get_vars(host=host)
        templar = Templar(variables=data, loader=self.loader)
        return templar.template(data, fail_on_undefined=False)

    def get_clean_host_vars(self, host):
        """Return clean hostvars for a given host, cleaned up of all keys inserted by Templar.

        Args:
            host (ansible.inventory.host.Host): The host to retrieve variable data from.

        Raises:
            TypeError: When "magic_vars_to_evaluate" is declared in an Ansible inventory file and is not of type list,
            a type error is raised

        Returns:
            dict: clean hostvars
        """
        keys_cleanup = [
            "inventory_file",
            "inventory_dir",
            "inventory_hostname",
            "inventory_hostname_short",
            "group_names",
            "ansible_facts",
            "playbook_dir",
            "ansible_playbook_python",
            "groups",
            "omit",
            "ansible_version",
            "ansible_config_file",
            "schema_enforcer_schema_ids",
            "schema_enforcer_strict",
            "schema_enforcer_automap_default",
            "magic_vars_to_evaluate",
        ]

        hostvars = self.get_host_vars(host)

        # Extract magic vars which should be evaluated
        magic_vars_to_evaluate = hostvars.get("magic_vars_to_evaluate", [])
        if not isinstance(magic_vars_to_evaluate, list):
            raise TypeError(f"magic_vars_to_evaluate variable configured for host {host.name} must be of type list")

        keys_cleanup = list(set(keys_cleanup) - set(magic_vars_to_evaluate))

        for key in keys_cleanup:
            if key in hostvars:
                del hostvars[key]

        return hostvars

    @staticmethod
    def get_applicable_schemas(hostvars, smgr, declared_schema_ids, automap):
        """Get applicable schemas.

        Search an explicit mapping to determine the schemas which should be used to validate hostvars
        for a given host.

        If an explicit mapping is not defined, correlate top level keys in the structured data with top
        level properties in the schema to acquire applicable schemas.

        Args:
            hostvars (dict): dictionary of cleaned host vars which will be evaluated against schema
            smgr (schema_enforcer.schemas.manager.SchemaManager): SchemaManager object
            declared_schema_ids (list): A list of declared schema IDs inferred from schema_enforcer_schemas variable
            automap (bool): Whether or not to use the `automap` feature to automatically map top level hostvar keys
                to top level schema definition properties if no schema ids are declared (list of schema ids is empty)

        Returns:
            applicable_schemas (dict): dictionary mapping schema_id to schema obj for all applicable schemas
        """
        applicable_schemas = {}
        for key in hostvars.keys():
            # extract applicable schema ID to JsonSchema objects if schema_ids are declared
            if declared_schema_ids:
                for schema_id in declared_schema_ids:
                    applicable_schemas[schema_id] = smgr.schemas[schema_id]

            # extract applicable schema ID to JsonSchema objects based on host var to top level property mapping.
            elif automap:
                for schema in smgr.schemas.values():
                    if key in schema.top_level_properties:
                        applicable_schemas[schema.id] = schema
                        continue

        return applicable_schemas

    def get_schema_validation_settings(self, host):
        """Parse Ansible Schema Validation Settings from a host object.

        Validate settings or ensure an error is raised in the event an invalid parameter is
        configured in the host file.

        Args:
            host (AnsibleInventory.host): Ansible Inventory Host Object

        Raises:
            TypeError: Raised when one of the schema configuration parameters is of the wrong type
            ValueError: Raised when one of the schema configuration parameters is incorrectly configured

        Returns:
            (dict): Dict of validation settings with keys "declared_schema_ids", "strict", and "automap"
        """
        # Generate host_var and automatically remove all keys inserted by ansible
        hostvars = self.get_host_vars(host)

        # Extract declared_schema_ids from hostvar setting
        declared_schema_ids = []
        if "schema_enforcer_schema_ids" in hostvars:
            if not isinstance(hostvars["schema_enforcer_schema_ids"], list):
                raise TypeError(f"'schema_enforcer_schema_ids' attribute defined for {host.name} must be of type list")
            declared_schema_ids = hostvars["schema_enforcer_schema_ids"]

        # Extract whether to use a strict validator or a loose validator from hostvar setting
        strict = False
        if "schema_enforcer_strict" in hostvars:
            if not isinstance(hostvars["schema_enforcer_strict"], bool):
                raise TypeError(f"'schema_enforcer_strict' attribute defined for {host.name} must be of type bool")
            strict = hostvars["schema_enforcer_strict"]

        automap = True
        if "schema_enforcer_automap_default" in hostvars:
            if not isinstance(hostvars["schema_enforcer_automap_default"], bool):
                raise TypeError(
                    f"'schema_enforcer_automap_default' attribute defined for {host.name} must be of type bool"
                )
            automap = hostvars["schema_enforcer_automap_default"]

        # Raise error if settings are set incorrectly
        if strict and not declared_schema_ids:
            msg = (
                f"The 'schema_enforcer_strict' parameter is set for {host.name} but the 'schema_enforcer_schema_ids' parameter does not declare a schema id. "
                "The 'schema_enforcer_schema_ids' parameter MUST be defined as a list declaring only one schema ID if 'schema_enforcer_strict' is set."
            )
            raise ValueError(msg)

        if strict and declared_schema_ids and len(declared_schema_ids) > 1:
            msg = (
                f"The 'schema_enforcer_strict' parameter is set for {host.name} but the 'schema_enforcer_schema_ids' parameter declares more than one schema id. "
                "The 'schema_enforcer_schema_ids' parameter MUST be defined as a list declaring only one schema ID if 'schema_enforcer_strict' is set."
            )
            raise ValueError(msg)

        return {
            "declared_schema_ids": declared_schema_ids,
            "strict": strict,
            "automap": automap,
        }

    def print_schema_mapping(self, hosts, limit, smgr):
        """Print host to schema IDs mapping.

        Args:
            hosts (list): A list of ansible.inventory.host.Host objects for which the mapping should be printed
            limit (str): The host to which to limit the search
            smgr (schema_enforcer.schemas.manager.SchemaManager): Schema manager which handles schema objects
        """
        print_dict = {}
        for host in hosts:
            if limit and host.name != limit:
                continue

            # Get hostvars
            hostvars = self.get_clean_host_vars(host)

            # Acquire validation settings for the given host
            schema_validation_settings = self.get_schema_validation_settings(host)
            declared_schema_ids = schema_validation_settings["declared_schema_ids"]
            automap = schema_validation_settings["automap"]

            # Validate declared schemas exist
            smgr.validate_schemas_exist(declared_schema_ids)

            # Acquire schemas applicable to the given host
            applicable_schemas = self.get_applicable_schemas(hostvars, smgr, declared_schema_ids, automap)

            # Add an element to the print dict for this host
            print_dict[host.name] = list(applicable_schemas.keys())

        if print_dict:
            print("{:25} Schema ID".format("Ansible Host"))  # pylint: disable=consider-using-f-string
            print("-" * 80)
            print_strings = []
            for hostname, schema_ids in print_dict.items():
                print_strings.append(f"{hostname:25} {schema_ids}")
            print("\n".join(sorted(print_strings)))
