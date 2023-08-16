import pandas as pd
from .. import log


def enrich_tfer_data(*,
    df: pd.DataFrame,
    token_ca: str,
    pool_ca: str,
    trading_start_block: int
    ):

    value_col = "args_value"
    null_addr = "0x0000000000000000000000000000000000000000"
    max_supply = df[value_col].iloc[0]
    log.info(f"token ca: {token_ca}, pool ca: {pool_ca}")

    balance_of = {null_addr: max_supply, token_ca: 0, pool_ca: 0}
    new_holders = set([])
    
    ignore_list = [null_addr, token_ca, pool_ca]

    early_trades = df[df["blockNumber"] < trading_start_block + 6]
    early_holders = [_ for _ in early_trades["args_to"].unique()[:30] if _ not in ignore_list]
    early_holders_GMV = 0
    early_holders_count = 0

    from tqdm import tqdm
    for i, row in tqdm(df.iterrows()):

        from_ = row["args_from"]
        to_ = row["args_to"]
        value_ = row[value_col]
        
        if to_ not in balance_of:
            balance_of[to_] = value_
            if to_ in early_holders:
                early_holders_count += 1
        else:
            balance_of[to_] += value_
        if to_ in early_holders:
            early_holders_GMV += value_
            
        balance_of[from_] -= value_
        if from_ in early_holders:
            early_holders_GMV -= value_

        if from_ not in ignore_list:
            assert balance_of[from_] >= 0, str((from_, balance_of[from_]))
            if balance_of[from_] <= 0:
                balance_of.pop(from_)
                if from_ in early_holders:
                    early_holders_count -= 1
        else:
            if balance_of[from_] < 0:
                log.warning(f"balance of {from_} is negative {balance_of[from_]}")
        
        df.loc[i, "isNewHolder"] = to_ in new_holders
        new_holders = new_holders | set([to_])
        df.loc[i, "newHolderCount"] = len(new_holders)
        df.loc[i, "holderCount"] = len(balance_of)
        df.loc[i, "earlyHoldersGMV"] = early_holders_GMV
        df.loc[i, "earlyHoldersCount"] = early_holders_count