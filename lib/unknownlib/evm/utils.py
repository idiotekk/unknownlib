"""
Some generic utility functions.
"""
from . import log
from .core import Web3Connector
import pandas as pd
import typing
from hexbytes import HexBytes


__all__ = [
    "flatten_dict",
    "interpolate_timestamp",
]


def flatten_dict(d: dict, sep: str="_") -> dict:

    def _flatten_dict_helper( # i really hate this function name
        d: typing.Any,
        sep: str="_") -> typing.Any:

        if isinstance(d, HexBytes):
            return d.hex()
        elif hasattr(d, "items"):
            d_ = {}
            for k, v in d.items():
                assert isinstance(k, str), f"key can only be str, got {k} with type {type(k)}"
                if hasattr(v, "items"):
                    for kk, vv in v.items():
                        d_[f"{k}{sep}{kk}"] = _flatten_dict_helper(vv)
                else:
                    d_[k] = _flatten_dict_helper(v)
            return d_
        else:
            return d

    return _flatten_dict_helper(d)


def interpolate_timestamp(d: pd.DataFrame, w3: Web3Connector,  block_number_col: str="blockNumber"):

    min_block = int(d[block_number_col].min())
    max_block = int(d[block_number_col].max())
    tz = "UTC"
    stime = pd.to_datetime(w3.eth.get_block(min_block).timestamp * 1e9,utc=True).tz_convert(tz)
    etime = pd.to_datetime(w3.eth.get_block(max_block).timestamp * 1e9,utc=True).tz_convert(tz)
    if min_block == max_block:
        d["timestamp"] = stime
    else:
        d["timestamp"] = (etime - stime) / (max_block - min_block) * (d[block_number_col] - min_block) + stime
    return d