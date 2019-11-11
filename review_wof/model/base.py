"""model/base.py - Base classes for data model
"""
from abc import ABCMeta, abstractmethod
from argparse import Namespace
from collections.abc import Mapping


class DataSource(metaclass=ABCMeta):
    """A base class for data sources that know hoe to fetch raw data and feed
    it to one or more data views used by the application to access it

    Data views are classes that:
    * Are decorated with the 'view' method of this class or derivatives
    * Have a constructor that can accept the DataSource instane and no other
      arguments
    * Have zero or more of the following instance methods:
        * 'on_new_data': Called when new data is made available by the DSC
        * 'on_data_loaded': Called when the DSC is done loading its data

    DSC classes expose the view classes that are linked to them via the `views`
    class property. Similarly DSC instances expose their view instances via
    the `views` property.
    """
    @classmethod
    def view(cls, name):
        if hasattr(cls, 'views'):
            views = cls.views
        else:
            views = Namespace()
            cls.views = views
        def decorator(dcls):
            setattr(views, name, dcls)
            return dcls
        return decorator

    def __init__(self):
        self.views = Namespace(**{
            vname: vcls(self) for vname, vcls
            in vars(getattr(self.__class__, 'views', Namespace())).items()
        })

    def _data_to_views(self, data):
        self._call_views('on_new_data', self, data)

    def _eod_to_views(self):
        self._call_views('on_data_loaded', self)

    def _call_views(self, method, *args):
        for view in vars(self.views).values():
            getattr(view, method, lambda *x: None)(*args)


class GeneratorDSC(DataSource):
    """A base class for data sources that implement fetching data using
    a generator member function
    """
    @abstractmethod
    def _generate_data(self):
        pass

    def __init__(self):
        super().__init__()
        for data_chunk in self._generate_data():
            self._data_to_views(data_chunk)
        self._eod_to_views()


class FunctionSet(Mapping):
    """A Mapping of named functions where functions can be added by decorating
    them, and collectively called in various ways
    """
    def __init__(self):
        self._funtions = {}

    def __getitem__(self, key):
        return self._funtions[key]

    def __iter__(self):
        return iter(self._funtions)

    def __len__(self):
        return len(self._funtions)

    def member(self, name):
        def decorator(func):
            self._funtions[name] = func
            return func
        return decorator

    def __call__(self, *args, **kwargs):
        for key, func in self._funtions.items():
            yield key, func(*args, **kwargs)

    def first_true(self, *args, **kwargs):
        return next((key for key, rv in self(*args, *kwargs) if rv), None)


class DataFrameView(metaclass=ABCMeta):
    def __init__(self, dsc):
        self._df = None

    @abstractmethod
    def create_dataframe(self, dsc):
        pass

    def on_data_loaded(self, dsc):
        self._df = self.create_dataframe(dsc)

    @property
    def df(self):
        return self._df
