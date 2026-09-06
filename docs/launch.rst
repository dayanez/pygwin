.. _launch:

************************************
Launch Options
************************************

Pygwin accepts the following command-line arguments:

.. code-block:: text

    pygwin [-h] [-V] [-c COMMAND] [-n] [-i] [-l] [--rc RC [RC ...]]
          [--no-rc] [--no-env] [--no-script-cache] [--cache-everything]
          [-D ITEM] [-st SHELL_TYPE] [--timings]
          [--save-origin-env] [--load-origin-env]
          [script-file] [args ...]

Arguments Reference
===================

``script-file``
    If present, execute the script and exit.

``args``
    Additional arguments passed to the script.

``-h``, ``--help``
    Show help and exit.

``-V``, ``--version``
    Show version information and exit.

``-c COMMAND``
    Run a single command and exit.

``-n``, ``--no-execute``
    Check syntax of the command, script, or stdin without running it.
    Exit non-zero on errors.  See also the ``pygwin check`` subcommand.

``-i``, ``--interactive``
    Force running in interactive mode.

``-l``, ``--login``
    Run as a login shell.

``--rc RC [RC ...]``
    The :doc:`pygwin RC <pygwinrc>` files to load. These may be either pygwin files or
    directories containing pygwin files.

``--no-rc``
    Do not load any pygwin RC files.  ``--rc`` is ignored when
    ``--no-rc`` is set.

``--no-env``
    Do not inherit parent environment variables.

``--no-script-cache``
    Do not cache scripts as they are run.

``--cache-everything``
    Use a cache, even for interactive commands.

``-D ITEM``
    Define an environment variable, in the form ``-DVAR=VAL``, or
    inherit an existing variable with ``-DVAR``.  May be used many
    times.

``-st``, ``--shell-type SHELL_TYPE``
    What kind of shell to use.  Possible values: ``best`` (``b``),
    ``prompt-toolkit`` (``ptk``, ``prompt_toolkit``),
    ``readline`` (``rl``), ``dumb`` (``d``), ``random`` (``rand``).
    Overrides ``$SHELL_TYPE``.

``--timings``
    Print timing information before the prompt is shown.  Useful for
    tracking down performance issues and investigating startup times.

``--save-origin-env``
    Save origin environment variables before running pygwin.  Use with
    ``--load-origin-env`` to restore them later.

``--load-origin-env``
    Load origin environment variables that were saved with
    ``--save-origin-env``.


Clean Environment
=================

Starting pygwin with ``--no-env`` drops the inherited environment, but
a few essential variables (``PATH``, ``TERM``, ``HOME``) will be
missing, which may cause warnings.  Use ``-D`` to pass them through:

.. code-block:: pygwin

    pygwin --no-rc --no-env  # works, but may warn about no TTY or no HOME

    # Create a convenient alias:
    aliases['pygwin-no-env'] = 'pygwin --no-rc --no-env -DPATH -DTERM -DHOME'
    pygwin-no-env


Minimal Startup
===============

For the fastest possible startup with no extras -- useful for scripting,
benchmarking, or debugging -- combine the flags to disable everything:

.. code-block:: pygwin

    pygwin --no-rc --no-env --shell-type readline \
          -DCOLOR_INPUT=0 -DCOLOR_RESULTS=0 -DPROMPT='@ ' \
          -DPYGWIN_HISTORY_BACKEND=dummy -DXONTRIBS_AUTOLOAD_DISABLED=1

What each flag does:

* ``--no-rc`` -- prevent loading RC files.
* ``--no-env`` -- prevent inheriting the environment.
* ``--shell-type readline`` -- use the cheapest shell backend.
* ``-DCOLOR_INPUT=0`` -- disable input coloring and the file-type
  completer that reads files to choose colors.
* ``-DCOLOR_RESULTS=0`` -- disable colors in output.
* ``-DPROMPT='@ '`` -- use a simple prompt instead of the default one
  with gitstatus and other complex fields.
* ``-DPYGWIN_HISTORY_BACKEND=dummy`` -- disable the history backend.
* ``-DXONTRIBS_AUTOLOAD_DISABLED=1`` -- skip loading xontribs.


.. _launch-xpygwin:

Launching the Same Pygwin (xpygwin)
=================================

The built-in ``xpygwin`` alias (see :ref:`aliases-xpygwin` for the alias
entry in the Built-in Aliases reference) launches exactly the same
``pygwin`` that was used to start the current session — same interpreter,
same source tree, regardless of the current working directory or whatever
is installed in ``site-packages``.

When another tool needs to spawn pygwin with the same identity as the
current session, use ``get_xpygwin_alias()`` from ``pygwin.aliases``: it
always returns a ``list`` so it can be concatenated with any other argv
list. For example, to start ``tmux`` with exactly this pygwin:

.. code-block:: pygwin

    aliases['xtmux'] = ['tmux', 'new-session'] + @.imp.pygwin.aliases.get_xpygwin_alias()


Save and Load Origin Environment
================================

When you launch a nested pygwin with ``--no-env``, all environment
variables from the parent session are dropped. Sometimes you want a
clean environment for a project but still need the original env with ``PATH``,
``TERM``, and other OS-level variables.

``--save-origin-env`` snapshots the current environment before running pygwin,
and ``--load-origin-env`` restores that snapshot inside the
new session. Together, they let you start a fresh pygwin from the current modified
environment.

For example, suppose you have a main pygwin session and you run
``pygwin --save-origin-env``. You're working, doing things, and then you need
to work with a project that has its own environment setup in ``project_rc.xsh``.
You don't want to source this file to avoid collisions, and you can't run a
pygwin instance with just ``--rc`` because the new session will inherit your current
environment.

In this case, you can run ``pygwin --load-origin-env --rc project_rc.xsh`` and
get a new, clean environment with project-specific aliases, environment variables,
and possibly a custom prompt as well.

After finishing work on that project, you can exit and return to your main environment.


Running from Another Shell
==========================

To launch pygwin from another shell, make sure that shell is itself running
in interactive mode — otherwise the OS will suspend the interactive pygwin
process. For example, when starting pygwin from a bash script, use an
interactive shebang (``#!/bin/bash -i``).


.. _launch-fg-takeover:

Controlling Terminal and Foreground Process Group
==================================================

At startup pygwin performs the industry-standard handshake used by interactive shells
to install itself as the foreground process group of its controlling terminal.

On POSIX, the first thing :func:`pygwin.main.main` does — before argument
parsing, xontrib loading, or :doc:`pygwin RC <pygwinrc>` execution — is call
:func:`pygwin.main._setup_controlling_terminal`. This function installs a
Python-level no-op handler for ``SIGTTIN`` and ``SIGTTOU`` on every POSIX
invocation. If ``os.isatty(stderr)`` is true, it then calls
:func:`pygwin.main._acquire_controlling_terminal`; otherwise it returns after
installing the handlers.

``_acquire_controlling_terminal`` uses stderr (file descriptor 2) as the TTY
handle, matching :func:`pygwin.procs.jobs.give_terminal_to`. It blocks
``SIGTTOU``, ``SIGTTIN``, ``SIGTSTP``, and ``SIGCHLD`` in the calling thread
with ``pthread_sigmask``. If the TTY's foreground group is already the current
process group, it short-circuits to success without registering an ``atexit``
restorer. Otherwise it calls ``setpgid(0, 0)`` followed by
``tcsetpgrp(tty_fd, getpgrp())``, remembers the previous foreground group, and
records the success. The signal mask is restored in a ``finally`` block.

Control returns to ``_setup_controlling_terminal``, which branches on the
result. On success, the Python no-op handlers stay in place, and
:func:`pygwin.main._release_controlling_terminal` is registered with
:mod:`atexit` only when foreground ownership was actually transferred. On
failure, the Python no-op handlers are replaced with ``SIG_IGN`` for
``SIGTTIN`` and ``SIGTTOU``. ``_setup_controlling_terminal`` is idempotent and
is also called from the top of :func:`pygwin.main.main_pygwin`, with the second
call short-circuiting on the ``_tty_setup_done`` module flag.

On shutdown, if the ``atexit`` restorer was registered,
``_release_controlling_terminal`` calls ``tcsetpgrp`` to hand the previous
foreground group back to the parent shell with ``SIGTTOU`` blocked during the
call. If the parent has already reclaimed the TTY, or if the fd is no longer
valid, the error is swallowed. In every other case — no handshake ran, the
fast path was taken, or the handshake failed — the restorer is a no-op.

When the handshake is a no-op
------------------------------

The handshake itself is skipped, though the Python no-op handlers for
``SIGTTIN`` and ``SIGTTOU`` are still installed, on Windows; in non-interactive
invocations where stderr is not a TTY, such as ``pygwin script.xsh``, piped
input, redirected stderr, script-from-stdin mode, and pytest runs that capture
stderr via a pipe; when pygwin is a session leader (``getsid(0) == getpid()``);
when pygwin is already the foreground group, in which case the fast path
returns and the ``atexit`` restorer is not registered; and when
``pthread_sigmask`` is not available on the platform.

Disabling the handshake
------------------------

Set ``PYGWIN_NO_FG_TAKEOVER=1`` in the parent environment (before launching
pygwin) to skip the handshake entirely. When the handshake is disabled, pygwin
falls back to installing ``SIG_IGN`` for ``SIGTTIN`` and ``SIGTTOU``.

.. code-block:: bash

    # disable the takeover
    PYGWIN_NO_FG_TAKEOVER=1 pygwin


Tips
====

When passing multi-statement commands to ``pygwin -c``, the
:ref:`subprocess expression macro <macros>` ``@!()`` lets you avoid
manual quoting — it captures its content as a literal string and passes
it as a single argument:

.. code-block:: pygwin

    $(@lines pygwin -c @!(echo hello; echo world))

See :ref:`macros` for more on ``@!()``.

Subcommands
===========

* ``pygwin format`` -- format pygwin source files in place, à la Black
  (``--check`` / ``--diff`` supported). Run ``pygwin format --help``.
* ``pygwin check`` -- check pygwin source files for syntax errors without
  running them; the ``-n`` / ``--no-execute`` flag does the same for a
  ``-c`` command, a script file, or piped stdin. Run ``pygwin check --help``.
* ``pygwin lint`` -- lint pygwin source files for likely mistakes (env-var
  typos, bad env-var values, deprecated vars, unused imports), without
  running them. Run ``pygwin lint --help``.


See also
========

* :doc:`pygwin RC <pygwinrc>` -- RC file loading and configuration snippets
* :doc:`env` -- environment variables and type system
* :doc:`envvars` -- full list of environment variables
