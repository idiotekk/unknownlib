"""
Some generic utility functions.
"""
from . import log
import typing
from hexbytes import HexBytes


__all__ = [
    "flatten_dict"
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