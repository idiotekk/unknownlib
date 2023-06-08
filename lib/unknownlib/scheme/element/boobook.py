from .base import Element
from ..logging import log
from typing import Any

__all__ = [
    "Boobook"
]


class Boobook(Element):
    
    def init(self):
        log.info(f"I am a boobook")

    def calc(self, time: int):
        log.info(f"Boobook {time} Boobook")
        
    def field(self, s) -> Any:
        if s == "name":
            return "kk"
        else:
            raise