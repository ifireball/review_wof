from unittest.mock import create_autospec, call
from argparse import Namespace

from review_wof.model.base import DataSource, GeneratorDSC

def test_data_source():
    class Adsc(DataSource):
        pass

    @Adsc.view('streamed')
    @create_autospec
    class StreamedView:
        def on_new_data(self, dsc, data):
            pass

    @Adsc.view('finished')
    @create_autospec
    class FinishedView:
        def on_data_loaded(self, dsc):
            pass

    @Adsc.view('streamed_n_finished')
    @create_autospec
    class StreamedNFinishedView:
        def on_new_data(self, dsc, data):
            pass

        def on_data_loaded(self, dsc):
            pass

    view_classes = Namespace(
        streamed=StreamedView,
        finished=FinishedView,
        streamed_n_finished=StreamedNFinishedView,
    )
    assert Adsc.views == view_classes

    dsc = Adsc()
    for (vcn, vc), (vn, vo) in zip(
        vars(dsc.views).items(), vars(view_classes).items()
    ):
        assert vcn == vn
        assert id(vc) != id(vo)
    dsc._data_to_views('d1')
    dsc._data_to_views('d2')
    dsc._eod_to_views()

    assert StreamedView.mock_calls == [
        call(dsc),
        call().on_new_data(dsc, 'd1'),
        call().on_new_data(dsc, 'd2'),
    ]
    assert FinishedView.mock_calls == [
        call(dsc),
        call().on_data_loaded(dsc),
    ]
    assert StreamedNFinishedView.mock_calls == [
        call(dsc),
        call().on_new_data(dsc, 'd1'),
        call().on_new_data(dsc, 'd2'),
        call().on_data_loaded(dsc),
    ]


def test_generator_dsc(monkeypatch):
    class AGenDsc(GeneratorDSC):
        def _generate_data(self):
            yield 'dat1'
            yield 'dat2'

    data_to_views = create_autospec(AGenDsc._data_to_views)
    eod_to_views = create_autospec(AGenDsc._eod_to_views)
    monkeypatch.setattr(AGenDsc, '_data_to_views', data_to_views)
    monkeypatch.setattr(AGenDsc, '_eod_to_views', eod_to_views)

    dsc = AGenDsc()
    assert data_to_views.mock_calls == [
        call(dsc, 'dat1'),
        call(dsc, 'dat2'),
    ]
    assert eod_to_views.mock_calls == [
        call(dsc),
    ]
