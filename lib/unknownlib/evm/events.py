import pandas as pd


def get_event_logs_as_df(*,
    stime: pd.Timestamp,
    etime: pd.Timestamp):
    
    from_block = fw.scan.get_block_number_by_timestamp(to_int(stime, "s"))
    to_block = fw.scan.get_block_number_by_timestamp(to_int(etime, "s")) - 1
    filter_params = {
        "fromBlock": from_block,
        "toBlock": to_block,
        "address": pool_addr,
        "topics": [swap_topic0]
    }
    log.info(f"filtering logs {filter_params} . (number of blocks: {to_block - from_block})")
    raw_logs = fw.eth.get_logs(filter_params)
    log.info(f"number of logs: {len(raw_logs)}")
    processed_log = [flatten_dict(dict(raw_log_processor(raw_log))) for raw_log in raw_logs]
    df = pd.DataFrame(sum(processed_logs, []))
    return df