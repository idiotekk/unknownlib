"""
Base classes of evm lib.
This module doesn't deal with any specific contract or address, e.g.
TODO: need better name than "base.py".
"""
import os

from typing import Optional, Dict, Any
from functools import cache
from web3 import Web3
from web3.eth.eth import Eth
from web3.contract.contract import Contract

from .enums import Chain, ERC20, ActionIfItemExists
from .. import log


__all__ = [
    "Web3Connector",
    "ContractBook",
    "ERC20ContractBook",
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
            base_url_map = {
                Chain.ETHEREUM: "https://mainnet.infura.io/v3",
                Chain.GOERLI: "https://goerli.infura.io/v3",
                Chain.SEPOLIA: "https://serpolia.infura.io/v3",
                Chain.AVALANCHE: "https://avalanche-mainnet.infura.io/v3",
                Chain.ARBITRUM: "https://arbitrum-mainnet.infura.io/v3",
                Chain.OPTIMISM: "https://optimism-mainnet.infura.io/v3",
                Chain.POLYGON: "https://polygon-mainnet.infura.io/v3",
            }
            base_url = base_url_map[chain]
            api_key = os.environ["INFURA_API_KEY"]
            url = f"{base_url}/{api_key}"
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
    _supported_key_types: tuple = (ERC20, str)

    def contract(self, key: Any) -> Contract:
        """ Fetch contract by label or token.
        """
        assert isinstance(key, self._supported_key_types), f"only supporting {self._supported_key_types}, got {type(key)}"
        if key not in self._contracts:
            raise ValueError(f"{key} is not found.")
        return self._contracts[key]

    def init_contract(self,
                      *,
                      contract: Contract=None,
                      addr: str=None,
                      abi: Optional[list]=None,
                      impl_addr: Optional[str]=None,
                      key: Any,
                      if_exists: str="skip",
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
        """
        if key in self._contracts:
            action_if_exists = ActionIfItemExists.from_str(if_exists)
            msg = f"contract {key} is already initialized"
            if action_if_exists == ActionIfItemExists.SKIP:
                log.info(msg)
                return
            elif action_if_exists == ActionIfItemExists.RAISE:
                raise ValueError(msg)
            elif action_if_exists == ActionIfItemExists.OVERRIDE:
                log.info(f"{msg}, will override")
            else:
                raise ValueError(action_if_exists)
        if contract is not None:
            self._contracts[key] = contract
        else:
            addr = self.web3.to_checksum_address(addr)
            if abi is None:
                if impl_addr is None:
                    impl_addr = addr
                log.info(f"addr: {addr}\nimpl addr: {impl_addr}")
                abi = self.get_abi(impl_addr)
            contract = self.web3.eth.contract(address=addr, abi=abi)
            self._contracts[key] = contract

    @cache
    def get_abi(addr: str) -> str:
        raise NotImplementedError()


class ERC20ContractBook(ContractBook):

    def init_erc20(self, token: ERC20):
        """ Add ERC20 to the contract book.
        """
        self.init_contract(addr=token.addr, abi=token.abi, key=token, if_exists="skip")

    def get_balance_of(self, *, token: ERC20, addr: str) -> int:
        """ Get the balance of an ERC20 token of address.
        """
        self.init_erc20(token)
        balance = self.contract(token).functions.balanceOf(addr).call()
        decimals = self.get_decimals(token)
        log.info(f"address {addr} balance of {token} = {balance} / 10e{decimals} = {balance/(10**decimals)}")
        return balance

    @cache
    def get_decimals(self, token: ERC20) -> int:
        return self.contract(token).functions["decimals"]().call()