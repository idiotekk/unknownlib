from . import log
from typing import Optional


__all__ = [
    "Element",
    "ElementCatalog",
    "ElementManager",
]


class Element:
    
    _name: str = None
    _manager = None
    _params: dict = None

    def __init__(self, name: str, params: dict) -> None:
        self._name = name
        self._params = params

    def set_manager(self, manager):
        self._manager = manager
    
    def set_params(self, params):
        self._params = params

    def get_element_by_name(self, name: str):
        return self._manager.get_element_by_name(name)

    def get_element_by_type(self, type_: type):
        return self._manager.get_element_by_type(type_)

    def init(self):
        raise NotImplementedError(f"`init` is not implemented for {self.__class__}")

    def calc(self, time: int):
        raise NotImplementedError(f"`calc` is not implemented for {self.__class__}")
    
    def done(self):
        log.info(f"{self._name} done.")

    def field(self, s):
        raise NotImplementedError(s)


class ElementCatalog:

    _catalog: dict = {}

    @classmethod
    def register_element_type(cls, type_name: str, type_: type):
        assert type_name not in cls._catalog, "type {type_name} is already registered!"
        log.info(f"registered: name = {type_name}, type = {type_}")
        cls._catalog[type_name] = type_

    @classmethod
    def get_element_type(cls, type_name: str):
        assert type_name in cls._catalog, f"{type_name} is not found in {list(cls._catalog.keys())}"
        return cls._catalog[type_name]
    

class ElementManager:
    
    _elements: dict = {}
    
    def create_element(self, name, params: dict):
        assert name not in self._elements, f"{name} is already created!"
        type_name = params["type"]
        type_ = ElementCatalog.get_element_type(type_name)
        e = type_(name, params)
        e.set_manager(self)
        self._elements[name] = e

    def get_element_by_name(self, name: str) -> Element:
        return self._elements[name]

    def get_element_by_type(self, type_: type) -> Element:
        es = [e for n, e in self.iter_elements() if isinstance(e, type_)]
        assert len(es) == 1, f"found {len(es)} elements of type {type_}; expected 1."
        return es[0]

    def iter_elements(self):
        for n, e in self._elements.items():
            yield n, e
    
    def init_elements(self):
        for _, e in self.iter_elements():
            e.init()
    
    def calc_elements(self, time: int):
        for _, e in self.iter_elements():
            e.calc(time)
    
    def done_elements(self):
        for _, e in self.iter_elements():
            e.done()