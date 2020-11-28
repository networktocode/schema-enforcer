"""Custom inventory Plugin for testing."""

from ansible.plugins.inventory import BaseInventoryPlugin, Constructable, Cacheable

class InventoryModule(BaseInventoryPlugin, Constructable, Cacheable):

    NAME = "simpleplugin"

    def verify_file(self, path):
        """Verify file method, return True for this test plugin."""
        return True
    
    def parse(self, inventory, loader, path, cache=True):
        """Parse method, add host from simple list of dictionaries."""
        super(InventoryModule, self).parse(inventory, loader, path, cache)
        for device in [{"name": "leaf3", "group": "leaf"}, {"name": "leaf4", "group": "leaf"}]:
            self.inventory.add_host(device['name'], group=device['group'])
