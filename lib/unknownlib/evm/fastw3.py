import json
import requests
import web3
import pandas as pd

from eth_account import Account
from ens import ENS
from typing import Optional

from .enums import *
from .. import log


class FastW3:
    """ A class that combines web3, ens and account.
    """

    _web3: web3.Web3
    _ens: ENS
    _acct: Account
    
    def __init__(self) -> None:
        pass

    def init_web3(self,
                  *,
                  ipc_path: Optional[str]=None,
                  http_url: Optional[str]=None):
        self._web3 = self._connect_to_web3(ipc_path=ipc_path, http_url=http_url)
    
    def _connect_to_web3(self,
                  *,
                  ipc_path: Optional[str]=None,
                  http_url: Optional[str]=None):
        from web3 import Web3
        if ipc_path is not None:
            self._web3 = Web3(Web3.IPCProvider(ipc_path))
        elif http_url is not None:
            self._web3 = Web3(Web3.HTTProvider(http_url))
        else:
            raise ValueError("")
        assert self._we3.is_connected(), "Web3 is not connected"

    def init_acct(self,
                  *,
                  priv_key: str):
        self._acct = Account.from_key(priv_key)
    
    
    def init_ens(self,
                 *,
                 ipc_path: Optional[str]=None,
                 http_url: Optional[str]=None,
                 ):
        if ipc_path is not None or http_url is not None:
            _web3 = self._connect_to_web3(ipc_path=ipc_path, http_url=http_url)
        else:
            _web3 = self._web3
        self._ens = ENS.from_web3(_web3)

    
    @property
    def web3(self):
        return self._web3
    
    @property
    def acct(self):
        return self._acct

    @property
    def ens(self):
        return self._ens


    def get_block_number(self,
                         *,
                         timestamp: Optional[pd.Timestamp]=None):
        """ Get the block number of a timestamp.
        If timestamp is not specified, get the latest block number.
        """
        if timestamp is not None:
            seconds_since_epoch = (timestamp.value / 1e9)
        else:
            return self._web3.eth.get_block_number()

    def get_block_time(self,
                       *,
                       block_number: int,
                       tz="US/Eastern"):
        return pd.to_datetime(
            self._web3.eth.get_block(block_number).timestamp * 1e9,
            utc=True).tz_convert(tz)


def get_abi_of(addr: str,
               *,
               from_cache :bool=True,
               chain: Chain=Chain.ETHEREUM) -> list:
    """
    Get abi from contract address.
    addr : str
    from_cache ： bool
        if True, check cache file first TODO: use 3rd party caching library
    """
    # Exports contract ABI in JSON
    abi_endpoint_map = {
        Chain.ETHEREUM: 'https://api.etherscan.io/api?module=contract&action=getabi&address=',
        Chain.ARBITRUM: 'https://api.arbiscan.io/api?module=contract&action=getabi&address=',
    }
    abi_endpoint = abi_endpoint_map[chain]
    cache_file = f"/tmp/{addr}.abi.json"
    if from_cache:
        try:
            with open(cache_file) as f:
                abi_json = json.load(f)
                print(f"read from {cache_file}")
                return abi_json
        except Exception:
            print(f"failed to read from {cache_file}")

    def _get_json_from_url(url: str) -> object:
        """ GET response from a url as json.
        """
        log.info(f"requesting from {url}")
        response = requests.get(url)
        response_json = response.json()
        return response_json

    abi_url = f"{abi_endpoint}{addr}"
    abi_json = json.loads(_get_json_from_url(abi_url)["result"])

    with open(cache_file, "w") as f:
        json.dump(abi_json, f)
        print(f"cached to: {cache_file}")
    return abi_json