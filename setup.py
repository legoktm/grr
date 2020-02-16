#!/usr/bin/env python3
from setuptools import setup

setup(
    name='grr',
    version='1.0.1',
    author='Kunal Mehta',
    author_email='legoktm@member.fsf.org',
    url='https://github.com/legoktm/grr/',
    license='GPL-3.0-or-later',
    description='A command-line utility to work with Gerrit',
    long_description=open('README.rst').read(),
    packages=['grr'],
    install_requires=[],
    python_requires='>=3.5',
    entry_points={
        'console_scripts': [
            'grr = grr:main'
        ],
    },
    include_package_data=True,
)
