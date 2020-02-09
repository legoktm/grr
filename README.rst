grr
===
.. image:: https://travis-ci.org/legoktm/grr.svg?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/legoktm/grr

.. image:: https://img.shields.io/pypi/v/grr.svg
    :target: https://pypi.python.org/pypi/grr/
    :alt: Latest Version

``grr`` is a simple utility to make using Gerrit a little less painful. It requires Python 3.5+.

The basic workflow involves using a detached head, and pulling down changes from gerrit to
work on them, and re-submitting them. Inspired by git-review_, ``grr`` reads from ``.gitreview`` files
and will try to use your ``gitreview.username`` setting.

Installation:

.. code-block:: bash

    pip install grr


* ``grr init``: Adds a `gerrit` remote and installs the commit-msg hook
* ``grr fetch 12345[:2]``: Pulls change 12345. An optional patchset # can be specified, otherwise the latest will be used.
* ``grr cherry-pick 12345[:2]``: Just like fetch, except it cherry-picks the patch on top of HEAD.
* ``grr pull [master]``: Pulls the latest remote changes and checks out the given branch, defaults to master.
* ``grr checkout [master]``: Checkout the given branch, defaults to master
* ``grr review [branch]``: Uploads your patches for review, the branch defaults to master.
* ``grr [branch]``: Shorthand for `grr review`.

Licensed as GPLv3 or later, see COPYING for details.

.. _git-review: https://pypi.python.org/pypi/git-review
