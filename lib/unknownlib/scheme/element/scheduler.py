from .base import Element
from ..logging import log
import pandas as pd
import time


__all__ = [
    "Scheduler",
    "SimpleScheduler",
    "FreqScheduler",
]


class Scheduler(Element):

    _count = 0
    _calc_times = None

    def calc(self, time: int):
        pass
    
    def schedule(self):
        raise NotImplementedError()


class SimpleScheduler(Scheduler):

    def init(self):
        self._calc_times = range(
            self._params["start"],
            self._params["end"],
        )

    def schedule(self) -> int:
        for time_ in self._calc_times:
            log.info(f"scheduling calc time {time_}")
            yield time_


class FreqScheduler(Scheduler):

    _freq: pd.Timedelta
    _is_live: bool
    _cur_time: pd.Timestamp
    _start: pd.Timestamp
    _end: pd.Timestamp

    def init(self):
        self._freq = pd.Timedelta(self._params["freq"])
        self._is_live = self._params["is_live"]
        self._parse_start_end()
        self._cur_time = self._start

    def _parse_start_end(self):
        if self._is_live:
            self._start = pd.Timestamp.now().round(self._freq)
            if self._params.get("end"):
                self._end = pd.to_datetime(self._params["end"])
            else:
                self._end = self._start + pd.Timedelta("24h")
        else:
            self._start = pd.to_datetime(self._params["start"])
            self._end = pd.to_datetime(self._params["end"])
        log.info(f"start: {self._start}, end: {self._end}")

    def schedule(self) -> pd.Timestamp:
        while True:
            self._refresh_cur_time()
            if self._cur_time > self._end:
                log.info(f"cur time {self._cur_time} > end time {self._end}; will stop.")
                break
            else:
                yield self._cur_time

    @staticmethod
    def _real_time():
        return pd.Timestamp.now()

    def _refresh_cur_time(self):
        if self._is_live:
            while self._cur_time <= self._real_time():
                self._cur_time += self._freq
            s = (self._cur_time - self._real_time()).total_seconds()
            log.info(f"sleeping until {self._cur_time}")
            time.sleep(s)
        else:
            self._cur_time += self._freq