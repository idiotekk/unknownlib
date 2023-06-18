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

fw = FastW3()


def get_start_end_block_numbers(date, tz="US/Eastern"):
    start_time = pd.to_datetime(str(date)).tz_localize(tz)
    time_delta = pd.Timedelta("24h")
    end_time = start_time + time_delta
    s = fw.scan.get_block_number_by_timestamp(to_int(start_time, "s"))
    e = fw.scan.get_block_number_by_timestamp(to_int(end_time, "s")) - 1
    log.info(f"({start_time}, {end_time}) -> blocks({s}, {e}), {e-s+1} blocks in total")
    return s, e 


def fetch_one_date(date):
    
    from_block, to_block = get_start_end_block_numbers(date)
    raw_logs = fw.get_event_logs(
        contract=contract_name,
        event_name=event_name,
        from_block=from_block,
        to_block=to_block)

    def _flatten_log(log_: dict) -> dict:
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
        df = fetch_one_date(date)
        sql.write(df, table_name=table_name, index=["blockNumber", "logIndex"])