import pandas as pd


def enrich_tfer_data(*,
    df: pd.DataFrame,
    token_ca: str,
    pool_ca: str):

    value_col = "args_value"
    null_addr = "0x0000000000000000000000000000000000000000"
    max_supply = df[value_col].iloc[0]

    balance_of = {null_addr: max_supply, token_ca: 0, pool_ca: 0}
    new_holders = set([])

    from tqdm import tqdm
    for i, row in tqdm(df.iterrows()):

        from_ = row["args_from"]
        to_ = row["args_to"]
        value_ = row[value_col]
        
        if to_ not in balance_of:
            balance_of[to_] = value_
        else:
            balance_of[to_] += value_
            
        balance_of[from_] -= value_
        if from_ not in [null_addr, token_ca, pool_ca]:
            assert balance_of[from_] >= 0, str((from_, balance_of[from_]))
            if balance_of[from_] <= 0:
                balance_of.pop(from_)
        else:
            if balance_of[from_] < 0:
                log.warning(f"balance of {from_} is negative {balance_of[from_]}")
        
        df.loc[i, "isNewHolder"] = to_ in new_holders
        new_holders = new_holders | set([to_])
        df.loc[i, "newHolderCount"] = len(new_holders)
        df.loc[i, "holderCount"] = len(balance_of)