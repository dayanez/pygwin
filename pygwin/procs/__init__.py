"""Subprocess and pipeline execution for the pygwin shell.

Contains :class:`~pygwin.procs.specs.SubprocSpec` construction, command
pipelines, job control, callable-alias proxies, platform-specific process
helpers and pipe/stream readers.
"""

# Fix https://github.com/xonsh/xonsh/pull/5437
from pygwin.procs import proxies  # noqa
