import pandas as pd
from typing import Optional, Union, List, Callable, Dict, Sequence

__all__ = [
    "agg_df",
    "cross_join",
]


def agg_df(df: pd.DataFrame,
           *,
           by: Union[str, List[str]],
           func: Callable,
           ) -> pd.DataFrame:
           
    return df.groupby(by).apply(lambda x: pd.Series(func(x))).reset_index()

    
def cross_join(**kw: Dict[str, Sequence]) -> pd.DataFrame:
    """ Equivalent to "CJ" in R data.table.
    """
    from functools import reduce
    df_list = []
    for key, value in kw.items():
        df_tmp = pd.DataFrame({key: list(value), "__key": 0})
        df_list.append(df_tmp)
    res = reduce(lambda x, y: pd.merge(x, y, on="__key"), df_list)
    return res.drop("__key", axis=1)
   
    
@pd.api.extensions.register_dataframe_accessor("uk")
class UnknownDataFrame:

    def __init__(self, pandas_obj):
        self._validate(pandas_obj)
        self._obj = pandas_obj
    
    @staticmethod
    def _validate(obj):
        assert isinstance(obj, pd.DataFrame)

    def agg(self, *, by: Union[str, List[str]], func: Callable):
        """
        Group by `by` and apply `func`.

        Examples
        --------
        >>> df.uk.agg(by="date", func=lambda x: {"n": len(x)})
        """
        return agg_df(self._obj, by=by, func=func)

    def save(self, *a, **kw):
        from .io import save_df
        save_df(self._obj, *a, **kw)