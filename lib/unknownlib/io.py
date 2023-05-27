import os
import sys
import pandas as pd
from glob import glob
from multiprocess import Pool
from . import log


def read_df(file):
    
    pass


def _repr_seq(s, head=1, tail=1):
    if len(s) <= head + tail:
        r = str(s)
    else:
        s_ = list(s[:head]) + ["..."] + list(s[(-tail):])
        r = str(s_)
    r += f", {len(s)} in total"
    return r


def collect_df(p: str, cores=1, filepath=False, **kw) -> pd.DataFrame:
    """ Read and combine all files that match pattern `p`.
    """
    if isinstance(p, str):
        p = [p]
    else:
        pass
    p = [os.path.expandvars(_) for _ in p]
    files = sum([glob(_, recursive=True) for _ in p], [])
    files = [_ for _ in files if os.path.isfile(_)]
    if len(files) == 0:
        raise FileNotFoundError(f"no files found that match {p}")
    log.info(f"files found: {_repr_seq(files)}")

    def _reader(f):
        return pd.read_csv(f, **kw)

    if cores > 1:
        pool = Pool(cores)
        df_list = pool.map(_reader, files)
        pool.close()
    else:
        df_list = [_reader(f) for f in files]

    if filepath:
        [df.assign(filepath=f) for df, f in zip(df_list, files)]
    df = pd.concat(df_list)
    return df