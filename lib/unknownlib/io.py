import os
import sys
import pandas as pd
from glob import glob
from pathlib import Path
from typing import Union, Sequence
from . import log


def save_df(df: pd.DataFrame,
            file: Union[str, Path],
            **kw) -> str:
    """ Write dataframe to csv, creating parent dir if not exists.
    """
    file = Path(os.path.expandvars(str(file)))
    parent_dir = file.parent
    if not parent_dir.exists():
        log.info(f"creating {parent_dir}")
        parent_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(file, **kw)
    log.info(f"df shape: {df.shape}, written to: {file}")
    return file


def _repr_seq(s: Sequence, head: int=1, tail: int=1) -> str:
    """ A short repr of a sequence.
    """
    _repr = lambda s: "[" + ", ".join([str(_) for _ in s]) + "]"
    if len(s) <= head + tail:
        r = _repr(s)
    else:
        s_ = list(s[:head]) + ["..."] + list(s[(-tail):])
        r = _repr(s_) + f", {len(s)} in total"
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
        df_ = pd.read_csv(f, **kw)
        if filepath is True:
            df_["filepath"] = f
        log.info(f"{f} shape={df_.shape}")
        return df_

    if cores > 1:
        from multiprocess import Pool
        pool = Pool(cores)
        df_list = pool.map(_reader, files)
        pool.close()
    else:
        df_list = [_reader(f) for f in files]

    df = pd.concat(df_list)
    return df