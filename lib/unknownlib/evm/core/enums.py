from enum import Enum
from typing import Self, List, Dict, Any
from functools import cache
import json
from .types import check_type


__all__ = [
    "Chain",
    "ERC20",
    "ERC721",
    "ActionIfItemExists",
]


class Chain(Enum):
    
    ETHEREUM = 1
    GOERLI = 5
    OPTIMISM = 10
    BINANCE = 56
    POLYGON = 137
    ARBITRUM = 42161
    AVALANCHE = 43114
    SEPOLIA = 11155111

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)
    
    def __hash__(self) -> int:
        return super().__hash__()


class ERC20(Enum):

    # ETHEREUM
    USDT = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    USDC = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
    DAI  = "0x6B175474E89094C44Da98b954EedeAC495271d0F"
    UNI  = "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"
    APE  = "0x4d224452801ACEd8B2F0aebE155379bb5D594381"
    FRAX = "0x853d955aCEf822Db058eb8505911ED77F175b99e"
    WETH = "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    WBTC = "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
    # GOERLI
    GOERLI_USDC    = "0xa2bd28f23A78Db41E49db7d7B64b6411123a8B85"
    # ARBITRUM
    ARBITRUM_WBTC  = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
    ARBITRUM_WETH  = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
    ARBITRUM_UNI   = "0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0"
    ARBITRUM_LINK  = "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4"
    ARBITRUM_USDC  = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8" # bridged USDC
    ARBITRUM_USDCA = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" # official USDC on arb
    ARBITRUM_USDT  = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
    ARBITRUM_DAI   = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
    ARBITRUM_FRAX  = "0x17FC002b466eEc40DaE837Fc4bE5c67993ddBd6F"

    @property
    @cache
    def abi(self) -> List[Dict[str, Any]]:
        return json.loads('[{"constant": true, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"payable": true, "stateMutability": "payable", "type": "fallback"}, {"anonymous": false, "inputs": [{"indexed": true, "name": "owner", "type": "address"}, {"indexed": true, "name": "spender", "type": "address"}, {"indexed": false, "name": "value", "type": "uint256"}], "name": "Approval", "type": "event"}, {"anonymous": false, "inputs": [{"indexed": true, "name": "from", "type": "address"}, {"indexed": true, "name": "to", "type": "address"}, {"indexed": false, "name": "value", "type": "uint256"}], "name": "Transfer", "type": "event"}]')

    @property
    @cache
    def chain(self) -> Chain:
        _ = self.name.split("_")
        if len(_) == 1:
            return Chain.ETHEREUM
        elif len(_) == 2:
            return Chain[_[0]]
        else:
            raise ValueError(f"cannot parse chain from {self.name}")

    @property
    def addr(self) -> str:
        return self.value


class ERC721(Enum):

    abi: list = json.loads('[{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"approve","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"mint","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"safeTransferFrom","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"bytes","name":"_data","type":"bytes"}],"name":"safeTransferFrom","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"bool","name":"approved","type":"bool"}],"name":"setApprovalForAll","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"constant":false,"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"transferFrom","outputs":[],"payable":false,"stateMutability":"nonpayable","type":"function"},{"inputs":[],"payable":false,"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"},{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Transfer","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"approved","type":"address"},{"indexed":true,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"owner","type":"address"},{"indexed":true,"internalType":"address","name":"operator","type":"address"},{"indexed":false,"internalType":"bool","name":"approved","type":"bool"}],"name":"ApprovalForAll","type":"event"},{"constant":true,"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getApproved","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"operator","type":"address"}],"name":"isApprovedForAll","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"ownerOf","outputs":[{"internalType":"address","name":"","type":"address"}],"payable":false,"stateMutability":"view","type":"function"},{"constant":true,"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"payable":false,"stateMutability":"view","type":"function"}]')


class ActionIfItemExists(Enum):
    
    SKIP = 0
    RAISE = 1
    OVERRIDE = 2

    @classmethod
    def from_str(cls, s: str) -> Self:
        return cls[s.upper()]

    def __eq__(self, __other: Self) -> bool:
        check_type(__other, self.__class__)
        return self.value == __other.value