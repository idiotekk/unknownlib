import os
import json
import requests
import pandas as pd
from pathlib import Path
from web3 import Web3
from .etherscan import Etherscan

# for type hints
from web3.contract import Contract
from web3.contract.contract import ContractFunction
from web3.datastructures import AttributeDict
from web3.types import TxReceipt
from web3.eth.eth import Eth
from eth_account import Account
from ens import ENS
from typing import Optional, Dict, List, Callable, Any, Union
from functools import cache

from .enums import Chain, ERC20
from .. import log
from ..io import dump_json


class FastW3:
    """ A class that combines web3, ens and account.
    """

    _web3: Web3
    _chain: Chain
    _scan: Etherscan
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
    
    def init_scan(self, chain: Chain):
        self._scan = Etherscan(chain)

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
            _web3 = self.connect_to_http_provider(provider=provider, chain=chain)
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

    def contract(self, label_or_token: Union[str, ERC20]) -> Contract:
        """ Fetch contract by label or token.
        """
        if isinstance(label_or_token, ERC20):
            label = label_or_token.name
        else:
            assert isinstance(label_or_token, str)
            label = label_or_token
        if label not in self._contracts:
            raise ValueError(f"{label} is not found; existing contracts: {list(self._contracts.keys())}")
        return self._contracts[label]

    def get_block_number(self,
                         *,
                         timestamp: Optional[pd.Timestamp]=None) -> int:
        """ Get the block number of a timestamp.
        If timestamp is not specified, get the latest block number.
        """
        if timestamp is not None:
            return self._scan.get_block_number_by_timestamp(int(timestamp.value / 1e9))
        else:
            return self._web3.eth.get_block_number()

    def get_block_time(self,
                       *,
                       block_number: int,
                       tz: str="US/Eastern") -> pd.Timestamp:
        return pd.to_datetime(
            self._web3.eth.get_block(block_number).timestamp * 1e9,
            utc=True).tz_convert(tz)

    def init_contract(self,
                      *,
                      addr: str,
                      abi: Optional[list]=None,
                      impl_addr: Optional[str]=None,
                      label: str,
                      override: bool=True,
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
        # check existing contracts
        if label in self._contracts:
            log.warning(f"contract label {label} is already used")
            if override:
                log.warning(f"will override {label}")
            if not override:
                log.warning(f"skipped")
                return

        addr = self._web3.to_checksum_address(addr)
        if abi is None:
            if impl_addr is None:
                impl_addr = addr
            log.info(f"addr: {addr}\nimpl addr: {impl_addr}")
            abi = self.get_abi(impl_addr)
        contract = self._web3.eth.contract(address=addr, abi=abi)
        self.add_contract(contract, label=label)

    def add_contract(self, c: Contract, *, label: str):
        self._contracts[label] = c
        log.info(f"contract cached as '{label}'")

    def init_erc20(self, token_or_token_name: Union[ERC20, str]):
        if isinstance(token_or_token_name, ERC20):
            token = token_or_token_name
        else:
            token = ERC20[token_or_token_name]
        self.init_contract(addr=token.addr, abi=token.abi, label=token.name, override=False)

    @cache
    def _decimals(self, token: ERC20) -> int:
        d = self.contract(token.name).functions.decimals().call()
        log.info(f"{token} decimals = {d}")
        return d

    def balance_of(self, *, token: ERC20) -> int:
        """ Get the balance of an ERC20 token.
        """
        self.init_erc20(token.name)
        balance = self.contract(token.name).functions.balanceOf(self.acct.address).call()
        decimals = self._decimals(token)
        log.info(f"balance of {token} = {balance} / 10e{decimals} = {balance/(10**decimals)}")
        return balance

    def call(self,
             func: ContractFunction,
             *,
             value: float=0, # value in *ETH*
             gas: float, # gas, unit = gwei
             hold: bool=False, # if True, only build tx, not send it
             **kw: dict, # other transaction args than from, nounce, value, gas
             ) -> AttributeDict:
        """ Execute a transaction.
        """
        tx = func.build_transaction({
            "from": self._acct.address,
            "nonce": self._web3.eth.get_transaction_count(self._acct.address),
            "value": self._web3.to_wei(value, "ether"), # not that this won't count as an API call
            "gas": int(gas),
            "gasPrice": self.eth.gas_price,
            **kw,
        })
        if hold is True:
            log.info(f"holding tx because hold is {hold}")
            return AttributeDict(tx)
        return self._sign_and_send(tx)
    
    def _sign_and_send(self, tx: Dict[str, Any]) -> TxReceipt:
        """ Sign and send a transaction and obtain receipt.
        """
        log.info(f"signing transaction {tx}")
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
                   ) -> TxReceipt:
        """ Send ether of `value` in `unit` to `to`.
        """

        log.info(f"sending {value} {unit} to {to}")
        nonce = self._web3.eth.get_transaction_count(self._acct.address)
        to = self._web3.to_checksum_address(to)
        tx = {
            "nonce": nonce,
            "to": to,
            "value": self._web3.to_wei(value, unit),
            "gas": int(gas),
            "gasPrice": self.eth.gas_price,
        }
        return self._sign_and_send(tx)

    def get_abi(self, addr: str) -> list:
        """ Get abi from contract address.
        """
        return self._scan.get(module="contract", action="getabi", address=addr)

    @staticmethod
    def connect_to_http_provider(provider: str, chain: Chain) -> Web3:

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

    def get_event_logs(self,
                       *,
                       contract: str,
                       event_name: str,
                       from_block: int,
                       to_block: int,
                       topics: List[str]=[],
                       ) -> List[AttributeDict]:
        """ Get event logs of a contract for block within range [from_block, to_block].

        Parameters
        ----------
        contract : str
            Label of the contract.
        topics : [str]
            *Extra* topics for the filter, in addition to the first topic which
            always identifies the event itself.
        """

        def get_event_topic(contract: Contract, event_name: str) -> str:
            func = contract.events[event_name]()
            topics = func._get_event_filter_params(func.abi)["topics"]
            assert len(topics) == 1, f"expect 1 topic; got {topics}"
            return topics[0]

        c = self.contract(contract)
        event_topic = get_event_topic(c, event_name)
        topics = [event_topic] + topics

        filter_params = {
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": c.address,
            "topics": topics,
        }
        log.info(f"filtering logs {filter_params} for event {event_name}. (number of blocks: {to_block - from_block})")
        raw_logs = self.eth.get_logs(filter_params)
        log.info(f"number of logs = {len(raw_logs)}")

        processed_log = [dict(c.events[event_name]().process_log(raw_log)) for raw_log in raw_logs]
        return processed_log