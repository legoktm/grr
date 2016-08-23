#!/usr/bin/env python3

import json
import os
import unittest

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
        self.already_init = False

    def shell_exec(self, args):
        self.executed.append(args)
        if args == ['git', 'remote'] and self.already_init:
            # This is kind of hacky but...
            return 'gerrit\n'
        return ''

    def rest_api(self, query):
        with open(os.path.join(os.path.dirname(__file__), 'rest_api.json')) as f:
            d = json.load(f)
        return d


class GrrTest(unittest.TestCase):
    def test_pull(self):
        # grr pull
        mock = MockGrr({})
        mock.run('pull')
        self.assertEqual(mock.executed, [
            ['git', 'fetch', 'origin'],
            ['git', 'checkout', 'origin/master']
        ])

        # grr pull develop
        mock = MockGrr({})
        mock.run('pull', 'develop')
        self.assertEqual(mock.executed, [
            ['git', 'fetch', 'origin'],
            ['git', 'checkout', 'origin/develop']
        ])

    def test_checkout(self):
        # grr checkout
        mock = MockGrr({})
        mock.run('checkout')
        self.assertEqual(mock.executed, [
            ['git', 'checkout', 'origin/master']
        ])

        # grr checkout develop
        mock = MockGrr({})
        mock.run('checkout', 'develop')
        self.assertEqual(mock.executed, [
            ['git', 'checkout', 'origin/develop']
        ])

    def test_fetch(self):
        # grr fetch 12345:2
        mock = MockGrr({})
        mock.run('fetch', '12345:2')
        self.assertEqual(mock.executed, [
            ['git', 'fetch', 'https://gerrit.example.org/r/gerrit/example', 'refs/changes/45/12345/2'],
            ['git', 'checkout', 'FETCH_HEAD']
        ])

        # grr fetch 12345
        # Note: this test is based on rest_api.json
        mock = MockGrr({})
        mock.run('fetch', '12345')
        self.assertEqual(mock.executed, [
            ['git', 'fetch', 'https://gerrit.wikimedia.org/r/mediawiki/core', 'refs/changes/25/303525/1'],
            ['git', 'checkout', 'FETCH_HEAD']
        ])

    def test_cherry_pick(self):
        # grr fetch 12345:2
        mock = MockGrr({})
        mock.run('cherry-pick', '12345:2')
        self.assertEqual(mock.executed, [
            ['git', 'fetch', 'https://gerrit.example.org/r/gerrit/example', 'refs/changes/45/12345/2'],
            ['git', 'cherry-pick', 'FETCH_HEAD']
        ])

        # grr fetch 12345
        # Note: this test is based on rest_api.json
        mock = MockGrr({})
        mock.run('cherry-pick', '12345')
        self.assertEqual(mock.executed, [
            ['git', 'fetch', 'https://gerrit.wikimedia.org/r/mediawiki/core', 'refs/changes/25/303525/1'],
            ['git', 'cherry-pick', 'FETCH_HEAD']
        ])

    def test_init_repo(self):
        mock = MockGrr({})
        mock._username = 'ExampleUser'
        mock.run('init')
        self.assertEqual(mock.executed, [
            ['git', 'remote'],
            ['git', 'remote', 'add', 'gerrit', 'ssh://ExampleUser@gerrit.example.org:29418/gerrit/example.git'],
            ['scp', '-P29418', 'ExampleUser@gerrit.example.org:hooks/commit-msg', '.git/hooks/commit-msg'],
            ['git', 'checkout', 'origin/master', '-q']
        ])

        mock = MockGrr({})
        mock._username = 'ExampleUser'
        mock.already_init = True
        mock.run('init')
        self.assertEqual(mock.executed, [
            ['git', 'remote'],
            ['git', 'checkout', 'origin/master', '-q']
        ])

    def test_review(self):
        # grr review
        mock = MockGrr({})
        mock.already_init = True
        mock.run('review')
        self.assertEqual(mock.executed, [
            ['git', 'remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master']
        ])

        # grr review develop
        mock = MockGrr({})
        mock.already_init = True
        mock.run('review', 'develop')
        self.assertEqual(mock.executed, [
            ['git', 'remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/develop']
        ])

        # grr review --topic=foo-bar-topic
        mock = MockGrr({})
        mock.already_init = True
        mock.options = {'topic': 'foo-bar-topic'}
        mock.run('review')
        self.assertEqual(mock.executed, [
            ['git', 'remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master%topic=foo-bar-topic']
        ])

        # grr
        mock = MockGrr({})
        mock.already_init = True
        mock.run()
        self.assertEqual(mock.executed, [
            ['git', 'remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/master']
        ])

        # grr develop
        mock = MockGrr({})
        mock.already_init = True
        mock.run('develop')
        self.assertEqual(mock.executed, [
            ['git', 'remote'],
            ['git', 'push', 'gerrit', 'HEAD:refs/for/develop']
        ])

if __name__ == '__main__':
    unittest.main()
