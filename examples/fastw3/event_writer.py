"""
This example fetches trade prices from uniswap v3 USDC pool,
then plot the prices in an interactive chart.
"""
import os
import pandas as pd
from hexbytes import HexBytes
from unknownlib.evm.fastw3 import FastW3, Chain, log
from unknownlib.evm.timestamp import to_int
from unknownlib.evm.sql import SQLConnector
from typing import Tuple, List

fw = FastW3()


def fetch_range(*,
                contract_name: str,
                event_names: List[str],
                time_range: Tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    
    start_time, end_time = time_range
    if end_time <= start_time:
        raise ValueError(f"end time {end_time} <= start time {start_time}")
    from_block = fw.scan.get_block_number_by_timestamp(to_int(start_time, "s"))
    to_block = fw.scan.get_block_number_by_timestamp(to_int(end_time, "s")) - 1
    log.info(f"({start_time}, {end_time}) -> blocks({from_block}, {to_block}), {to_block-from_block+1} blocks in total")

    raw_logs = []
    for event_name in event_names:
        raw_logs = fw.get_event_logs(
            contract=contract_name,
            event_name=event_name,
            from_block=from_block,
            to_block=to_block)

    def _flatten_log(log_: dict) -> dict:
        """ Make log a single-layer dictionary by expanding "args". """
        return {
            **{f"args_{k}": v for k, v in log_["args"].items()},
            **{k: v.hex() if isinstance(v, HexBytes) else v for k, v in log_.items() if k != "args"}
        }

    logs = [_flatten_log(_) for _ in raw_logs]
    df = pd.DataFrame(logs)
    stime = fw.get_block_time(block_number=from_block)
    etime = fw.get_block_time(block_number=to_block)
    df["timestamp"] = (etime - stime) / (to_block - from_block) * (df["blockNumber"] - from_block) + stime
    return df


def fetch_one_date(*,
                   contract_name: str,
                   event_names: List[str],
                   date: int,
                   ) -> pd.DataFrame:

    start_time = pd.to_datetime(str(date)).tz_localize("US/Eastern")
    time_delta = pd.Timedelta("24h")
    end_time = start_time + time_delta
    return fetch_range(
        contract_name=contract_name,
        event_names=event_names,
        time_range=(start_time, end_time))


if __name__ == "__main__":

    chain = Chain.ETHEREUM
    contract_name = "milady"
    contract_addr = "0x12970E6868f88f6557B76120662c1B3E50A646bf"
    event_name = "Transfer"
    db_path = '/tmp/evm.db'
    sdate = 20230601
    edate = 20230615

    fw.init_web3(provider="infura", chain=Chain.ETHEREUM)
    fw.init_scan(chain=Chain.ETHEREUM)
    fw.init_contract(addr=contract_addr, label=contract_name)
    table_name = f"{contract_name}_{event_name}"
    sql = SQLConnector()
    sql.connect(db_path)

    for date in pd.date_range(str(sdate), str(edate), freq="1d"):
        date = int(date.strftime("%Y%m%d"))
        print(date)
        df = fetch_one_date(date=date, event_names=[event_name], contract_name=contract_name)
        sql.write(df, table_name=table_name, index=["blockNumber", "logIndex"])