"""review_wof.py - Build report of patches and reviews
"""
from collections import Counter, OrderedDict
from subprocess import check_output
import json
from functools import partial
from time import time
from flask import Flask, render_template


application = Flask(__name__)


GERRIT_HOST = 'gerrit.ovirt.org'
GERRIT_QUERY_LIMIT = 50
PROJECTS = {'jenkins', 'infra-docs', 'repoman'}
REVIEW_FLAGS = {"Code-Review"}
BLACKLISTED_USERS = {
    'jenkins-staging', 'jenkins@ovirt.org', 'jenkins_ro', 'zuul@ovirt.org',
    'automation@ovirt.org',
}

patch_states = OrderedDict()
people_states = OrderedDict()


@application.route('/')
def index():
    people, patch_state_counts = create_report()
    return render_template(
        'index.html.j2',
        people=people,
        patch_state_counts=patch_state_counts,
    )


def create_report():
    until = int(time())
    since = until - (60 * 60 * 24 * 30)
    patches = get_patches(GERRIT_HOST, PROJECTS, since, until)
    people = {}
    patch_state_counts = Counter()
    for patch in patches:
        update_people_states(patch, people, since, until)
        update_patch_states(patch, patch_state_counts, since, until)
    for user in BLACKLISTED_USERS:
        if user in people:
            del people[user]
    return people, patch_state_counts


def get_patches(gerrit_host, projects, since, until):
    for project in projects:
        for patch in get_patches_from_query(
            gerrit_host, project, ['status:open']
        ):
            yield patch
        for patch in get_patches_from_query(
            gerrit_host, project, ['status:closed']
        ):
            if patch.get('lastUpdated', 0) < since:
                break
            yield patch


def get_patches_from_query(gerrit_host, project, query=[]):
    skip = 0
    results_cnt = GERRIT_QUERY_LIMIT
    while results_cnt >= GERRIT_QUERY_LIMIT:
        js = check_output([
            'ssh', gerrit_host, '-p', '29418', 'gerrit', 'query',
            '--comments', '--all-approvals', '--format=JSON',
            '--start', str(skip), 'limit:' + str(GERRIT_QUERY_LIMIT),
            'project:' + project,
        ] + query)
        lines = js.splitlines()
        results_cnt = len(lines) - 1
        for line in lines:
            patch = json.loads(line)
            if patch.get('type') == 'stats':
                continue
            yield patch
        results_cnt = len(lines) - 1
        skip += results_cnt


def update_people_states(patch, people, since, until):
    state_for_person = {}
    for state, finder in people_states.items():
        people_in_state = set(finder(patch, since, until))
        for person in people_in_state:
            state_for_person[person] = state
    for person, state in state_for_person.items():
        person_state_counters = people.setdefault(person, Counter())
        person_state_counters[state] += 1


def update_patch_states(patch, patch_state_counts, since, until):
    for state, predicate in reversed(list(patch_states.items())):
        if predicate(patch, since, until):
            patch_state_counts[state] += 1
            break


def state_decorator(state_predicate_map, state_name):
    def decorator(fun):
        state_predicate_map[state_name] = fun
        return fun
    return decorator


patch_state = partial(state_decorator, patch_states)
people_state = partial(state_decorator, people_states)


@patch_state('Stalled')
def stalled_patch(patch, since, until):
    return patch.get('open', True)


@patch_state('Updated')
def updated_patch(patch, since, until):
    return since <= patch.get('lastUpdated', 0) <= until


@patch_state('Commented upon')
def commented_patch(patch, since, until):
    return any(
        since <= comment['timestamp'] <= until
        for comment in patch.get('comments', [])
    )


@patch_state('Voted upon')
def voted_patch(patch, since, until):
    return any(
        any(
            (since <= approval['grantedOn'] <= until) and
            (approval['type'] in REVIEW_FLAGS)
            for approval in patchset.get('approvals', [])
        )
        for patchset in patch.get('patchSets', [])
    )


@patch_state('Review done')
def patch_with_review_done(patch, since, until):
    return any(
        any(
            (since <= approval['grantedOn'] <= until) and
            (approval['type'] in REVIEW_FLAGS) and
            (int(approval['value']) >= 2)
            for approval in patchset.get('approvals', [])
        )
        for patchset in patch.get('patchSets', [])
    )


@patch_state('Merged or abandoned')
def merged_or_abandoned_patch(patch, since, until):
    return \
        (not patch.get('open', True)) \
        and (since <= patch.get('lastUpdated', 0) <= until)


@people_state('Commented')
def people_who_commented(patch, since, until):
    for comment in patch.get('comments', []):
        if since <= comment['timestamp'] <= until:
            yield user_key(comment['reviewer'])


@people_state('Voted')
def people_who_voted(patch, since, until):
    for patchset in patch.get('patchSets', []):
        for person in people_who_voted_in_patchset(patchset, since, until):
            yield person


@people_state('Voted on latest PatchSet')
def people_who_voted_on_latest_patchset(patch, since, until):
    patchsets = patch.get('patchSets', [])
    if not patchsets:
        return
    for person in people_who_voted_in_patchset(patchsets[-1], since, until):
        yield person


def user_key(user_rec):
    return user_rec.get('email', user_rec['username'])


def people_who_voted_in_patchset(patchset, since, until):
    for approval in patchset.get("approvals", []):
        if not (since <= approval['grantedOn'] <= until):
            continue
        if approval['type'] not in REVIEW_FLAGS:
            continue
        yield user_key(approval['by'])
