import time, os
import asyncio
from pprint import pprint
import typing
import json
from web3 import Web3
from ens import ENS
import pandas as pd
import numpy as np
from unknownlib.plt.bk import tsplot
from unknownlib.evm.fastw3 import FastW3
from unknownlib.evm.sql import SQLConnector
from unknownlib.evm.timestamp import to_int
from unknownlib.evm import flatten_dict, Chain, Addr, interpolate_timestamp, log
from hexbytes import HexBytes
from eth_account import Account
from unknownlib.algo import batch_run
from unknownlib.apps.tokentracker import enrich_tfer_data


class ERC20TokenTracker(FastW3):

    def get_univswap_v2_pair(self, addr) -> str:
        self.init_contract(addr="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f", key="UniswapV2Factory")
        c = self.contract("UniswapV2Factory")
        pool_ca = c.functions["getPair"](
            Addr("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2").value, 
            Addr(addr).value
        ).call()
        return pool_ca

    def get_token_creation_time(self, contract_name: str) -> pd.Timestamp:
        creation_log = fw.get_logs_as_df(
            stime=pd.to_datetime("20180101").tz_localize("UTC"),
            etime=pd.Timestamp.utcnow(),
            contract_name=contract_name,
            event_name="OwnershipTransferred",
            topics=["0x8be0079c531659141344cd1fd0a4f28419497f9722a3daafe3b4186f6b6457e0", "0x0000000000000000000000000000000000000000000000000000000000000000"]
        ).iloc[0].to_dict()
        creation_block_number = int(creation_log["blockNumber"])
        creation_time = fw.get_block_time(block_number=creation_block_number)
        log.info(f"{contract_name} was created at {creation_block_number}, {creation_time}")
        return creation_time

fw = ERC20TokenTracker()


def get_logs(*,
    sdate: typing.Optional[int]=None,
    edate: typing.Optional[int]=None,
    stime: typing.Optional[pd.Timestamp]=None,
    etime: typing.Optional[pd.Timestamp]=None,
    ticker):

    def _date_to_utc(date):
        return pd.to_datetime(str(date)).tz_localize("UTC")

    if sdate:
        assert stime is None
        stime = _date_to_utc(sdate)
    if edate:
        assert etime is None
        etime = min(_date_to_utc(edate), pd.Timestamp.utcnow())
    batch_freq = "1d"

    df_swap = fw.get_logs_as_df(
        stime=stime,
        etime=etime,
        contract_name=f"{ticker}_pool",
        event_name="Swap",
        batch_size=pd.Timedelta(batch_freq),
    )

    df_tfer = fw.get_logs_as_df(
        stime=stime,
        etime=etime,
        contract_name=f"{ticker}_token",
        event_name="Transfer",
        batch_size=pd.Timedelta(batch_freq),
    )
    df_tfer = interpolate_timestamp(df_tfer, fw)

    def safe_div(x, y):
        return np.where(
            y != 0,
            x / np.where(y != 0, y, 1),
            np.nan)
    df_swap["price"] = np.where(
        df_swap["args_amount1In"] > 0,
        safe_div(df_swap["args_amount1In"], df_swap["args_amount0Out"]),
        safe_div(df_swap["args_amount1Out"], df_swap["args_amount0In"])
    )
    df_swap["volume1"] = df_swap["args_amount1In"] + df_swap["args_amount1Out"]
    df_swap["volume0"] = df_swap["args_amount0In"] + df_swap["args_amount0Out"]
    df_swap["side"] = np.where(df_swap["args_amount1In"] > 0, 1, -1)
    # enrich swaps
    df = df_swap[["transactionHash", "price", "side", "blockNumber", "logIndex"]].copy()
    df_swap_1 = df.copy()

    # enrich transfers
    value_col = "args_value" if "args_value" in df_tfer.columns else "args_amount"
    df_tfer["args_value"] = df_tfer[value_col]
    df = df_tfer[["args_from", "args_to", value_col, "timestamp", "transactionHash", "blockNumber", "logIndex"]].copy()
    df_tfer_1 = df.copy()

    return df_tfer_1, df_swap_1


if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("ticker", type=str)
    parser.add_argument("token_ca", type=str)
    parser.add_argument("--delete-table", action="store_true")
    args = parser.parse_args()

    chain = Chain.ETHEREUM
    fw.init_web3(provider="infura", chain=chain)
    fw.init_scan(chain=chain)
    db_path = os.path.expandvars('$HOME/data/evm.db')
    sql = SQLConnector()
    sql.connect(db_path)

    ticker = args.ticker
    token_ca = args.token_ca

    token_ca = Addr(token_ca).value
    pool_ca = fw.get_univswap_v2_pair(token_ca)
    fw.init_contract(addr=pool_ca, key=f"{ticker}_pool")
    fw.init_contract(addr=token_ca, key=f"{ticker}_token")

    table_name=f"ERC20_{ticker}"
    if args.delete_table:
        sql.delete_table(table_name+"_Transfer")
        sql.delete_table(table_name+"_Swap")

    if sql.table_exists(table_name+"_Transfer") and sql.table_exists(table_name+"_Swap"):
        df_tfer_hist = sql.read_table(table_name+"_Transfer")
        df_swap_hist = sql.read_table(table_name+"_Swap")
        last_block = min(
            int(df_tfer_hist["blockNumber"].max()),
            int(df_swap_hist["blockNumber"].max()))
        stime = fw.get_block_time(block_number=last_block)
        log.info(f"last observed block time = {stime}")
    else:
        df_tfer_hist = None
        df_swap_hist = None
        stime = fw.get_token_creation_time(f"{ticker}_token")


    etime = pd.Timestamp.utcnow()
    df_tfer, df_swap = get_logs(stime=stime, etime=etime, ticker=ticker)

    if df_tfer_hist is not None:
        df_tfer = pd.concat([df_tfer_hist, df_tfer])
    if df_swap_hist is not None:
        df_swap = pd.concat([df_swap_hist, df_swap])

    trading_start_block = int(df_swap["blockNumber"].min())
    enrich_tfer_data(df=df_tfer, token_ca=token_ca, pool_ca=pool_ca, trading_start_block=trading_start_block)
    sql.write(df_tfer, table_name=table_name+"_Transfer", index=["blockNumber", "logIndex"])
    sql.write(df_swap, table_name=table_name+"_Swap", index=["blockNumber", "logIndex"])