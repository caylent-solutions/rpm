# Supported Python Versions

## Summary

Python 3.11 or later is required. RPM Git Repo is tested against Python 3.11, 3.12, 3.13, and 3.14.

## repo hooks

Projects that use [repo hooks] run on independent schedules.
Since it's not possible to detect what version of Python the hooks were written
or tested against, we always import & exec them with the active Python version.

If the user's Python is too new for the [repo hooks], then it is up to the hooks
maintainer to update.

## Repo launcher

The [repo launcher] is an independent script that can support older versions of
Python without holding back the rest of the codebase.
If it detects the current version of Python is too old, it will try to reexec
via a newer version of Python via standard `pythonX.Y` interpreter names.

If your default python interpreters are too old to run the launcher even though
you have newer versions installed, you can modify the [repo launcher]'s shebang
to suit your environment.

## Older Python Versions

Python versions below 3.11 are not supported. If you need to use an older
Python version, consider using the upstream repo tool directly.

[repo hooks]: ./repo-hooks.md
[repo launcher]: ../repo
