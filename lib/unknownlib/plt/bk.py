import pandas as pd
from typing import Union, List, Optional, Tuple
from bokeh.io import output_notebook
from bokeh.resources import INLINE
from bokeh.plotting import figure, gridplot
from bokeh.plotting import show as _show
from pandas.api.types import is_string_dtype

output_notebook(INLINE)


def _colors(n: int) -> List[str]:
    default_colors = ["black", "red", "green", "blue", "cyan", "magenta"]
    assert n <= len(default_colors)
    return default_colors[:n]


def plot(df: pd.DataFrame,
         *,
         x: str,
         y: Union[str, List[str]],
         hue: Optional[str]=None,
         hlines: List[float]=[],
         vlines: List[float]=[],
         line_types: str="line",
         figsize: Tuple[float]=(800, 500),
         title: Optional[str]=None,
         show: bool=True,
         tools: str="pan,reset,wheel_zoom,box_zoom,save",
         ):

    if isinstance(y, list):
        assert hue is None
        df = pd.melt(df,
                     id_vars=x,
                     value_vars=y,
                     var_name=" variable",
                     value_name=" value",
                     )
        y = " value"
        hue = " variable"
    else:
        df = df.copy()
    
    if hue is None:
        df["dummy"] = y
        hue = "dummy"

    if not is_string_dtype(df[hue]):
        df[hue] = df[hue].astype(str)

    unique_hues = df[hue].unique()
    palette = _colors(len(unique_hues))

    w, h = figsize
    if title is None:
        title = y
    p = figure(title=title,
               tools=tools,
               width=w,
               height=h)
    p.toolbar.active_scroll = None

    line_types = line_types.split(",")
    for color, hue_ in zip(palette, unique_hues):

        legend_label = hue_
        df_hue = df[df[hue] == hue_].copy()
        for line_type in line_types:
            line_func = getattr(p, line_type)
            line_func(df_hue[x], df_hue[y], color=color, legend_label=legend_label)
    
    for hl in hlines:
        p.line(df_hue[x], hl, color="black", line_dash="dashed")

    for vl in vlines:
        p.line(df_hue[vl], hl, color="black", line_dash="dashed")

    if show is True:
        _show(p)

    return p

    
def tsplot(df,
           *,
           time_var,
           y: Union[str, List[str]],
           hue: Optional[str]=None,
           show: bool=True,
           **kw,
           ):

    p = plot(df,
             x=time_var,
             y=y,
             hue=hue,
             show=False,
             **kw)

    from bokeh.models import DatetimeTickFormatter
    p.xaxis.formatter = DatetimeTickFormatter(
        years="%Y", months="%Y%m", days="%Y%m%d",
        hours="%Y%m%d %Hh", minutes="%Y%m%d-%H:%M")
    if show is True:
        _show(p)
    return p