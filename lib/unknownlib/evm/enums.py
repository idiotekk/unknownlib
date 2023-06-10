from enum import Enum


__all__ = [
    "Chain"
]

class Chain(Enum):
    
    ETHEREUM = 1
    OPTIMISM = 10
    ARBITRUM = 42170
    POLYGON = 137

    def __eq__(self, other):
        return self.__class__ is other.__class__ and other.value == self.value
    
    def __hash__(self) -> int:
        return super().__hash__()