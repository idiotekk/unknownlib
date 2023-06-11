from enum import Enum


__all__ = [
    "Chain"
]

class Chain(Enum):
    
    ETHEREUM = 1
    GOERLI = 5
    OPTIMISM = 10
    POLYGON = 137
    AVALANCHE = 43114
    ARBITRUM = 42170
    SEPOLIA = 11155111
    
    def __hash__(self) -> int:
        return super().__hash__()

    @property
    def name(self):
        """ Lower case name.
        """
        return str(self).split(".")[-1].lower()

        

class ERC20(Enum):

    pass