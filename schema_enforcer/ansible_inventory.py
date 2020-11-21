"""Ansible Inventory class to generate final hostvars based on group_vars and host_vars."""
from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.template import Templar


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
        self.extra_vars = extra_vars or dict()

    def get_hosts_containing(self, var=None):
        """Gets hosts that have a value for ``var``.

        If ``var`` is None, then all hosts in inventory will be returned.

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
            host (ansible.inventory.host.Host): The host to retrieve variable data.

        Returns:
            dict: The variables defined by the ``host`` in Ansible Inventory.
        """
        data = self.var_mgr.get_vars(host=host)
        templar = Templar(variables=data, loader=self.loader)
        return templar.template(data, fail_on_undefined=False)

    def get_clean_host_vars(self, host):
        """Return clean hostvars for a given host, cleaned up of all keys inserted by Templar.

        Args:
            host (ansible.inventory.host.Host): The host to retrieve variable data.

        Returns:
            dict: clean hostvar
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
            "schema_enforcer_schemas",
            "schema_enforcer_strict",
        ]

        hostvars = self.get_host_vars(host)

        for key in keys_cleanup:
            if key in hostvars:
                del hostvars[key]

        return hostvars

    @staticmethod
    def get_applicable_schemas(hostvars, smgr, mapping):
        """Get applicable schemas.

        Search an explicit mapping to determine the schemas which should be used to validate hostvars
        for a given host.

        If an explicit mapping is not defined, correlate top level keys in the structured data with top
        level properties in the schema to acquire applicable schemas.

        Args:
            hostvars (dict): dictionary of cleaned host vars which will be evaluated against schema

        Returns:
            applicable_schemas (dict): dictionary mapping schema_id to schema obj for all applicable schemas
        """
        applicable_schemas = {}
        for key in hostvars.keys():
            if mapping and key in mapping:
                applicable_schemas = {schema_id: smgr.schemas[schema_id] for schema_id in mapping[key]}
            else:
                applicable_schemas = {
                    schema.id: smgr.schemas[schema.id]
                    for schema in smgr.schemas.values()
                    if key in schema.top_level_properties
                }

        return applicable_schemas

    def get_schema_validation_settings(self, host):
        """Parse Ansible Schema Validation Settings from a host object.

        Validate settings to ensure an error is raised in the event an invalid parameter is
        configured in the host file.

        Args:
            host (AnsibleInventory.host): Ansible Inventory Host Object

        Raises:
            TypeError: Raised when one of the scehma configuration parameters is of the wrong type
            ValueError: Raised when one of the schema configuration parameters is incorrectly configured

        Returns:
            mapping (list): List of schema IDs against which to validate ansible vars
            strict (bool): Whether or not to use strict validation while validating the schema
        """
        # Generate host_var and automatically remove all keys inserted by ansible
        hostvars = self.get_host_vars(host)

        # Extract mapping from hostvar setting
        mapping = None
        if "schema_enforcer_schemas" in hostvars:
            if not isinstance(hostvars["schema_enforcer_schemas"], list):
                raise TypeError(f"'schema_enforcer_schemas' attribute defined for {host.name} must be of type list")
            mapping = hostvars["schema_enforcer_schemas"]
            del hostvars["schema_enforcer_schemas"]

        # Extract whether to use a strict validator or a loose validator from hostvar setting
        strict = False
        if "schema_enforcer_strict" in hostvars:
            if not isinstance(hostvars["schema_enforcer_strict"], bool):
                raise TypeError(f"'schema_enforcer_strict' attribute defined for {host.name} must be of type bool")
            strict = hostvars["schema_enforcer_strict"]
            del hostvars["schema_enforcer_strict"]

        # Raise error if settings are set incorrectly
        if strict and not mapping:
            msg = (
                f"The 'schema_enforcer_strict' parameter is set for {host.name} but the 'schema_enforcer_schemas' parameter does not declare a schema id. "
                "The 'schema_enforcer_schemas' parameter MUST be defined as a list declaring only one schema ID if 'schema_enforcer_strict' is set."
            )
            raise ValueError(msg)

        if strict and mapping and len(mapping) > 1:
            if mapping:
                msg = f"The 'schema_enforcer_strict' parameter is set for {host.name} but the 'schema_enforcer_schemas' parameter declares more than one schema id. "
                msg += "The 'schema_enforcer_schemas' parameter MUST be defined as a list declaring only one schema ID if 'schema_enforcer_strict' is set."
            raise ValueError(msg)

        return mapping, strict
