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

import configparser
import json
import os.path
import subprocess
import sys
from urllib.request import urlopen


class Grr:
    def __init__(self, options):
        self.options = options
        self._username = None
        self._config = None

    def debug(self, text):
        if self.options.get('debug'):
            self.out(text)

    def out(self, text):
        print(text)

    def shell_exec(self, args):
        self.debug('$ ' + ' '.join(args))
        return subprocess.check_output(args).decode()

    def run(self, *args):
        args = list(args)
        if args:
            action = args.pop(0)
        else:
            action = 'review'
        self.debug('action: {0}, args: {1}'.format(action, ' '.join(args)))
        if action == 'init':
            # grr init
            self.init_repo()
            self.checkout(branch='master', quiet=True)
        elif action == 'fetch':
            # grr 12345
            # grr 12345:2
            self.fetch(args[0])
        elif action == 'pull':
            # grr pull
            # grr pull REL1_24
            self.pull(args[0])
        elif action == 'checkout':
            # grr checkout
            # grr checkout REL1_24
            self.checkout(args[0])
        elif action == 'review':
            # grr review REL1_24
            self.review(args[0])
        elif not action:
            # grr
            self.review()
        else:
            # grr branch
            self.review(action)

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
                username = self.shell_exec(['git', 'config', 'gitreview.username']).strip()
            except subprocess.CalledProcessError:
                username = input('Please enter your gerrit username: ').strip()
                self.shell_exec(['git', 'config', '--get', 'gitreview.username', username])
            self._username = username
        return self._username

    def checkout(self, branch='master', quiet=False):
        args = ['git', 'checkout', 'origin/{0}'.format(branch)]
        if quiet:
            args.append('-q')
        self.shell_exec(args)

    def pull(self, branch='master'):
        self.shell_exec(['git', 'fetch', 'origin'])
        self.checkout(branch)

    def review(self, branch='master'):
        self.init_repo()
        to = 'HEAD:refs/for/{0}'.format(branch)
        if 'topic' in self.options:
            to += '%topic=' + self.options['topic']
        self.shell_exec(['git', 'push', 'gerrit', to])

    def fetch(self, changeset):
        if ':' in changeset:
            change, patch = changeset.split(':', 1)
            fetch = {
                'url': 'https://{host}/r/{name}'.format(
                    host=self.config['host'],
                    name=self.config['project'].strip('.git')
                ),
                'ref': 'refs/changes/{0}/{1}/{2}'.format(change[-2:], change, patch)
            }
        else:
            change = changeset
            query = self.rest_api('changes/{0}?o=CURRENT_REVISION'.format(change))
            current_rev = query['current_revision']
            fetch = query['revisions'][current_rev]['fetch']['anonymous http']
        self.shell_exec(['git', 'fetch', fetch['url'], fetch['ref']])
        self.shell_exec(['git', 'checkout', 'FETCH_HEAD'])

    def init_repo(self):
        output = self.shell_exec(['git', 'remote'])
        if 'gerrit\n' in output:
            # Remote already setup
            return False
        remote = 'ssh://{username}@{host}:{port}/{project}'.format(username=self.username, **self.config)
        self.shell_exec(['git', 'remote', 'add', 'gerrit', remote])
        self.out('Added gerrit remote')
        commit_msg = '{username}@{host}:hooks/commit-msg'.format(username=self.username, **self.config)
        self.shell_exec(['scp', '-P' + self.config['port'], commit_msg, '.git/hooks/commit-msg'])
        self.out('Installed commit-msg hook')


def main():
    args = sys.argv[1:]
    options = {}
    for arg in args[:]:
        if arg.startswith('--'):
            opt = arg[2:]
            if '=' in opt:
                sp = opt.split('=', 1)
                options[sp[0]] = sp[1]
            else:
                options[opt] = True
            args.remove(arg)
    g = Grr(options=options)
    g.run(*args)

if __name__ == '__main__':
    main()
