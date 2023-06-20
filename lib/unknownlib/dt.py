"""
Date and time.
"""


import time
import pandas as pd
from . import log


def sleep(t_: str):
    """
    Parameters
    ----------
    t_ : str
        Parsable by pd.Timedelta.
    """
    s = pd.Timedelta(t_).total_seconds()
    log.info(f"sleeping for {t_} = {s} seconds")
    time.sleep(s)
    

def utcnow() -> pd.Timestamp:
    return pd.Timestamp.utcnow()