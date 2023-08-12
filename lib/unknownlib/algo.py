import pandas as pd
import typing
from . import log


def batch_run(*,
              func: typing.Callable[[pd.Timestamp], pd.Timestamp],
              start: pd.Timestamp,
              end: pd.Timestamp,
              batch_size: pd.Timedelta,
              min_batch_size: typing.Optional[pd.Timedelta]=None,
              ) -> typing.List[typing.Any]:
    """
    Sequetially run:
        func(start, start + batch_size),
        func(start + batch_size, start + 2 * batch_size),
        ...
        func(start + n*batch_size, start + end),
    and return the results as a list.
    * if any of the batches failed, then shrink batch size by 2, until
    the batch goes through or reach min batch size.
    """
    assert start <= end, f"failed: {start} < {end}"
    batch_start = start
    res = []
    batch_id = 0
    if min_batch_size is not None:
        min_delta = min_batch_size
    else:
        min_delta = batch_size / 4

    while batch_start < end:
        delta = batch_size
        while delta >= min_delta:
            try:
                batch_end  = min(batch_start + delta, end)
                log.info(f"running batch {batch_id} ({batch_start}, {batch_end})")
                res_batch = func(batch_start, batch_end)
                res.append(res_batch)
                batch_start = batch_end
                batch_id += 1
                break
            except Exception as e:
                log.info(f"{e}")
                delta /= 2
                log.info(f"reducing batch size to: {delta}")
        if delta < min_delta:
            raise Exception(f"failed to run with min batch size {min_delta}")
    return res