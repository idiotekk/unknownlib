"""
This example fetches logs of an event from a contract and write to sql database.
"""
import os
import requests
import argparse
import time
import json
import pandas as pd
from requests.adapters import HTTPAdapter
from hexbytes import HexBytes
from pprint import pprint
from unknownlib.evm.fastw3 import FastW3, Chain, log
from unknownlib.evm.mktdata import ChainLinkPriceFeed, Coin
from unknownlib.evm.core import ERC721ContractBook
from unknownlib.evm.timestamp import to_int
from unknownlib.evm.sql import SQLConnector
from unknownlib.dt import sleep
from typing import Tuple, List, Optional


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--token", help="coin name. e.g. BTC")
    parser.add_argument("--delete", action="store_true")
    parser.add_argument("--sdate", type=int)
    parser.add_argument("--edate", type=int)
    parser.add_argument("--date", type=int)
    parser.add_argument("--freq", type=int, default=10, help="frequency of samples; unit=blocks")
    
    args = parser.parse_args()

    chain = Chain.ETHEREUM
    w3 = FastW3()
    w3.init_web3(provider="infura", chain=chain)
    w3.init_scan(chain=chain)

    token_name = args.token
    token = Coin[token_name]
    if args.date is not None:
        sdate = edate = args.date
    else:
        sdate = args.sdate
        edate = args.edate
    freq = args.freq
    stime = pd.to_datetime(str(sdate), utc=True)
    etime = pd.to_datetime(str(edate), utc=True) + pd.Timedelta("24h")
    sblock = w3.get_block_number(timestamp=stime) // freq * freq
    eblock = w3.get_block_number(timestamp=etime)
    log.info(f"""
date range [{sdate}, {edate}];
time range [{stime}, {etime});
blocks [{sblock}, {eblock}]; freq = {freq} blocks""")

    sql = SQLConnector()
    db_path = os.path.expandvars('$HOME/data/mktdata.db')
    sql.connect(db_path)


    table_name=f"coin_mktdata_{token_name}"
    if args.delete:
        delete_staus = sql.delete_table(table_name=table_name)
        if delete_staus is False:
            exit(0)

    if sql.table_exists(table_name):
        block_number_count = sql.read(f"SELECT blockNumber FROM {table_name}")["blockNumber"].value_counts()
        assert (block_number_count <= 1).all(), f"duplicate tokenId found: {block_number_count[block_number_count > 1]}"
        existing_block_numbers = list(block_number_count.index)
    else:
        existing_block_numbers = []
    
    for block_number in range(sblock, eblock + 1, freq):
        if block_number in existing_block_numbers:
            log.info(f"block number {block_number} is found in the database; skipping ")
            continue
        price_data = {
            "blockNumber": block_number,
            "price": w3.get_price(token, block_number=block_number),
            "timestamp": w3.get_block_time(block_number=block_number, tz="UTC"),
        }
        log.info(price_data)
        row = pd.DataFrame(price_data, index=["blockNumber"])
        sql.write(row, table_name=table_name, index=["blockNumber"])