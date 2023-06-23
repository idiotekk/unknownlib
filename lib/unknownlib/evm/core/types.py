from typing import Union, Tuple, Any


def check_type(var: Any, type_or_types: Union[type, Tuple]):

    if not isinstance(var, type_or_types):
        raise TypeError(f"{var} has type {type(var)}, expected {type_or_types}")