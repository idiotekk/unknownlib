from ..logging import log
import re
from typing import Optional, Dict, Any, Self, Union


__all__ = [
    "Element",
    "ElementCatalog",
    "ElementManager",
]


class Element:
    """ The basic class and building block of the scheme.
    """
    
    _name: str = None
    _manager = None
    _params: dict = None

    def __init__(self, name: str, params: Dict[str, Any]):
        self._name = name
        self._params = params
        log.info(f"""
        name: {name}
        type: {self.__class__},
        params: {params}""")

    def set_manager(self, manager):
        self._manager = manager
    
    def set_params(self, params: Dict[str, Any]):
        self._params = params

    def get_element_by_name(self, name: str) -> Self:
        """ A portal to refer to other elements. """
        return self._manager.get_element_by_name(name)

    def get_element_by_type(self, type_: type) -> Self:
        """ A portal to refer to other elements. """
        return self._manager.get_element_by_type(type_)

    def init(self):
        """ Initialize the element. Typically an element parses its parameters,
        initialize its member variables, etc.
        """
        raise NotImplementedError(f"`init` is not implemented for {self.__class__}")

    def calc(self, time: int):
        """ This function is called at every calc round scheduled by a scheduler.
        """
        raise NotImplementedError(f"`calc` is not implemented for {self.__class__}")
    
    def done(self):
        """ This funcitons is called at the end, doing wrapping-up jobs,
        e.g. writing in-memory data to files.
        """
        log.info(f"{self._name} done.")

    def field(self, s) -> Union[str, float, int, bool]:
        """ Get value of field `s`.
        """
        raise NotImplementedError(s)

    @classmethod
    def type_name(cls) -> str:
        """ A string that represent the class.
        By default, the name is the class name snake-casified.
        E.g., class "SimpleScheduler" -> type_name "simple_scheduler".
        """
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()


class ElementCatalog:
    """ A class that maintains a mapping from type names to types, e.g.,
    "scheduler" -> Scheduler
    "optimizer" -> Optimizer
    """

    _catalog: Dict[str, type] = {}

    @classmethod
    def register_element_type(cls, type_: type):
        type_name = type_.type_name()
        assert type_name not in cls._catalog, "type {type_name} is already registered!"
        log.info(f"registered: name = {type_name}, type = {type_}")
        cls._catalog[type_name] = type_

    @classmethod
    def register_all_element_types(cls):
        """ Recursively find and register all subclasses of Element.
        This should be called before building a scheme.
        """
        cls._catalog = {} # reset
        def search_subclasses(cls):
            return cls.__subclasses__() + sum(
                [search_subclasses(_) for _ in cls.__subclasses__()], [])
        all_element_types = search_subclasses(Element)
        for type_ in all_element_types:
            cls.register_element_type(type_)

    @classmethod
    def get_element_type(cls, type_name: str) -> type:
        """ Find the type (aka subclass of Element) given a type name.
        """
        assert type_name in cls._catalog, f"{type_name} is not found in {list(cls._catalog.keys())}"
        return cls._catalog[type_name]
    

class ElementManager:
    """ A central entiry that creates, initializes and triggers element.
    """
    
    _elements: Dict[str, type]

    def __init__(self) -> None:
        self._elements = {}
    
    def create_element(self, name: str, params: Dict[str, Any]):
        """ Create an element with given name and parameters.
        """
        assert name not in self._elements, f"{name} is already created!"
        type_name = params["type"]
        type_ = ElementCatalog.get_element_type(type_name)
        e = type_(name, params)
        e.set_manager(self)
        self._elements[name] = e

    def get_element_by_name(self, name: str) -> Element:
        """ Get the unique element that has the given name.
        """
        return self._elements[name]

    def get_element_by_type(self, type_: type) -> Element:
        """ Get the unique element that match the given type.
        """
        es = [e for _, e in self.iter_elements() if isinstance(e, type_)]
        assert len(es) == 1, f"found {len(es)} elements of type {type_}; expected 1."
        return es[0]

    def iter_elements(self):
        """ Iterate through all elements.
        """
        for n, e in self._elements.items():
            yield n, e
    
    def init_elements(self):
        """ Initialize all elements sequentially.
        """
        for _, e in self.iter_elements():
            e.init()
    
    def calc_elements(self, time: int):
        """ Calc all elements sequentially.
        """
        for _, e in self.iter_elements():
            e.calc(time)
    
    def done_elements(self):
        """ Finish up all elements sequentially.
        """
        for _, e in self.iter_elements():
            e.done()


class ElementParams:

    _params: Dict[str, Any] = {}

    def __init__(self, params: Dict[str, Any]) -> None:
        self._params = params