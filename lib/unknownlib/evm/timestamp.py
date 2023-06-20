import pandas as pd


def utcnow() -> pd.Timestamp:
    return pd.Timestamp.utcnow()


def to_utc(t: pd.Timestamp) -> pd.Timestamp:
    if t.tzinfo is not None:
        return t.tz_convert("UTC")
    else:
        raise ValueError("can't convert tz-naive timetstamp to UTC!")


def to_int(t: pd.Timestamp, unit="ns") -> int:
    """ Convert timestamp to integer.
    `t` is required to be tz-aware.
    """
    ns = int(to_utc(t).value)
    if unit == "ns":
        return ns
    elif unit == "s":
        return ns // int(1e9)
    else:
        raise ValueError(f"unsupported unit {unit}")