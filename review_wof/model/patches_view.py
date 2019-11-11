"""model/patches_view.py - DV Listing gerrit patches and they statuses
"""
from pandas import DataFrame

from .base import FunctionSet, DataFrameView
from .gerrit_patches import GerritPatches


@GerritPatches.view('list')
class PatchesView(DataFrameView):
    def __init__(self, dsc):
        super().__init__(dsc)
        self._load_buffer = []

    def on_new_data(self, dsc, patch):
        record = {
            'url': patch['url'],
            'number': patch['number'],
            'subject': patch['subject'],
            'state': self._get_patch_state(dsc, patch),
        }
        self._load_buffer.append(record)

    def create_dataframe(self, dsc):
        df = DataFrame(self._load_buffer)
        del self._load_buffer
        return df

    def _get_patch_state(self, dsc, patch):
        return _patch_states.first_true(
            patch, dsc.since, dsc.until, dsc.review_flags_for(patch)
        )

_patch_states = FunctionSet()

@_patch_states.member('Review done')
def patch_with_review_done(patch, since, until, review_flags):
    return any(
        any(
            (since <= approval['grantedOn'] <= until) and
            (approval['type'] in review_flags) and
            (int(approval['value']) >= 2)
            for approval in patchset.get('approvals', [])
        )
        for patchset in patch.get('patchSets', [])
    )

@_patch_states.member('Voted upon')
def _voted_patch(patch, since, until, review_flags):
    return any(
        any(
            (since <= approval['grantedOn'] <= until) and
            (approval['type'] in review_flags)
            for approval in patchset.get('approvals', [])
        )
        for patchset in patch.get('patchSets', [])
    )

@_patch_states.member('Commented upon')
def _commented_patch(patch, since, until, review_flags):
    return any(
        since <= comment['timestamp'] <= until
        for comment in patch.get('comments', [])
    )

@_patch_states.member('Updated')
def _updated_patch(patch, since, until, review_flags):
    return since <= patch.get('lastUpdated', 0) <= until

@_patch_states.member('Stalled')
def _stalled_patch(patch, since, until, review_flags):
    return patch.get('open', True)
