#!/usr/bin/env python3

import json
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
            d = json.load(f)
        return d


class TestGrr:
    def test_pull(self):
        # grr pull
        mock = MockGrr({})
        mock.run('pull')
        assert mock.executed == [
            ['git', 'fetch', 'origin'],
            ['git', 'checkout', 'origin/master']
        ]

        # grr pull
        mock = MockGrr({'rebase': True})
        mock.run('pull')
        assert mock.executed == [
            ['git', 'fetch', 'origin'],
            ['git', 'rebase', 'origin/master']
        ]

        # grr pull develop
        mock = MockGrr({})
        mock.run('pull', 'develop')
        assert mock.executed == [
            ['git', 'fetch', 'origin'],
            ['git', 'checkout', 'origin/develop']
        ]

    def test_checkout(self):
        # grr checkout
        mock = MockGrr({})
        mock.run('checkout')
        assert mock.executed == [
            ['git', 'checkout', 'origin/master']
        ]

        # grr checkout develop
        mock = MockGrr({})
        mock.run('checkout', 'develop')
        assert mock.executed == [
            ['git', 'checkout', 'origin/develop']
        ]

    def test_fetch(self):
        # grr fetch 12345:2
        mock = MockGrr({})
        mock.run('fetch', '12345:2')
        assert mock.executed == [
            ['git', 'fetch', 'https://gerrit.example.org/r/gerrit/example', 'refs/changes/45/12345/2'],
            ['git', 'checkout', 'FETCH_HEAD']
        ]

        # grr fetch 12345
        # Note: this test is based on rest_api.json
        mock = MockGrr({})
        mock.run('fetch', '12345')
        assert mock.executed == [
            ['git', 'fetch', 'https://gerrit.wikimedia.org/r/mediawiki/core', 'refs/changes/25/303525/1'],
            ['git', 'checkout', 'FETCH_HEAD']
        ]

    def test_cherry_pick(self):
        # grr fetch 12345:2
        mock = MockGrr({})
        mock.run('cherry-pick', '12345:2')
        assert mock.executed == [
            ['git', 'fetch', 'https://gerrit.example.org/r/gerrit/example', 'refs/changes/45/12345/2'],
            ['git', 'cherry-pick', 'FETCH_HEAD']
        ]

        # grr fetch 12345
        # Note: this test is based on rest_api.json
        mock = MockGrr({})
        mock.run('cherry-pick', '12345')
        assert mock.executed == [
            ['git', 'fetch', 'https://gerrit.wikimedia.org/r/mediawiki/core', 'refs/changes/25/303525/1'],
            ['git', 'cherry-pick', 'FETCH_HEAD']
        ]

    def test_review(self):
        # grr review
        mock = MockGrr({})
        mock.run('review')
        assert mock.executed == [
            ['git', 'config', '--get', 'gitreview.remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master']
        ]

        # grr review develop
        mock = MockGrr({})
        mock.run('review', 'develop')
        assert mock.executed == [
            ['git', 'config', '--get', 'gitreview.remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/develop']
        ]

        # grr review --topic=foo-bar-topic
        mock = MockGrr({})
        mock.options = {'topic': 'foo-bar-topic'}
        mock.run('review')
        assert mock.executed == [
            ['git', 'config', '--get', 'gitreview.remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master%topic=foo-bar-topic']
        ]

        # grr review --code-review=+2 --submit --verified=+2
        mock = MockGrr({})
        mock.options = {'code-review': '+2', 'submit': True, 'verified': '+2'}
        mock.run('review')
        assert mock.executed == [
            ['git', 'config', '--get', 'gitreview.remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master%l=Code-Review+2,l=Verified+2,submit']
        ]

        # grr review --hashtags=one,two,three
        mock = MockGrr({})
        mock.options = {'hashtags': 'one,two,three'}
        mock.run('review')
        assert mock.executed == [
            ['git', 'config', '--get', 'gitreview.remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master%t=one,t=two,t=three']
        ]

        # grr
        mock = MockGrr({})
        mock.run()
        assert mock.executed == [
            ['git', 'config', '--get', 'gitreview.remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master']
        ]

        # grr develop
        mock = MockGrr({})
        mock.run('develop')
        assert mock.executed == [
            ['git', 'config', '--get', 'gitreview.remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/develop']
        ]

        # remote set to origin
        mock = MockGrr({})
        mock._remote = 'origin'
        mock.run()
        assert mock.executed == [
            ['git', 'push', 'origin', 'HEAD:refs/for/master']
        ]
