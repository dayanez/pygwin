"""DEPRECATED: Use `pygwin.lib.lazyasd` instead of `pygwin.lazyimps`."""

import warnings

warnings.warn(
    "Use `pygwin.lib.lazyimps` instead of `pygwin.lazyimps`.",
    DeprecationWarning,
    stacklevel=2,
)

from pygwin.lib.lazyimps import *  # noqa
