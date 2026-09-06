"""Implements the pygwin parser."""

import os

from pygwin.lib.lazyasd import lazyobject
from pygwin.platform_info import PYTHON_VERSION_INFO


@lazyobject
def Parser():
    if os.environ.get("PYGWIN_RD_PARSER"):
        from pygwin.parsers.rd_parser import Parser as p
    elif PYTHON_VERSION_INFO >= (3, 13):
        from pygwin.parsers.v313 import Parser as p
    elif PYTHON_VERSION_INFO > (3, 10):
        from pygwin.parsers.v310 import Parser as p
    elif PYTHON_VERSION_INFO > (3, 9):
        from pygwin.parsers.v39 import Parser as p
    elif PYTHON_VERSION_INFO > (3, 8):
        from pygwin.parsers.v38 import Parser as p
    else:
        from pygwin.parsers.v36 import Parser as p
    return p
