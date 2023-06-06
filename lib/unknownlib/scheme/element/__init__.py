from .. import log
from .base import *
from .logger import *
from .scheduler import *
from .boobook import *


for name, type_ in {
    "scheduler": Scheduler,
    "boobook": Boobook,
    "logger": Logger,
}.items():
    ElementCatalog.register_element_type(name, type_)