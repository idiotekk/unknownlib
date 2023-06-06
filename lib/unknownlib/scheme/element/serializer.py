from .base import Element
from ...io import save_df
from typing import Dict
import pandas as pd


__all__ = [
    "Serializer"
]


class Serializer(Element):
    
    _data: Dict[str, list] = {}

    def init(self):
        self._data["time"] = []
        for var in self._params["vars"]:
            self._data[var] = []
    
    def calc(self, time):
        self._data["time"].append(time)
        for var in self._params["vars"]:
            self._data[var].append(self.snap_var(var))

    def done(self):
        df = pd.DataFrame(self._data)
        save_df(
            df,
            self._params["output_file"],
            index=False,
        )

    def snap_var(self, var):
        elem_name, field = var.split(".")
        return self.get_element(elem_name).field(field)