"""Core utils (cat, echo, pwd, ...) implemented in Python.

The current list includes:

* cat
* echo
* pwd
* tee
* tty
* yes

In many cases, these may have a lower performance overhead than the
posix command line utility with the same name. This is because these
tools avoid the need for a full subprocess call. Additionally, these
tools are cross-platform.
"""

from pygwin.built_ins import PygwinSession
from pygwin.platform_info import ON_POSIX
from pygwin.xoreutils.cat import cat
from pygwin.xoreutils.echo import echo
from pygwin.xoreutils.pwd import pwd
from pygwin.xoreutils.tee import tee
from pygwin.xoreutils.tty import tty
from pygwin.xoreutils.umask import umask
from pygwin.xoreutils.uname import uname
from pygwin.xoreutils.uptime import uptime
from pygwin.xoreutils.yes import yes


def _load_pgtrib_(xsh: PygwinSession, **_):
    xsh.aliases["cat"] = cat
    xsh.aliases["echo"] = echo
    xsh.aliases["pwd"] = pwd
    xsh.aliases["tee"] = tee
    xsh.aliases["tty"] = tty
    xsh.aliases["uname"] = uname
    xsh.aliases["uptime"] = uptime
    xsh.aliases["umask"] = umask
    xsh.aliases["yes"] = yes
    if ON_POSIX:
        from pygwin.xoreutils.ulimit import ulimit

        xsh.aliases["ulimit"] = ulimit
