from enum import Enum
import json


__all__ = [
    "Chain",
    "ERC20",
]

class Chain(Enum):
    
    ETHEREUM = 1
    GOERLI = 5
    OPTIMISM = 10
    POLYGON = 137
    AVALANCHE = 43114
    ARBITRUM = 42170
    SEPOLIA = 11155111

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)
    
    def __hash__(self) -> int:
        return super().__hash__()

    @property
    def name(self):
        """ Lower case name.
        """
        return str(self).split(".")[-1].lower()


class ERC20(Enum):

    ARBITRUM_WBTC  = "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f"
    ARBITRUM_WETH  = "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1"
    ARBITRUM_UNI   = "0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0"
    ARBITRUM_LINK  = "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4"
    ARBITRUM_USDC  = "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8"
    ARBITRUM_USDT  = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"
    ARBITRUM_DAI   = "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1"
    ARBITRUM_FRAX  = "0x17FC002b466eEc40DaE837Fc4bE5c67993ddBd6F"

    @property
    def abi(self):
        return json.loads('[{"constant": true, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_spender", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_from", "type": "address"}, {"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transferFrom", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": true, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "payable": false, "stateMutability": "view", "type": "function"}, {"constant": false, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "payable": false, "stateMutability": "nonpayable", "type": "function"}, {"constant": true, "inputs": [{"name": "_owner", "type": "address"}, {"name": "_spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "payable": false, "stateMutability": "view", "type": "function"}, {"payable": true, "stateMutability": "payable", "type": "fallback"}, {"anonymous": false, "inputs": [{"indexed": true, "name": "owner", "type": "address"}, {"indexed": true, "name": "spender", "type": "address"}, {"indexed": false, "name": "value", "type": "uint256"}], "name": "Approval", "type": "event"}, {"anonymous": false, "inputs": [{"indexed": true, "name": "from", "type": "address"}, {"indexed": true, "name": "to", "type": "address"}, {"indexed": false, "name": "value", "type": "uint256"}], "name": "Transfer", "type": "event"}]')

    @property
    def chain(self):
        return Chain[self.name.split("_")[0]]

    @property
    def addr(self):
        return self.value