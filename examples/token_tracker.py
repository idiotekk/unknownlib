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
from unknownlib.evm import flatten_dict, Chain, Addr, interpolate_timestamp
from hexbytes import HexBytes
from eth_account import Account
from unknownlib.algo import batch_run

fw = FastW3()


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
    df_swap["side"] = np.where(df_swap["args_amount1In"] > 0, 1, -1)
    df_swap.head()

    # enrich transfers
    value_col = "args_value" if "args_value" in df_tfer.columns else "args_amount"
    df_tfer["args_value"] = df_tfer[value_col]
    df = df_tfer[["args_from", "args_to", value_col, "timestamp", "transactionHash"]].copy()
        
    df_tfer_1 = df.copy()

    # enrich swaps
    df = df_swap[["transactionHash", "price", "side"]].copy()
    df_swap_1 = df.copy()

    df = pd.merge(
        df_tfer_1,
        df_swap_1,
        on=["transactionHash"],
        how="outer") # keep transfer order
    #df["price"] = 1/df["price"]

    return df


if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("ticker", type=str)
    parser.add_argument("token_ca", type=str)
    parser.add_argument("pool_ca", type=str)
    parser.add_argument("--delete-table", action="store_true")
    args = parser.parse_args(
		#"NFT 0xe89efe25f387a45a2e5486df1e555ceb44888938 0x41ef64562155687ed6824e8349fcb59d6769e96f".split(" ")
		#"Anime 0xfe643c262d04cf8ee8f605963175363880ae6de6 0x0821e3cb9d5c653622b6c7b9dceddf3581880d34".split(" ")
	)

    sdate = 20230812
    edate = 20230813
    chain = Chain.ETHEREUM
    fw.init_web3(provider="infura", chain=chain)
    fw.init_scan(chain=chain)
    db_path = os.path.expandvars('$HOME/data/evm.db')
    sql = SQLConnector()
    sql.connect(db_path)

    ticker = args.ticker
    token_addr = args.token_ca
    pool_addr = args.pool_ca

    table_name=f"ERC20_trades_{ticker}"
    if args.delete_table:
        sql.delete_table(f"ERC20_trades_{ticker}")
    token_addr = Addr(token_addr).value
    pool_addr = Addr(pool_addr).value
    fw.init_contract(addr=pool_addr, key=f"{ticker}_pool")
    fw.init_contract(addr=token_addr, key=f"{ticker}_token")

    df = get_logs(sdate, edate, ticker)
    sql.write(df, table_name=table_name, index=["blockNumber", "logIndex"])
