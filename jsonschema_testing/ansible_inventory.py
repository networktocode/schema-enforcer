from ansible.inventory.manager import InventoryManager
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.template import Templar


# Referenced https://github.com/fgiorgetti/qpid-dispatch-tests/ for the below class
class AnsibleInventory(object):
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
        hosts_with_var = [
            host for host in all_hosts if var in self.var_mgr.get_vars(host=host)
        ]
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

        KEYS_CLEANUP = [ 'inventory_file', 'inventory_dir', 'inventory_hostname', 'inventory_hostname_short', 'group_names', 'ansible_facts', 'playbook_dir', 'ansible_playbook_python', 
        'groups', 'omit', 'ansible_version']

        hv = self.get_host_vars(host)
        
        for key in KEYS_CLEANUP:
            if key in hv:
                del hv[key]

        return hv 