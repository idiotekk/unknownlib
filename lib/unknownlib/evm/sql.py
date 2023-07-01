import sqlite3
from . import log
import pandas as pd
import numpy as np
from typing import Union, List, Optional
from pandas.api.types import is_string_dtype


class SQLConnector:
    
    _con: sqlite3.Connection
   
    def connect(self, path: str, **kw):
        self._path = path
        self._con = sqlite3.connect(path, **kw)

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
        
        query = """CREATE TABLE IF NOT EXISTS {} ({});""".format(table_name, "\n,".join([k + " " + v for k, v in dtype.items()]))
        self.con.execute(query)
        query = f"""CREATE UNIQUE INDEX IF NOT EXISTS __index ON {table_name}({','.join(index)})"""
        self.con.execute(query)
        log.info(f"created table {table_name} at {self._path}; index = {index}")

        query = "REPLACE INTO {} ({}) VALUES ({}) ".format(table_name, ', '.join(df.columns), ', '.join(["?"]*len(df.columns)))
        for i in range(len(df)):
            self.con.execute(query, tuple(df.iloc[i]))
        self.con.commit()
        log.info(f"written {len(df)} rows.")
        
    def read(self, query: str, parse_str_columns=True) -> pd.DataFrame:
        df = pd.read_sql_query(query, self.con)
        self.parse_str_columns(df, inplace=True)
        return df

    def delete_table(self, table_name: str):
        should_delete = input(f"delete table {table_name}? (Y/N)")
        if should_delete == "Y":
            self.con.execute(f"DROP TABLE {table_name}")
    
    def table_exists(self, table_name: str) -> bool:
        c = self.con.execute(f'''SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}' ''')
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