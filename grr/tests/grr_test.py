#!/usr/bin/env python3

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

    def shell_exec(self, args):
        self.executed.append(args)
        return ''


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

if __name__ == '__main__':
    unittest.main()
