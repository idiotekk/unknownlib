import numpy as np
import pandas as pd
from typing import Tuple
from .. import log


def calc_ret(df: pd.DataFrame,
             *,
             time_var: str,
             price_var: str,
             bound: float=1000,
             ret_type="log") -> Tuple[pd.DataFrame, str]:
    """
    Calculate return from last tick to this tick.
    """
    ret_var = f"{price_var}_ret"
    log.info(f"calculating {ret_var}")
    assert df[time_var].is_monotonic_increasing
    assert bound > 0
    if ret_type == "log":
        df[ret_var] = np.clip(np.log(df[price_var] / df[price_var].shift()), -bound, bound)
    elif ret_type == "sign":
        df[ret_var] = np.sign(np.log(df[price_var] / df[price_var].shift()))
    else:
        raise NotImplementedError(ret_type)
    return df, ret_var


def calc_fwd_ret(df: pd.DataFrame,
             time_var: str,
             price_var: str,
             bound: float=1000,
             horizon: int=1,
             ret_type:str="log") -> Tuple[pd.DataFrame, str]:
    """
    Calculate return from last tick to this tick.
    """
    fwd_ret_var = f"{price_var}_fwd_ret_{horizon}"
    log.info(f"calculating {fwd_ret_var}")
    assert df[time_var].is_monotonic_increasing
    assert bound > 0
    if ret_type == "log":
        df[fwd_ret_var] = np.clip(np.log(df[price_var].shift(-horizon) / df[price_var]), -bound, bound)
    elif ret_type == "sign":
        df[fwd_ret_var] = np.sign(np.log(df[price_var].shift(-horizon) / df[price_var]))
    else:
        raise NotImplementedError(ret_type)
    return df, fwd_ret_var


def calc_ema(df: pd.DataFrame,
             *,
             var: str,
             halflife: int,
            ) -> Tuple[pd.DataFrame, str]:
    ema_var = f"{var}_ema_{halflife}"
    log.info(f"calculating {ema_var}")
    df[ema_var] = df[var].ewm(halflife=halflife).mean()
    return df, ema_var