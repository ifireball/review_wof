"""model/patch_reviewers_view.py - DV Linking users to patches
"""
from functools import partial

from pandas import DataFrame

from .base import DataFrameView, FunctionSet
from .gerrit_patches import GerritPatches


@GerritPatches.view('reviewers')
class PatchReviewersView(DataFrameView):
    def __init__(self, dsc):
        super().__init__(dsc)
        self._load_buffer = []
        self._uk_set = partial(_user_keys_set, dsc.blacklisted_users)

    def on_new_data(self, dsc, patch):
        states_and_people = ((s, self._uk_set(p)) for s, p in _people_states(
            patch, dsc.since, dsc.until, dsc.review_flags_for(patch)
        ))
        seen_people = set()
        for state, people in states_and_people:
            people_in_state = people - seen_people
            if not people_in_state:
                continue
            seen_people |= people
            self._load_buffer.append(
                [patch['url'], state, list(people_in_state)]
            )

    def create_dataframe(self, dsc):
        df = DataFrame(
            self._load_buffer, columns=('patch', 'state', 'reviewers')
        )
        del self._load_buffer
        df = df.explode('reviewers')
        df.reset_index(drop=True, inplace=True)
        return df


def _user_keys_set(blacklisted_users, user_records):
    key_set = set(
        user_rec.get('email', user_rec['username'])
        for user_rec in user_records
    )
    return key_set - blacklisted_users


_people_states = FunctionSet()


@_people_states.member('Voted on latest PatchSet')
def _people_who_voted_on_latest_patchset(patch, since, until, review_flags):
    patchsets = patch.get('patchSets', [])
    if not patchsets:
        return iter([])
    return _people_who_voted_in_patchset(
        patchsets[-1], since, until, review_flags
    )


@_people_states.member('Voted')
def _people_who_voted(patch, since, until, review_flags):
    for patchset in patch.get('patchSets', []):
        return \
            _people_who_voted_in_patchset(patchset, since, until, review_flags)


@_people_states.member('Commented')
def _people_who_commented(patch, since, until, review_flags):
    for comment in patch.get('comments', []):
        if since <= comment['timestamp'] <= until:
            yield comment['reviewer']


def _people_who_voted_in_patchset(patchset, since, until, review_flags):
    for approval in patchset.get("approvals", []):
        if not (since <= approval['grantedOn'] <= until):
            continue
        if approval['type'] not in review_flags:
            continue
        yield approval['by']
