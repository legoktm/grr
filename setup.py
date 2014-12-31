#!/usr/bin/env python3
from setuptools import setup
import sys

setup(
    name='grr',
    version='0.2.1',
    author='Kunal Mehta',
    author_email='legoktm@gmail.com',
    url='https://github.com/legoktm/grr/',
    license='CC-0',
    description='A command-line utility to work with Gerrit',
    long_description=open('README.rst').read(),
    packages=['grr'],
    install_requires=['configparser'] if sys.version_info[0] == 2 else [],
    entry_points={
        'console_scripts': [
            'grr = grr:main'
        ],
    }
)
