grr
===
.. image:: https://travis-ci.org/legoktm/grr.svg?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/legoktm/grr

grr is a simple utility to make using Gerrit a little less painful.

The basic workflow involves using a detached head, and pulling down changes from gerrit to
work on them, and re-submitting them. Inspired by git-review, grr reads from .gitreview files
and will try to use your gitreview.username setting.

Installation: pip install grr


* grr init: Adds a `gerrit` remote and installs the commit-msg hook
* grr fetch 12345[:2]: Pulls change 12345. An optional patchset # can be specified, otherwise the latest will be used.
* grr pull [master]: Pulls the latest remote changes and checks out the given branch, defaults to master.
* grr checkout [master]: Checkout the given branch, defaults to master
* grr review [branch]: Uploads your patches for review, the branch defaults to master.
* grr [branch]: Shorthand for `grr review`.

Licensed as CC-0.
