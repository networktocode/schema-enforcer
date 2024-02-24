from .dns import Dns
from .hostname import Hostname
from .interfaces import Interfaces  # , Interface, InterfaceTypes

from schema_enforcer.schemas.manager import PydanticManager


manager1 = PydanticManager(models=[Hostname, Interfaces])
manager2 = PydanticManager(prefix="pydantic", models=[Hostname, Interfaces, Dns])
