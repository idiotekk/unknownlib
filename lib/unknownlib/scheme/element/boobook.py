from .base import Element
from . import log

__all__ = [
    "Boobook"
]


class Boobook(Element):
    
    def init(self):
        log.info(f"I am a boobook")

    def calc(self, time: int):
        log.info(f"Boobook {time} Boobook")
        
    def field(self, s):
        if s == "name":
            return "kk"
        else:
            raise