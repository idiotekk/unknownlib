import re
from typing import Union, Self
from functools import cache
from web3 import Web3


__all__ = [
    "Addr",
]


class Addr:

    _value: str # checksum address

    def __init__(self, value: Union[str, Self]) -> None:
        if isinstance(value, Addr):
            self._value = value
        elif isinstance(value, str) and self.is_valid(value):
            self._value = self.to_checksum_address(value)
        else:
            raise ValueError(f"invalid address {value}")

    @staticmethod
    def is_valid(value: str) -> bool:
        pattern = "^0x[0-9A-Fa-f]{40}$"
        return re.match(pattern, value) is not None

    @staticmethod
    @cache
    def to_checksum_address(value) -> str:
        return Web3.to_checksum_address(value)

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, __other: Union[str, Self]) -> bool:
        return self.value == Addr(__other).value

    def __hash__(self) -> int:
        return self.value.__hash__()

    def to_topic(self) -> str:
        """ Convert to event topic.
        TODO: better way than str.replace?
        """
        return self.value.replace("0x", "0x" + "0" * 24)