#!/usr/bin/env python3
"""
Copyright (C) 2014-2016 Kunal Mehta

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import argparse
import configparser
import json
import os.path
import shutil
import subprocess
import sys
from urllib.request import urlopen


class Grr:
    def __init__(self, options):
        self.options = options
        self._username = None
        self._config = None
        self._remote = None

    def debug(self, text):
        if self.options.get('debug'):
            self.out(text)

    def out(self, text):
        print(text)

    def shell_exec(self, args):
        self.debug('$ ' + ' '.join(args))
        return subprocess.check_output(args).decode()

    def run(self, args: list):
        action = args.pop(0)
        self.debug('action: {0}, args: {1}'.format(action, ' '.join(args)))
        if action == 'init':
            # grr init
            self.init_repo()
        elif action == 'fetch':
            # grr fetch 12345
            # grr fetch 12345:2
            self.fetch(args[0])
            self.shell_exec(['git', 'checkout', 'FETCH_HEAD'])
        elif action == 'cherry-pick':
            # grr fetch 12345
            # grr fetch 12345:2
            self.fetch(args[0])
            self.shell_exec(['git', 'cherry-pick', 'FETCH_HEAD'])
        elif action == 'pull':
            # grr pull
            # grr pull REL1_24
            self.pull(*args)
        elif action == 'checkout':
            # grr checkout
            # grr checkout REL1_24
            self.checkout(*args)
        elif action == 'review':
            # grr review REL1_24
            self.review(*args)
        else:
            raise RuntimeError('Should not be possible to reach here')

    @property
    def config(self):
        if self._config is None:
            # Find the repository root
            root = self.shell_exec(['git', 'rev-parse', '--show-toplevel']).strip()
            self.debug('Parsing .gitreview file...')
            config = configparser.ConfigParser()
            config.read(os.path.join(root, '.gitreview'))
            self._config = config['gerrit']
        return self._config

    def rest_api(self, query):
        self.debug('Making API request to: {query}'.format(query=query))
        req = urlopen('https://{host}/r/{query}'.format(host=self.config['host'], query=query))
        resp = req.read().decode()[4:]
        return json.loads(resp)

    @property
    def username(self):
        if self._username is None:
            try:
                username = self.shell_exec(['git', 'config', '--get', 'gitreview.username']).strip()
            except subprocess.CalledProcessError:
                username = input('Please enter your gerrit username: ').strip()
            self._username = username
        return self._username

    @property
    def remote(self):
        if self._remote is None:
            try:
                self._remote = self.shell_exec(['git', 'config', '--get', 'gitreview.remote']).strip()
            except subprocess.CalledProcessError:
                pass

            if not self._remote:
                self._remote = 'gerrit'
        return self._remote

    def checkout(self, branch='master', quiet=False):
        args = ['git', 'checkout', 'origin/{0}'.format(branch)]
        if quiet:
            args.append('-q')
        try:
            self.shell_exec(args)
        except subprocess.CalledProcessError:
            self.out('Checkout failed')
            sys.exit(1)

    def rebase(self, branch='master', quiet=False):
        args = ['git', 'rebase', 'origin/{0}'.format(branch)]
        if quiet:
            args.append('-q')
        try:
            self.shell_exec(args)
        except subprocess.CalledProcessError:
            self.out('Rebase failed')
            sys.exit(1)

    def pull(self, branch='master'):
        try:
            self.shell_exec(['git', 'fetch', 'origin'])
        except subprocess.CalledProcessError:
            self.out('Fetching origin failed')
            sys.exit(1)
        if self.options.get('rebase'):
            self.rebase(branch)
        else:
            self.checkout(branch)

    def review(self, branch='master'):
        self.init_repo()
        to = 'HEAD:refs/for/{0}'.format(branch)
        extra = []
        if 'topic' in self.options:
            extra.append('topic=' + self.options['topic'])
        if 'code_review' in self.options:
            extra.append('l=Code-Review' + self.options['code_review'])
        if 'verified' in self.options:
            extra.append('l=Verified' + self.options['verified'])
        if self.options.get('submit'):
            extra.append('submit')
        if 'hashtags' in self.options:
            for hashtag in self.options['hashtags'].split(','):
                extra.append('t=' + hashtag)
        if extra:
            to += '%' + ','.join(extra)
        try:
            self.shell_exec(['git', 'push', self.remote, to])
        except subprocess.CalledProcessError:
            sys.exit(1)

    def fetch(self, changeset):
        if ':' in changeset:
            change, patch = changeset.split(':', 1)
            fetch = {
                'url': 'https://{host}/r/{name}'.format(
                    host=self.config['host'],
                    name=self.config['project'].rsplit('.', 1)[0]
                ),
                'ref': 'refs/changes/{0}/{1}/{2}'.format(change[-2:], change, patch)
            }
        else:
            change = changeset
            query = self.rest_api('changes/{0}?o=CURRENT_REVISION'.format(change))
            current_rev = query['current_revision']
            fetch = query['revisions'][current_rev]['fetch']['anonymous http']
        self.shell_exec(['git', 'fetch', fetch['url'], fetch['ref']])

    def init_repo(self):
        git_dir = self.shell_exec(['git', 'rev-parse', '--git-dir']).strip()
        path = os.path.join(git_dir, 'hooks/commit-msg')
        if os.path.isfile(path):
            # Already configured
            return False
        shutil.copy(os.path.join(os.path.dirname(__file__), 'commit-msg'), path)
        self.out('Installed commit-msg hook')


def parse_args(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable extra debugging output')
    subparsers = parser.add_subparsers(dest='action')
    subparsers.add_parser('init')
    fetch = subparsers.add_parser('fetch')
    fetch.add_argument('patch', help='Patchset to fetch')
    cherry_pick = subparsers.add_parser('cherry-pick')
    cherry_pick.add_argument('patch', help='Patchset to cherry-pick')
    pull = subparsers.add_parser('pull')
    pull.add_argument('branch', nargs='?', default='master', help='Pull this branch')
    pull.add_argument('--rebase', action='store_true', help='Rebase instead of checking out the remote branch')
    checkout = subparsers.add_parser('checkout')
    checkout.add_argument('branch', nargs='?', default='master', help='Checkout this branch')
    review = subparsers.add_parser('review')
    review.add_argument('branch', nargs='?', default='master', help='Submit patch to this branch')
    review.add_argument('--topic', help='Gerrit topic for new patchset')
    review.add_argument('--code-review', help='Set Code-Review label when uploading patch')
    review.add_argument('--verified', help='Set Verified label when uploading patch')
    review.add_argument('--submit', action='store_true', help='Submit patch after uploading')
    review.add_argument('--hashtags', help='Comma-separated hashtags to set')

    if not argv:
        # `grr` defaults to `grr review`
        argv.append('review')
    elif len(argv) >= 1 and argv[0] not in subparsers.choices:
        # Add in a default action of 'review'
        argv.insert(0, 'review')

    parsed = vars(parser.parse_args(argv))
    args = [parsed.pop('action')]
    if 'branch' in parsed:
        args.append(parsed.pop('branch'))

    # Filter out None values
    options = {k: v for k, v in parsed.items() if v not in (None, False)}

    return args, options


def main():
    args, options = parse_args(sys.argv[1:])
    g = Grr(options=options)
    g.run(args)


if __name__ == '__main__':
    main()
