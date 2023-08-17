import os
import json
import pandas as pd
import numpy as np
from web3 import Web3
from pprint import pprint
from unknownlib.evm.sql import SQLConnector
from unknownlib.evm import flatten_dict, Chain, Addr, interpolate_timestamp, log, ContractBook, Etherscanner
from unknownlib.dt import sleep


class EventListenor(Etherscanner, ContractBook):
    pass


w3 = EventListenor()


if __name__ == "__main__":

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("--delete-table", action="store_true")
    args = parser.parse_args()

    chain = Chain.ETHEREUM
    w3.init_web3(provider="infura", chain=chain)
    w3.init_scan(chain=chain)
    db_path = os.path.expandvars('$HOME/data/evm.db')
    sql = SQLConnector()
    sql.connect(db_path)

    contract_name = "WETH"
    w3.init_contract(addr="0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", key=contract_name)
    event_name = "Approval"
    table_name = f"EventListener_{contract_name}_{event_name}"
    if args.delete_table:
        sql.delete_table(table_name)

    def log_loop(event_filter, retry_wait="5s"):
        while True:
            events = event_filter.get_new_entries()
            if events:
                rows = [flatten_dict(json.loads(Web3.to_json(e))) for e in events]
                for r in rows:
                    pprint(r)
                df = pd.DataFrame(rows)
                interpolate_timestamp(df)
                sql.write(df, table_name=table_name, index=["blockNumber", "logIndex"])
            sleep(retry_wait)

    contract = w3.contract("WETH")
    event_filter = contract.events[event_name].create_filter(fromBlock="latest")
    log_loop(event_filter)