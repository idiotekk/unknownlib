from .base import Element
from . import log


__all__ = [
    "Scheduler"
]


class Scheduler(Element):

    _count = 0
    _calc_times = None

    def init(self):
        self._calc_times = range(
            self._params["start"],
            self._params["end"],
        )

    def calc(self, time: int):
        pass

    def schedule_calc_times(self):
        for time_ in self._calc_times:
            log.info(f"scheduling calc time {time_}")
            yield time_