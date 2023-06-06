from .base import Element
from . import log


class Boobook(Element):
    
    def init(self):
        log.info(f"I am a boobook")

    def calc(self, time: int):
        log.info(f"Boobook {time} Boobook")