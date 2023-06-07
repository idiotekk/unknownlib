from . import log
import os
from .base import Element
from .optimizer import Optimizer


class Executor(Element):
    
    def calc(self):

        side, qty = self.get_element_by_type(Optimizer).get_order()
        pass