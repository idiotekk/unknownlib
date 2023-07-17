from web3.contract.contract import Contract
from functools import cache
from enum import Enum
from abc import ABC, abstractmethod
from typing import Union, Optional
from .core import ContractBook, Chain, ERC20
from . import log


__all__ = [
    "ChainLinkPriceFeed",
    "Coin",
]

class Coin(Enum):
    """ A generic class of token not limited to EVM tokens.
    """

    BTC = 0
    ETH = 1
    LINK = 2
    AVAX = 3
    DOGE = 4
    UNI = 5
    APE = 6
    SPY = 7
    LTC = 8

    def __hash__(self):
        return self.value


_MarketableToken = Union[Coin, ERC20]


class PriceFeed(ABC):

    @abstractmethod
    def get_price(self, token: _MarketableToken, block_number: Optional[int]):
        pass


class ChainLinkPriceFeed(ContractBook, PriceFeed):
    """ Chainlink price feed.
    Use get_price method to get price.
    """

    _price_feed_addr_book = {
        Chain.ETHEREUM: {
            Coin.BTC: "0xf4030086522a5beea4988f8ca5b36dbc97bee88c",
            Coin.ETH: "0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419",
            Coin.APE: "0xd10abbc76679a20055e167bb80a24ac851b37056",
            Coin.DOGE: "0x2465cefd3b488be410b941b1d4b2767088e2a028",
            Coin.LTC: "0x6af09df7563c363b5763b9102712ebed3b9e859b",
        },
        Chain.ARBITRUM: {
            ERC20.ARBITRUM_WBTC: "0xd0C7101eACbB49F3deCcCc166d238410D6D46d57",
            ERC20.ARBITRUM_WETH: "0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612",
            ERC20.ARBITRUM_UNI: "0x9C917083fDb403ab5ADbEC26Ee294f6EcAda2720",
            ERC20.ARBITRUM_LINK: "0x86E53CF1B870786351Da77A57575e79CB55812CB",
        },
    }
   
    def _init_price_feed(self, token: _MarketableToken):
        chainlink_price_feed_abi = """[{"inputs":[{"internalType":"address","name":"_aggregator","type":"address"},{"internalType":"address","name":"_accessController","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"int256","name":"current","type":"int256"},{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":false,"internalType":"uint256","name":"updatedAt","type":"uint256"}],"name":"AnswerUpdated","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint256","name":"roundId","type":"uint256"},{"indexed":true,"internalType":"address","name":"startedBy","type":"address"},{"indexed":false,"internalType":"uint256","name":"startedAt","type":"uint256"}],"name":"NewRound","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"OwnershipTransferRequested","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"from","type":"address"},{"indexed":true,"internalType":"address","name":"to","type":"address"}],"name":"OwnershipTransferred","type":"event"},{"inputs":[],"name":"acceptOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"accessController","outputs":[{"internalType":"contract AccessControllerInterface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"aggregator","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_aggregator","type":"address"}],"name":"confirmAggregator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint8","name":"","type":"uint8"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"description","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_roundId","type":"uint256"}],"name":"getAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"getRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_roundId","type":"uint256"}],"name":"getTimestamp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestAnswer","outputs":[{"internalType":"int256","name":"","type":"int256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRound","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"latestTimestamp","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint16","name":"","type":"uint16"}],"name":"phaseAggregators","outputs":[{"internalType":"contract AggregatorV2V3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"phaseId","outputs":[{"internalType":"uint16","name":"","type":"uint16"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_aggregator","type":"address"}],"name":"proposeAggregator","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"proposedAggregator","outputs":[{"internalType":"contract AggregatorV2V3Interface","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint80","name":"_roundId","type":"uint80"}],"name":"proposedGetRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"proposedLatestRoundData","outputs":[{"internalType":"uint80","name":"roundId","type":"uint80"},{"internalType":"int256","name":"answer","type":"int256"},{"internalType":"uint256","name":"startedAt","type":"uint256"},{"internalType":"uint256","name":"updatedAt","type":"uint256"},{"internalType":"uint80","name":"answeredInRound","type":"uint80"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_accessController","type":"address"}],"name":"setController","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"_to","type":"address"}],"name":"transferOwnership","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"version","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]"""
        if isinstance(token, ERC20):
            assert token.chain == self._chain, "cross-chain price feed of evn tokens is not supported to avoid confusion"
        self.init_contract(
            addr=self._price_feed_addr_book[self._chain][token],
            abi=chainlink_price_feed_abi,
            key=self._price_feed_label(token),
            if_exists="skip")
    
    @cache
    def _price_feed_contract(self, token: _MarketableToken) -> Contract:
        self._init_price_feed(token)
        return self.contract(self._price_feed_label(token))

    @cache
    def _price_feed_label(self, token: _MarketableToken) -> str:
        return f"{self.__class__}:{token.name}"
            
    def get_price(self,
            token: _MarketableToken,
            *,
            block_number: Optional[int]=None) -> float:
        """
        Return the latest price of token as of block_number.
        If block_number is None, then return the latest price of the latest block.
        """
        price_raw = self._price_feed_contract(token).functions["latestAnswer"]().call(block_identifier=block_number)
        return price_raw / (10**self.__decimals(token))

    @cache
    def __decimals(self, token: _MarketableToken) -> int:
        return self._price_feed_contract(token).functions["decimals"]().call()