from . import log
from .. import default_formatter
import logging
from .base import Element
from pathlib import Path


__all__ = [
    "Logger"
]


class Logger(Element):
    """ Add additional handler to default logger.
    """
    _filename: str
    _level: int

    def calc(self, time: int):
        pass
    
    def init(self):
        
        self._filename = self._params["filename"]
        Path(self._filename).parent.mkdir(parents=True, exist_ok=True)
        self._level = self._params.get("level", 0)
        handler = logging.FileHandler(self._filename, mode="w")
        handler.setLevel(self._level)
        handler.setFormatter(default_formatter) # use default formatter
        log.addHandler(handler)