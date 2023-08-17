import os
import sqlite3
import json
from . import log
import pandas as pd
import numpy as np
from typing import Union, List, Optional, Any
from functools import wraps
from pandas.api.types import is_string_dtype


__all__ = [
    "SQLConnector",
    "SQLCache"
]


class SQLConnector:
    
    _con: sqlite3.Connection
   
    def connect(self, path: str, **kw):
        self._path = path
        try:
            self._con = sqlite3.connect(path, **kw)
        except Exception as e:
            log.error(f"failed to open {path}, error: {e}")

    @property
    def con(self) -> sqlite3.Connection:
        return self._con
    
    def write(self,
              df: pd.DataFrame,
              *,
              table_name: str,
              index: Union[str, List[str]]):

        def get_sql_dtype(log_: dict) -> dict:
            return {k: "TEXT" for k, _ in log_.items()}
        dtype = get_sql_dtype(df.iloc[0].to_dict())
        df = df.astype(str)

        if isinstance(index, str):
            index = [index]
        assert all([_ in df.columns for _ in index]), f"not all of {index} are found in {df.columns}"
        
        if not self.table_exists(table_name):
            query = """CREATE TABLE IF NOT EXISTS {} ({}, PRIMARY KEY ({}));""".format(
                table_name,
                ",".join([k + " " + v for k, v in dtype.items()]),
                ",".join(index))
            self.execute(query, verbose=True)
            log.info(f"created table {table_name} at {self._path}; index = {index}")

        query = "REPLACE INTO {} ({}) VALUES ({}) ".format(table_name, ', '.join(df.columns), ', '.join(["?"]*len(df.columns)))
        for i in range(len(df)):
            self.execute(query, tuple(df.iloc[i]))
        self.con.commit()
        log.info(f"{len(df)} rows are written to {self._path}:{table_name}.")
        
    def read(self, query: str, parse_str_columns=True) -> pd.DataFrame:
        log.info(f"querying dataframe from {query}")
        df = pd.read_sql_query(query, self.con)
        if parse_str_columns is True:
            self.parse_str_columns(df, inplace=True)
        return df
    
    def read_table(self, table_name: str, parse_str_columns=True) -> pd.DataFrame:
        query = f"SELECT * from {table_name}"
        return self.read(query, parse_str_columns=parse_str_columns)

    def delete_table(self, table_name: str) -> bool:
        """ Return True if deleted is done.
        """
        input_table_name = input(f"type table name to delete {table_name}:")
        if input_table_name == table_name or input_table_name == table_name[-3:]:
            self.execute(f"DROP TABLE {table_name}")
            return True
        else:
            log.info(f"input table name {input_table_name} doesn't match with {table_name}; aborted")
            return False

    def execute(self, query: str, *a, verbose=False, **kw):
        try:
            if verbose:
                log.info(f"executing query = {query}, args = {a}")
            return self.con.execute(query, *a, **kw)
        except Exception as e:
            log.error(f"{query} failed with error {e}")
            raise e
    
    def table_exists(self, table_name: str) -> bool:
        c = self.execute(f'''SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}' ''')
        return c.fetchone() is not None

    @staticmethod
    def parse_str_columns(df: pd.DataFrame, inplace: bool=True) -> Optional[pd.DataFrame]:
        """ Auto-parse string columns.

        Parameters
        ----------
        df : pd.DataFrame
        inplcace : bool
            If True, modify `df` in-place, return None. Otherwise,
            modify a copy of `df` and return the modified copy.
        """
        if inplace is not True:
            df = df.copy()
        for v in df.columns:
            if is_string_dtype(df[v]):
                if np.all(df[v].isin(["True", "False"])):
                    log.info(f"parsing boolean column {v}")
                    df[v] = np.where(df[v] == "True", True, False)
                elif np.all(df[v].str.isdigit()):
                    if np.all(df[v].str.len() <= 18):
                        log.info(f"parsing integer column {v}")
                        df[v] = df[v].astype(int)
                    else:
                        log.info(f"parsing float column {v}")
                        df[v] = df[v].astype(float)
                else:
                    pass
        if inplace is not True:
            return df


class SQLCache:

    _sql: SQLConnector = SQLConnector()
    _db_path: str=os.path.expandvars("$UNKNOWN_SQL_CACHE_DIR/_SQLCache.db")
    
    @classmethod
    def __get_table_name(cls, table_identifier):
        return f"{cls.__name__}_{table_identifier}"
    
    @classmethod
    def reset(cls, table_identifier):
        cls._sql.delete_table(cls.__get_table_name(table_identifier))

    @classmethod
    def cache(cls, func):
        """ Note: func must be a pure function.
        """
        @wraps(func)
        def new_func(**kw: dict) -> Any:
            table_identifier = f"{func.__module__}_{func.__name__}"
            table_name = cls.__get_table_name(table_identifier)
            cls._sql.connect(cls._db_path)
            if not cls._sql.table_exists(table_name):
                pass
            else:
                table = cls._sql.read(f"SELECT * from {table_name} WHERE " +
                    " AND ".join([f"{k} = {v}" for k, v in kw.items()])
                    , parse_str_columns=False)
                if len(table) > 2:
                    raise ValueError(f"found multiple records {table}")
                elif len(table) == 1:
                    __value = json.loads(table["__value"].iloc[0])
                    return __value
                else:
                    pass
            __value = func(**kw)
            row = pd.DataFrame({**kw, "__value": json.dumps(__value)}, index=list(kw.keys()))
            cls._sql.write(row, table_name=table_name, index=sorted(list[kw.keys()]))
            cls._sql.con.close()
            return __value
        return new_func


def sql_cache(func):
    return SQLCache.cache(func)