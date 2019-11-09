"""model/gerrit_patches.py - DSC for Gerrit patches
"""
import json
from subprocess import check_output
from time import time

from .base import GeneratorDSC


GERRIT_QUERY_LIMIT = 50
GERRIT_HOST = 'gerrit.ovirt.org'
PROJECTS = {'jenkins', 'infra-docs', 'repoman'}
REVIEW_FLAGS = {"Code-Review"}
BLACKLISTED_USERS = {
    'jenkins-staging', 'jenkins@ovirt.org', 'jenkins_ro', 'zuul@ovirt.org',
    'automation@ovirt.org',
}


class GerritPatches(GeneratorDSC):
    def __init__(self, since=None, until=None):
        if until is None:
            until = int(time())
        if since is None:
            since = until - (60 * 60 * 24 * 30)
        self._since, self._until = since, until
        super().__init__()

    @property
    def since(self):
        return self._since

    @property
    def until(self):
        return self._until

    def review_flags_for(self, patch):
        return REVIEW_FLAGS

    @property
    def blacklisted_users(self):
        return BLACKLISTED_USERS

    def _generate_data(self):
        patches = self._get_patches_for_timespan(
            GERRIT_HOST, PROJECTS, self._since, self._until
        )
        yield from patches

    @classmethod
    def _get_patches_for_timespan(cls, gerrit_host, projects, since, until):
        for project in projects:
            for patch in cls._get_patches_by_status(
                gerrit_host, project, 'open'
            ):
                yield patch
            for patch in cls._get_patches_by_status(
                gerrit_host, project, 'closed'
            ):
                if patch.get('lastUpdated', 0) < since:
                    break
                yield patch

    @staticmethod
    def _get_patches_by_status(gerrit_host, project, status):
        skip = 0
        results_cnt = GERRIT_QUERY_LIMIT
        while results_cnt >= GERRIT_QUERY_LIMIT:
            js = check_output([
                'ssh', gerrit_host, '-p', '29418', 'gerrit', 'query',
                '--comments', '--all-approvals', '--format=JSON',
                '--start', str(skip), 'limit:' + str(GERRIT_QUERY_LIMIT),
                'project:' + project, 'status:' + status,
            ])
            lines = js.splitlines()
            results_cnt = len(lines) - 1
            for line in lines:
                patch = json.loads(line)
                if patch.get('type') == 'stats':
                    continue
                yield patch
            results_cnt = len(lines) - 1
            skip += results_cnt
