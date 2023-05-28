import pandas as pd
from typing import Optional, Union, List, Callable


def agg_df(df,
           *,
           by: Union[str, List[str]],
           func:Callable = None,
           ):
           
    return df.groupby(by).apply(lambda x: pd.Series(func(x))).reset_index()