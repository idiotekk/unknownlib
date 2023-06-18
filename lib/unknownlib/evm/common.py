import os
import re
import requests

from typing import Optional, Union, Dict, Self
from functools import cache
from web3 import Web3
from web3.eth.eth import Eth
from web3.contract.contract import Contract

from .enums import Chain, ERC20
from . import log


__all__ = [
    "Web3Connector",
    "ContractBook",
    "Addr",
]


class Web3Connector:
    """ A thin wrapper of Web3.
    """

    _web3: Web3
    _chain: Chain

    def init_web3(self,
                  *,
                  ipc_path: Optional[str]=None,
                  http_url: Optional[str]=None,
                  provider: Optional[str]=None,
                  chain: Optional[Chain]=None
                  ):
        self._web3 = self.connect_to_web3(ipc_path=ipc_path, http_url=http_url, provider=provider, chain=chain)
        self._chain = chain

    @staticmethod
    def connect_to_http_provider(*,
                                 provider: str,
                                 chain: Chain) -> Web3:

        if provider == "infura":
            url_base_map = {
                Chain.ETHEREUM: "https://mainnet.infura.io/v3",
                Chain.GOERLI: "https://goerli.infura.io/v3",
                Chain.SEPOLIA: "https://serpolia.infura.io/v3",
                Chain.AVALANCHE: "https://avalanche-mainnet.infura.io/v3",
                Chain.ARBITRUM: "https://arbitrum-mainnet.infura.io/v3",
                Chain.OPTIMISM: "https://optimism-mainnet.infura.io/v3",
                Chain.POLYGON: "https://polygon-mainnet.infura.io/v3",
            }
            url_base = url_base_map[chain]
            api_key = os.environ["INFURA_API_KEY"]
            url = f"{url_base}/{api_key}"
            log.info(f"connecting to: {url}")
            w3 = Web3(Web3.HTTPProvider(url))
            assert w3.is_connected()
            return w3
        else:
            NotImplementedError(f"not implemented provider: {provider}")
            
    @staticmethod
    def connect_to_web3(*,
                        ipc_path: Optional[str]=None,
                        http_url: Optional[str]=None,
                        provider: Optional[str]=None,
                        chain: Optional[Chain]=None
                        ) -> Web3:
        if ipc_path is not None:
            _web3 = Web3(Web3.IPCProvider(ipc_path))
        elif http_url is not None:
            _web3 = Web3(Web3.HTTProvider(http_url))
        elif provider is not None and chain is not None:
            _web3 = Web3Connector.connect_to_http_provider(provider=provider, chain=chain)
        else:
            raise ValueError("set ipc_path, http_url or (provider, chain)")
        assert _web3.is_connected(), "Web3 is not connected"
        return _web3

    @property
    def web3(self) -> Web3:
        return self._web3

    @property
    def chain(self) -> Chain:
        return self._chain

    @property
    def eth(self) -> Eth:
        return self.web3.eth

        
class ContractBook(Web3Connector):

    _contracts: Dict[str, Contract] = {}

    def contract(self, label_or_token: Union[str, ERC20]) -> Contract:
        """ Fetch contract by label or token.
        """
        if isinstance(label_or_token, ERC20):
            label = label_or_token.name
        else:
            assert isinstance(label_or_token, str)
            label = label_or_token
        if not hasattr(self, "_contracts") or label not in self._contracts:
            raise ValueError(f"{label} is not found.")
        return self._contracts[label]

    def init_contract(self,
                      *,
                      contract: Contract=None,
                      addr: str=None,
                      abi: Optional[list]=None,
                      impl_addr: Optional[str]=None,
                      label: str,
                      on_existing: str="skip",
                      ):
        """
        Directly return the contract is already created and found by `label` in self._contracts.
        Otherwise, create a Contract from addr and abi/impl_addr.
        
        Parameters
        ----------
        addr : str
            Contract address.
        abi : list
            Contract ABI.
        impl_addr : str | None
            Implementation address.
            Note: must set either `abi` or `impl_addr` if `addr` is a proxy, otherwise ABI is not right.
        label : str
            If set, the contract will be cached in self._contracts.
        """
        if label in self._contracts:
            msg = f"contract {label} is already initialized"
            if on_existing == "skip":
                log.info(msg)
                return
            elif on_existing == "raise":
                raise ValueError(msg)
            elif on_existing == "override":
                log.info(f"{msg}, will override")
            else:
                raise ValueError(on_existing)
        if contract is not None:
            self._contracts[label] = contract
        else:
            addr = self.web3.to_checksum_address(addr)
            if abi is None:
                if impl_addr is None:
                    impl_addr = addr
                log.info(f"addr: {addr}\nimpl addr: {impl_addr}")
                abi = self.get_abi(impl_addr)
            contract = self.web3.eth.contract(address=addr, abi=abi)
            self._contracts[label] = contract

    def init_erc20(self, token_or_token_name: Union[ERC20, str]):
        """ Add ERC20 to the contract book.
        """
        if isinstance(token_or_token_name, ERC20):
            token = token_or_token_name
        else:
            token = ERC20[token_or_token_name]
        self.init_contract(addr=token.addr, abi=token.abi, label=token.name, on_existing="skip")

    @cache
    def get_abi(addr: str) -> str:
        raise NotImplementedError()

    def get_balance_of(self, *, token: ERC20, addr: str) -> int:
        """ Get the balance of an ERC20 token of address.
        """
        self.init_erc20(token.name)
        balance = self.contract(token.name).functions.balanceOf(addr).call()
        decimals = self.get_decimals(token)
        log.info(f"address {addr} balance of {token} = {balance} / 10e{decimals} = {balance/(10**decimals)}")
        return balance

    @cache
    def get_decimals(self, token: ERC20) -> int:
        return self.contract(token).functions["decimals"]().call()


class Addr:

    _value: str # checksum address

    def __init__(self, value: Union[str, Self]) -> None:
        if isinstance(value, Addr):
            self._value = value.value
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

    def __eq__(self, __value: Union[str, Self]) -> bool:
        return self.value == Addr(__value).value

    def __hash__(self) -> int:
        return self.value.__hash__()

    def to_topic(self) -> str:
        """ Convert to event topic. TODO: better way than str.replace?
        """
        return self.value.replace("0x", "0x" + "0" * 24)
