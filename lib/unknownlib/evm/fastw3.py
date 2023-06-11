import os
import json
import requests
import pandas as pd
from pathlib import Path
from web3 import Web3

# for type hints
from web3.contract import Contract
from web3.contract.contract import ContractFunction
from web3.types import TxReceipt
from web3.eth.eth import Eth
from eth_account import Account
from ens import ENS
from typing import Optional, Dict, List, Callable, Any

from .enums import *
from .. import log


class FastW3:
    """ A class that combines web3, ens and account.
    """

    _web3: Web3
    _chain: Chain
    _ens: ENS
    _acct: Account
    _contracts: Dict[str, Contract] = {}
    
    def __init__(self) -> None:
        pass

    def init_web3(self,
                  *,
                  ipc_path: Optional[str]=None,
                  http_url: Optional[str]=None,
                  provider: Optional[str]=None,
                  chain: Optional[Chain]=None
                  ):
        self._web3 = self._connect_to_web3(
            ipc_path=ipc_path, http_url=http_url, provider=provider, chain=chain)
        self._chain = chain
    
    def _connect_to_web3(self,
                  *,
                  ipc_path: Optional[str]=None,
                  http_url: Optional[str]=None,
                  provider: Optional[str]=None,
                  chain: Optional[Chain]=None
                  ) -> Web3:
        from web3 import Web3
        if ipc_path is not None:
            _web3 = Web3(Web3.IPCProvider(ipc_path))
        elif http_url is not None:
            _web3 = Web3(Web3.HTTProvider(http_url))
        elif provider is not None and chain is not None:
            _web3 = self.connect_to_web3_provider(provider=provider, chain=chain)
        else:
            raise ValueError("set ipc_path, http_url or (provider, chain)")
        assert _web3.is_connected(), "Web3 is not connected"
        return _web3

    def init_acct(self,
                  *,
                  private_key: str):
        self._acct = Account.from_key(private_key)
        log.info(f"initialized account address: {self._acct.address}")
    
    def init_ens(self, **kw):
        if kw:
            _web3 = self._connect_to_web3(**kw)
        else:
            _web3 = self._web3
        self._ens = ENS.from_web3(_web3)
    
    @property
    def web3(self) -> Web3:
        return self._web3
    
    @property
    def acct(self) -> Account:
        return self._acct

    @property
    def ens(self) -> ENS:
        return self._ens
    
    @property
    def eth(self) -> Eth:
        return self._web3.eth

    @property
    def chain(self) -> Chain:
        return self._chain

    def contract(self, label: str) -> Contract:
        """ Fetch contract by label.
        """
        return self._contracts[label]

    def get_block_number(self,
                         *,
                         chain: Chain,
                         timestamp: Optional[pd.Timestamp]=None) -> int:
        """ Get the block number of a timestamp.
        If timestamp is not specified, get the latest block number.
        """
        if timestamp is not None:
            s = (timestamp.value / 1e9) # seconds since epoch
            chain_name = chain.name
            url = f"https://coins.llama.fi/block/{chain_name}/{s}"
            height = self.get_json_from_url(url)["height"]
            dt = pd.to_datetime(s * 1e9, utc=True)
            log.info(f"{chain} height = {height} as of {dt}")
            return height
        else:
            return self._web3.eth.get_block_number()

    def get_block_time(self,
                       *,
                       block_number: int,
                       tz: str="US/Eastern") -> pd.Timestamp:
        return pd.to_datetime(
            self._web3.eth.get_block(block_number).timestamp * 1e9,
            utc=True).tz_convert(tz)

    def get_contract(self,
                     addr: str,
                     impl_addr: Optional[str]=None,
                     label: str=None,
                     ) -> Contract:
        """
        Create a Contract from addr.
        
        Parameters
        ----------
        impl_addr : str | None
            Must set if `addr` is a proxy, otherwise ABI is not right.
        """
        if addr in self._contracts:
            log.info(f"fetching contract from cache")
            return self._contracts[addr]
        addr = self._web3.to_checksum_address(addr)
        if impl_addr is None:
            impl_addr = addr
        log.info(f"addr: {addr}\nimpl addr: {impl_addr}")
        abi = self.get_abi(impl_addr, from_cache=True, chain=self._chain)
        contract = self._web3.eth.contract(address=addr, abi=abi)
        self._contracts[addr] = contract
        if label is not None:
            log.info(f"contract cached as '{label}'")
            self._contracts[label] = contract
        return contract
        
    def call(self,
             func: ContractFunction,
             *,
             value: float=0, # value in *ETH*
             gas: float, # gas, unit = gwei
             gas_price: float, # gas price in *gwei*
             **kw: dict, # other transaction args than from, nounce, value, gas, gasPrice
             ) -> TxReceipt:
        """ Execute a transaction.
        """
        nonce = self._web3.eth.get_transaction_count(self._acct.address)
        tx = func.build_transaction({
            "from": self._acct.address,
            "nonce": nonce,
            "value": self._web3.to_wei(value, "ether"),
            "gas": int(gas),
            "gasPrice": self._web3.to_wei(gas_price, "gwei"),
            **kw,
        })
        return self._sign_and_send(tx)
    
    def _sign_and_send(self, tx: Dict[str, Any]) -> TxReceipt:
        """ Sign, send and transaction and obtain receipt.
        """
        log.info(f"signing transaction...")
        signed_tx = self._acct.sign_transaction(tx)
        log.info(f"sending transaction...")
        tx_hash = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        log.info(f"wating for transaction receipt...")
        tx_receipt = self._web3.eth.wait_for_transaction_receipt(tx_hash)
        return tx_receipt
        
    def send_ether(self, *,
                   to: str, # target address
                   value: float,
                   unit: str="ether",
                   gas: float,
                   gas_price: float,
                   ) -> TxReceipt:

        nonce = self._web3.eth.get_transaction_count(self._acct.address)
        to = self._web3.to_checksum_address(to)
        tx = {
            "nonce": nonce,
            "to": to,
            "value": self._web3.to_wei(value, unit),
            "gas": int(gas),
            "gasPrice": self._web3.to_wei(gas_price, "gwei"),
        }
        return self._sign_and_send(tx)


    @staticmethod
    def get_abi(contract_addr: str,
                *,
                from_cache :bool=True,
                chain: Chain=Chain.ETHEREUM) -> list:
        """
        Get abi from contract address.
        contract_addr : str
        from_cache ： bool
            if True, check cache file first.
            TODO: use 3rd party caching library
        """
        # Exports contract ABI in JSON
        abi_endpoint_map = {
            Chain.ETHEREUM: 'https://api.etherscan.io/api?module=contract&action=getabi&address=',
            Chain.ARBITRUM: 'https://api.arbiscan.io/api?module=contract&action=getabi&address=',
        }
        abi_endpoint = abi_endpoint_map[chain]
        cache_file = f"/tmp/abi/{chain}.{contract_addr}.json"
        if from_cache:
            try:
                with open(cache_file) as f:
                    abi_json = json.load(f)
                    print(f"read from {cache_file}")
                    return abi_json
            except Exception:
                print(f"failed to read from {cache_file}")

        abi_url = f"{abi_endpoint}{contract_addr}"
        abi_json = json.loads(FastW3.get_json_from_url(abi_url)["result"])

        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(abi_json, f)
            print(f"cached to: {cache_file}")
        return abi_json

    @staticmethod
    def connect_to_web3_provider(provider: str, chain: Chain) -> Web3:

        if provider == "infura":
            url_base = {
                Chain.ETHEREUM: "https://mainnet.infura.io/v3",
                Chain.GOERLI: "https://goerli.infura.io/v3",
                Chain.SEPOLIA: "https://serpolia.infura.io/v3",
                Chain.AVALANCHE: "https://avalanche-mainnet.infura.io/v3",
                Chain.ARBITRUM: "https://arbitrum-mainnet.infura.io/v3",
                Chain.OPTIMISM: "https://optimism-mainnet.infura.io/v3",
                Chain.POLYGON: "https://polygon-mainnet.infura.io/v3",
            }[chain]
            api_key = os.environ["INFURA_API_KEY"]
            url = f"{url_base}/{api_key}"
            log.info(f"connecting to: {url}")
            w3 = Web3(Web3.HTTPProvider(url))
            assert w3.is_connected()
            log.info(f"is connected to: {url}")
            return w3
        else:
            NotImplementedError(f"not implemented provider: {provider}")

    @staticmethod
    def get_json_from_url(url: str) -> object:
        """ GET response from a url as json.
        """
        log.info(f"requesting from {url}")
        response = requests.get(url)
        response_json = response.json()
        return response_json