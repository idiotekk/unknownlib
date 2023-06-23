import sqlite3
from . import log
import pandas as pd
from typing import Union, List


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
        
    def read(self, query: str) -> pd.DataFrame:
        return pd.read_sql_query(query, self.con)

    def delete_table(self, table_name: str):
        should_delete = input(f"delete table {table_name}? (Y/N)")
        if should_delete == "Y":
            self.con.execute(f"DROP TABLE {table_name}")
    
    def table_exists(self, table_name: str) -> bool:
        c = self.con.execute(f'''SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}' ''')
        return c.fetchone() is not None