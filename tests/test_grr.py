#!/usr/bin/env python3

import json
import pytest
import os

import grr


class MockGrr(grr.Grr):
    def __init__(self, options):
        super(MockGrr, self).__init__(options)
        self.executed = []
        self._config = {
            'host': 'gerrit.example.org',
            'project': 'gerrit/example.git',
            'port': '29418'
        }

    def init_repo(self):
        # Don't write to the filesystem when testing
        return False

    def shell_exec(self, args):
        self.executed.append(args)
        return ''

    def rest_api(self, query):
        with open(os.path.join(os.path.dirname(__file__), 'rest_api.json')) as f:
            return json.load(f)


@pytest.mark.parametrize('options,run,executed', [
    # grr pull
    ({}, ['pull'], [
        ['git', 'fetch', 'origin'],
        ['git', 'checkout', 'origin/master']
    ]),
    # grr pull --rebase
    ({'rebase': True}, ['pull'], [
        ['git', 'fetch', 'origin'],
        ['git', 'rebase', 'origin/master']
    ]),
    # grr pull develop
    ({}, ['pull', 'develop'], [
        ['git', 'fetch', 'origin'],
        ['git', 'checkout', 'origin/develop']
    ]),
    # grr checkout
    ({}, ['checkout'], [
        ['git', 'checkout', 'origin/master']
    ]),
    # grr checkout develop
    ({}, ['checkout', 'develop'], [
        ['git', 'checkout', 'origin/develop']
    ]),
    # grr fetch 12345:2
    ({'patch': '12345:2'}, ['fetch'], [
        ['git', 'fetch', 'https://gerrit.example.org/r/gerrit/example', 'refs/changes/45/12345/2'],
        ['git', 'checkout', 'FETCH_HEAD']
    ]),
    # grr fetch 12345
    # Note: this test is based on rest_api.json
    ({'patch': '12345'}, ['fetch'], [
        ['git', 'fetch', 'https://gerrit.wikimedia.org/r/mediawiki/core', 'refs/changes/25/303525/1'],
        ['git', 'checkout', 'FETCH_HEAD']
    ]),
    # grr cherry-pick 12345:2
    ({'patch': '12345:2'}, ['cherry-pick'], [
        ['git', 'fetch', 'https://gerrit.example.org/r/gerrit/example', 'refs/changes/45/12345/2'],
        ['git', 'cherry-pick', 'FETCH_HEAD']
    ]),
    # grr cherry-pick 12345
    # Note: this test is based on rest_api.json
    ({'patch': '12345'}, ['cherry-pick'], [
        ['git', 'fetch', 'https://gerrit.wikimedia.org/r/mediawiki/core', 'refs/changes/25/303525/1'],
        ['git', 'cherry-pick', 'FETCH_HEAD']
    ]),
    # grr review
    ({}, ['review'], [
        ['git', 'config', '--get', 'gitreview.remote'],
        ['git', 'push', 'gerrit', 'HEAD:refs/for/master']
    ]),
    # grr review develop
    ({}, ['review', 'develop'], [
        ['git', 'config', '--get', 'gitreview.remote'],
        ['git', 'push', 'gerrit', 'HEAD:refs/for/develop']
    ]),
    # grr review --topic=foo-bar-topic
    ({'topic': 'foo-bar-topic'}, ['review'], [
        ['git', 'config', '--get', 'gitreview.remote'],
        ['git', 'push', 'gerrit', 'HEAD:refs/for/master%topic=foo-bar-topic']
    ]),
    # grr review --code-review=+2 --submit --verified=+2
    ({'code_review': '+2', 'submit': True, 'verified': '+2'}, ['review'], [
        ['git', 'config', '--get', 'gitreview.remote'],
        ['git', 'push', 'gerrit', 'HEAD:refs/for/master%l=Code-Review+2,l=Verified+2,submit']
    ]),
    # grr review --hashtags=one,two,three
    ({'hashtags': 'one,two,three'}, ['review'], [
        ['git', 'config', '--get', 'gitreview.remote'],
        ['git', 'push', 'gerrit', 'HEAD:refs/for/master%t=one,t=two,t=three']
    ]),
    # grr
    ({}, ['review', 'master'], [
        ['git', 'config', '--get', 'gitreview.remote'],
        ['git', 'push', 'gerrit', 'HEAD:refs/for/master']
    ]),
    # grr develop
    ({}, ['review', 'develop'], [
        ['git', 'config', '--get', 'gitreview.remote'],
        ['git', 'push', 'gerrit', 'HEAD:refs/for/develop']
    ]),
])
def test_grr(options, run, executed):
    mock = MockGrr(options)
    mock.run(run)
    assert mock.executed == executed


def test_review():
    # remote set to origin
    mock = MockGrr({})
    mock._remote = 'origin'
    mock.run(['review', 'master'])
    assert mock.executed == [
        ['git', 'push', 'origin', 'HEAD:refs/for/master']
    ]


@pytest.mark.parametrize('argv,expected', (
    ('pull', (['pull', 'master'], {})),
    ('pull --rebase', (['pull', 'master'], {'rebase': True})),
    ('pull develop', (['pull', 'develop'], {})),
    ('review', (['review', 'master'], {})),
    ('review develop', (['review', 'develop'], {})),
    ('review --topic=foo-bar-topic', (['review', 'master'], {'topic': 'foo-bar-topic'})),
    ('review --code-review=+2 --submit --verified=+2', (['review', 'master'], {'code_review': '+2',
                                                                               'submit': True, 'verified': '+2'})),
    ('review --hashtags=one,two,three', (['review', 'master'], {'hashtags': 'one,two,three'})),
    ('develop', (['review', 'develop'], {})),
    ('init', (['init'], {})),
    ('fetch 12345', (['fetch'], {'patch': '12345'})),
))
def test_parse_args(argv, expected):
    actual = grr.parse_args(argv.split(' '))
    assert actual == expected


def test_parse_args_none():
    assert grr.parse_args([]) == (['review', 'master'], {})
