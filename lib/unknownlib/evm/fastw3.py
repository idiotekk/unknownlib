import pandas as pd
from .etherscan import Etherscanner

# for type hints
from web3.contract import Contract
from web3.contract.contract import ContractFunction
from web3.datastructures import AttributeDict
from web3.types import TxReceipt
from eth_account import Account
from ens import ENS
from typing import Optional, Dict, List, Any, Callable

from .core import Chain, ERC20, ERC20ContractBook
from .mktdata import ChainLinkPriceFeed
from .timestamp import utcnow, to_int
from .. import log


__all__ = [
    "FastW3",
]


class FastW3(Etherscanner, ERC20ContractBook, ChainLinkPriceFeed):
    """ A class that combines web3, ens and account.
    """

    _ens: ENS
    _acct: Account
    
    def init_acct(self,
                  *,
                  private_key: str):
        self._acct = Account.from_key(private_key)
        log.info(f"initialized account address: {self._acct.address}")
    
    def init_ens(self, **kw):
        if kw:
            _web3 = self.connect_to_web3(**kw)
        else:
            _web3 = self.web3
        assert _web3.eth.chain_id == 1, f"ens is only supported on {Chain(1)}, got {Chain(_web3.eth.chain_id)}"
        self._ens = ENS.from_web3(_web3)
    
    @property
    def acct(self) -> Account:
        return self._acct

    @property
    def ens(self) -> ENS:
        return self._ens

    def get_block_number(self,
                         *,
                         timestamp: Optional[pd.Timestamp]=None) -> int:
        """ Get the block number of a timestamp.
        If timestamp is not specified, get the latest block number.
        """
        if timestamp is None:
            timestamp = utcnow()
        n = self.scan.get_block_number_by_timestamp(to_int(timestamp, unit="s"))
        log.debug(f"block number as of {timestamp} = {n}")
        return n

    def get_block_time(self,
                       *,
                       block_number: int,
                       tz: str="UTC") -> pd.Timestamp:
        dt = pd.to_datetime(
            self.web3.eth.get_block(block_number).timestamp * 1e9,
            utc=True).tz_convert(tz)
        log.debug(f"block number {block_number} timestamp = {dt}")
        return dt

    def call(self,
             func: ContractFunction,
             *,
             value: float=0, # value in *ETH*
             gas: float, # gas, unit = gwei
             hold: bool=False, # if True, only build tx, not send it
             max_retries: int=5,
             **kw: dict, # other transaction args than from, nounce, value, gas
             ) -> AttributeDict:
        """ Execute a transaction.
        """
        tx_args = {
            "from": self.acct.address,
            "nonce": self.web3.eth.get_transaction_count(self.acct.address),
            "value": self.web3.to_wei(value, "ether"), # not that this won't count as an API call
            "gas": int(gas),
            "gasPrice": self.eth.gas_price,
            **kw,
        }
        tx = func.build_transaction(tx_args)
        if hold is True: # build but don't send
            log.info(f"holding tx because hold is {hold}")
            return AttributeDict(tx)
        else:
            return self._sign_and_send(tx, max_retries=max_retries)
    
    def _sign_and_send(self,
                       tx: Dict[str, Any],
                       *,
                       max_retries: int=5,
                       timout: int=60, # num of seconds to wait for receipt
                       ) -> TxReceipt:
        """ Sign and send a transaction and obtain receipt.
        """
        retries = 0
        while True:
            try:
                log.info(f"signing transaction {tx}")
                signed_tx = self.acct.sign_transaction(tx)
                log.info(f"sending transaction...")
                tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
                log.info(f"wating for transaction receipt for {tx_hash.hex()}, timout = {timout}s")
                tx_receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timout)
                return tx_receipt
            except Exception as e:
                err_msg = str(e)
                log.info(f"failed with error: {e}")
                if retries >= max_retries:
                    raise Exception(f"exhausted max retries {max_retries}")
                else:
                    retries += 1
                    if "nonce too low" in err_msg:
                        tx["nonce"] += 1
                        log.info(f"retry No.{retries} with nonce {tx['nonce']}")
                    elif ("max fee per gas less than block base fee" in err_msg or
                        "already known" in err_msg or
                        "is not in the chain after" in err_msg):
                        tx["gasPrice"] = int(tx["gasPrice"] * 1.2)
                        log.info(f"retry No.{retries} with gasPrice {tx['gasPrice']}")
                    else:
                        raise Exception(f"unable to handle error; exiting")
        
    def send_ether(self, *,
                   to: str, # target address
                   value: float,
                   unit: str="ether",
                   gas: float,
                   max_retries: int=3,
                   ) -> TxReceipt:
        """ Send ether of `value` in `unit` to `to`.
        """

        log.info(f"sending {value} {unit} to {to}")
        nonce = self.web3.eth.get_transaction_count(self.acct.address)
        to = self.web3.to_checksum_address(to)
        tx = {
            "nonce": nonce,
            "to": to,
            "value": self.web3.to_wei(value, unit),
            "gas": int(gas),
            "gasPrice": self.eth.gas_price,
        }
        return self._sign_and_send(tx, max_retries=max_retries)
    
    def get_logs_as_df(self,
        *,
        stime: pd.Timestamp,
        etime: pd.Timestamp,
        batch_size: Optional[pd.Timedelta]=None,
        contract_name: str, # contract key
        event_name: str,
        **kw,
        ) -> pd.DataFrame:
        """
        Args:
            batch_size: if None, get all logs in one shot; other wise batch by this size
            contract_name: name of contract. must be already cached
            event_name: name of event.
        """
        c_ = self.contract(contract_name)
        address = c_.address
        func = c_.events[event_name]()
        topics = func._get_event_filter_params(func.abi)["topics"]
        log_processor = func.process_log

        def get_logs_as_df_single(stime: pd.Timestamp, etime: pd.Timestamp) -> pd.DataFrame:
            from .utils import flatten_dict
            from_block = self.scan.get_block_number_by_timestamp(to_int(stime, "s"))
            to_block = self.scan.get_block_number_by_timestamp(to_int(etime, "s")) - 1
            filter_params = {
                **{
                    "fromBlock": from_block,
                    "toBlock": to_block,
                    "address": address,
                    "topics": topics
                },
                **kw,
            }
            log.info(f"filtering logs {filter_params} . (number of blocks: {to_block - from_block})")
            raw_logs = self.eth.get_logs(filter_params)
            log.info(f"number of logs: {len(raw_logs)}")
            processed_logs = [flatten_dict(dict(log_processor(raw_log))) for raw_log in raw_logs]
            df = pd.DataFrame(processed_logs)
            return df
        
        if batch_size is None:
            return get_logs_as_df_single(stime, etime)
        else:
            from ..algo import batch_run
            dfs = batch_run(
                func=get_logs_as_df_single,
                start=stime,
                end=etime,
                batch_size=batch_size)
            df = pd.concat(dfs).reset_index(drop=True)
            return df