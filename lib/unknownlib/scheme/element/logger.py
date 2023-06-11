from ..logging import log
from ..logging import default_formatter
import logging
from .base import Element
from pathlib import Path
from ...dt import utcnow


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
        
        self._filename = self.format_fileanme(self._params["filename"])
        Path(self._filename).parent.mkdir(parents=True, exist_ok=True)
        log.info(f"log file location: {self._filename}")

        self._level = self._params.get("level", 0)
        handler = logging.FileHandler(self._filename, mode="w")
        handler.setLevel(self._level)
        handler.setFormatter(default_formatter) # use default formatter
        log.addHandler(handler)

    def format_fileanme(self, f):

        f = f.replace("%TIMESTAMP%", utcnow().strftime("%Y%m%d_%H%M%S")).replace("%NAME%", self._name)
        if "%" in f:
            raise ValueError(f"expect no '%' remained in foramtted filename; got: {f}")
        return f