import os
import sys
import pandas as pd
from glob import glob
from pathlib import Path
from typing import Union, Sequence, Any
from . import log


__all__ = [
    "save_df",
    "collect_df",
    "load_json",
    "dump_json",
]


def make_sure_parent_dir_exists(path: Union[str, Path]) -> Union[str, Path]:
    """ Create parent dir if not exists.
    """
    parent_dir = Path(path).parent
    if not parent_dir.exists():
        log.info(f"creating {parent_dir}")
        parent_dir.mkdir(parents=True, exist_ok=True)
    return path


def save_df(df: pd.DataFrame,
            file: Union[str, Path],
            **kw) -> str:
    """ Write dataframe to csv, creating parent dir if not exists.
    """
    file = make_sure_parent_dir_exists(file)
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
        s_ = list(s[:head        query = """CREATE TABLE IF NOT EXISTS {} ({});""".format(table_name, "\n,".join([k + " " + v for k, v in dtype.items()]))
        self.execute(query)
        query = f"""CREATE UNIQUE INDEX IF NOT EXISTS __index ON {table_name}({','.join(index)})"""
        self.execute(query)
 ", {len(s)} in total"
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


def load_json(f_: Union[Path, str]) -> Any:
    import json
    log.info(f"reading {f_}")
    with open(str(f_), "r") as f:
        return json.load(f)


def dump_json(j: Union[list, dict], f_: Union[Path, str]):
    import json
    log.info(f"writing {f_}")
    f_ = make_sure_parent_dir_exists(f_)
    with open(str(f_), "w") as f:
        json.dump(j, f, indent=4)