from argparse import Namespace
from collections import deque
from unittest.mock import MagicMock, call, create_autospec

import pytest

from review_wof.model.base import DataSource, FunctionSet, GeneratorDSC


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


class TestFuncitonSet:
    def test_setup_and_call(self):
        func_set = FunctionSet()

        @func_set.member('first func')
        @create_autospec
        def func1(a1, a2, kw1, kw2):
            pass

        @func_set.member('second func')
        @create_autospec
        def func2(*args, **kwargs):
            pass

        @func_set.member('third func')
        @create_autospec
        def func3(*args, **kwargs):
            pass

        expected_set = {
            'first func': func1,
            'second func': func2,
            'third func': func3,
        }

        assert func_set == expected_set
        # test that insertion order is preserved
        assert list(func_set) == list(expected_set)
        results = func_set('v1', 'v2', kw1='v3', kw2='v4')
        other_funcs = deque(expected_set.values())
        for (key, value), (expkey, func) in zip(results, expected_set.items()):
            assert key == expkey
            # Mark the return values we got
            value.mark(key)
            # check that the function was called and we got the results
            assert func.mock_calls == [
                call('v1', 'v2', kw1='v3', kw2='v4'),
                call('v1', 'v2', kw1='v3', kw2='v4').mark(key),
            ]
            # Make sure other functions were not called yet
            other_funcs.popleft()
            for other_func in other_funcs:
                assert other_func.mock_calls == []

    @pytest.fixture
    def truth_set_maker(self):
        def make_set(truth_sequence):
            func_set = FunctionSet()
            for idx, value in enumerate(truth_sequence):
                func_set.member(f'f{idx}')(MagicMock(side_effect=(value,)))
            return func_set
        return make_set


    @pytest.mark.parametrize('truth_sequence,expected_key', [
        ((False, True, True, False), 'f1'),
        ((False, False, False), None),
    ])
    def test_first_true(self, truth_set_maker, truth_sequence, expected_key):
        truth_set = truth_set_maker(truth_sequence)
        result = truth_set.first_true('some_args')
        assert result == expected_key
        should_been_called = True
        for key, func in truth_set.items():
            if should_been_called:
                assert func.mock_calls == [call('some_args')], \
                    f'{key} function should`ve been called'
            else:
                assert func.mock_calls == [], \
                    f'{key} function should`nt have been called'
            if key == expected_key:
                should_been_called = False
