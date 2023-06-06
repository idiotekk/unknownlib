from .. import log
from .base import *
from .logger import *
from .scheduler import *
from .boobook import *
from .serializer import *


for _name, _type in {
    "scheduler": Scheduler,
    "boobook": Boobook,
    "logger": Logger,
    "serializer": Serializer
}.items():
    ElementCatalog.register_element_type(_name, _type)