"""model/base.py - Base classes for data model
"""
from abc import ABCMeta, abstractmethod
from argparse import Namespace


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
