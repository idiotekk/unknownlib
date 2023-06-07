from . import log
from .base import Element
from typing import Tuple


class Optimizer(Element):
    
    
    def calc(self, time):
        pass

    def get_order(self) -> Tuple(bool, float):
        pass