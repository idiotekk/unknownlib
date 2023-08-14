import time, os
import asyncio
from pprint import pprint
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

    def get_univswap_v2_pair(self, addr):
        self.init_contract(addr="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f", key="UniswapV2Factory")
        c = self.contract("UniswapV2Factory")
        pool_ca = c.functions["getPair"](
            Addr("0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2").value, 
            Addr(addr).value
        ).call()
        return pool_ca

fw = ERC20TokenTracker()


def get_logs(sdate, edate, ticker):

    def _date_to_utc(date):
        return pd.to_datetime(str(date)).tz_localize("US/Eastern").tz_convert("UTC")

    stime = _date_to_utc(sdate)
    etime = min(_date_to_utc(edate), pd.Timestamp.utcnow())
    batch_freq = "1d"

    df_tfer = fw.get_logs_as_df(
        stime=stime,
        etime=etime,
        contract_name=f"{ticker}_token",
        event_name="Transfer",
        batch_size=pd.Timedelta(batch_freq),
    )
    df_tfer = interpolate_timestamp(df_tfer, fw)

    df_swap = fw.get_logs_as_df(
        stime=stime,
        etime=etime,
        contract_name=f"{ticker}_pool",
        event_name="Swap",
        batch_size=pd.Timedelta(batch_freq),
    )

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
    df = df_swap[["transactionHash", "price", "side"]].copy()
    df_swap_1 = df.copy()

    # enrich transfers
    value_col = "args_value" if "args_value" in df_tfer.columns else "args_amount"
    df_tfer["args_value"] = df_tfer[value_col]
    df = df_tfer[["args_from", "args_to", value_col, "timestamp", "transactionHash"]].copy()
    enrich_tfer_data(df=df, token_ca=token_ca, pool_ca=pool_ca)
    df_tfer_1 = df.copy()

    return df_tfer_1, df_swap_1


if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("ticker", type=str)
    parser.add_argument("token_ca", type=str)
    parser.add_argument("--sdate", type=int, required=True)
    parser.add_argument("--delete-table", action="store_true")
    args = parser.parse_args()

    sdate = args.sdate
    edate = 20230815
    chain = Chain.ETHEREUM
    fw.init_web3(provider="infura", chain=chain)
    fw.init_scan(chain=chain)
    db_path = os.path.expandvars('$HOME/data/evm.db')
    sql = SQLConnector()
    sql.connect(db_path)

    ticker = args.ticker
    token_ca = args.token_ca

    table_name=f"ERC20_{ticker}"
    if args.delete_table:
        sql.delete_table(table_name+"_Transfer")
        sql.delete_table(table_name+"_Swap")

    token_ca = Addr(token_ca).value
    pool_ca = fw.get_univswap_v2_pair(token_ca)
    fw.init_contract(addr=pool_ca, key=f"{ticker}_pool")
    fw.init_contract(addr=token_ca, key=f"{ticker}_token")

    df_tfer, df_swap = get_logs(sdate, edate, ticker)
    sql.write(df_tfer, table_name=table_name+"_Transfer", index=["blockNumber", "logIndex"])
    sql.write(df_swap, table_name=table_name+"_Swap", index=["blockNumber", "logIndex"])