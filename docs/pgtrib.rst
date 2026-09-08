.. _pgtrib:

**********
Extensions
**********

Overview
========
pygwin is an extensible, user-patchable platform: third-party developers can
build and distribute their own extensions without going through the pygwin
release cycle, and end users can reshape any subsystem directly from their
:doc:`pygwin RC <pygwinrc>` because every part of pygwin is a Python module.
In the pygwin ecosystem these extensions are called *pgtribs*.

A pgtrib can be:

* a set of aliases — plain strings, lists, or callable Python functions
* a tab-completer for a single command or a whole API
* a prompt field (e.g. battery, container, version-control, kubernetes)
* a handler for session events such as ``on_chdir``, ``on_postcommand``,
  or ``on_pre_prompt``
* a new environment variable or ``$PYGWIN_*`` setting
* a full subsystem — syntax-highlighting tokens, a history backend, an
  integration with an external tool, and so on

Search and Install Pgtribs
===========================
Two good places to look for pgtribs published by the community:

* `Awesome xontribs <https://xonsh.github.io/awesome-xontribs/>`_ — curated
  list of xontribs written for real xonsh. pygwin's own pgtrib protocol has
  diverged from xonsh's (see Authoring Pgtribs below), so these are not
  directly installable in pygwin, but are a good source of ideas to port.
* `GitHub xontrib topic <https://github.com/topics/xontrib>`_ — every
  repository tagged with the ``xontrib`` topic on GitHub, for the same
  real-xonsh-ecosystem caveat as above.


Listing Known Pgtribs
======================
The ``pgtrib`` command allows you to list the installed pgtribs.
This command will report if they are loaded in the current session. To display this
information, pass the ``list`` action to the ``pgtrib`` command:

.. code-block:: pygwincon

    @ pgtrib list
    abbrevs             not-loaded          Expand command abbreviations while typing in the Pygwin shell.
    clp                 not-loaded          Copy output to clipboard. Cross-platform.
    cmd_done            not-loaded          Show long running commands durations in prompt with option to send notification when terminal is not focused.
    jedi                not-loaded          Use Jedi as pygwin's python completer.
    output_search       not-loaded          Get identifiers, paths, URLs and words from the previous command output and use them for the next command in pygwin shell
    pipeliner           not-loaded          Let your pipe lines flow thru the Python code in pygwin.
    prompt_starship     not-loaded          Starship cross-shell prompt in pygwin shell.
    sh                  not-loaded          Paste and run commands from bash, zsh, fish, tcsh in pygwin shell.

    @ pgtrib info sh
    Name: sh
    Source: pgtrib.sh at /Users/snail/.local/pygwin-env/lib/python3.14/site-packages/pgtrib/sh.py
    Description: Paste and run commands from bash, zsh, fish, tcsh in pygwin shell.
    Loaded: no

For programmatic access, you may also have this command print a JSON formatted
string:

.. code-block:: pygwincon

    @ $(@json pgtrib list --json)['abbrevs']
    {'name': 'abbrevs',
     'loaded': False,
     'auto': False,
     'module': 'pgtrib.abbrevs',
     'description': 'Expand command abbreviations while typing in the Pygwin shell.'}

Loading Pgtribs
================
Pgtribs may be loaded in a few different ways: from your :doc:`pygwin RC <pygwinrc>`,
dynamically at runtime with the ``pgtrib`` command, or its Python API.

Extensions are loaded via the ``pgtrib load`` command.
This command may be run from anywhere in your :doc:`pygwin RC <pygwinrc>` or at any point
after pygwin has started up.

.. code-block:: pygwin

    pgtrib load myext mpl mypkg.show

Pass ``-s`` (``--suppress-warnings``) to load every pgtrib that is installed and
silently skip any name that isn't. Useful in a :doc:`pygwin RC <pygwinrc>` that is shared across machines
where only a subset of pgtribs is installed.

The same can be done in Python as well

.. code-block:: python

    from pygwin.pgtribs import pgtribs_load
    pgtribs_load(['myext', 'mpl', 'mypkg.show'])

A pgtrib can be unloaded from the current session using ``pgtrib unload``

.. code-block:: pygwin

    pgtrib unload myext mpl mypkg.show

Pgtribs can use `setuptools entrypoints <https://setuptools.pypa.io/en/latest/userguide/entry_point.html?highlight=entrypoints>`_
to mark themselves available for autoloading using the below format.

.. code-block:: ini

    [options.entry_points]
    pygwin.pgtribs =
        pgtrib_name = path.to.the.module

Here the module should contain ``_load_pgtrib_`` function as described above.

.. note::

    Please make sure that importing the pgtrib module and calling ``_load_pgtrib_`` is fast enough.
    Otherwise it will affect the shell's startup time.
    Any other imports or heavy computations should be done in lazy manner whenever possible.


Authoring Pgtribs
==================
xonsh's `xontrib-template <https://github.com/xonsh/xontrib-template>`_
repository is a reasonable starting skeleton for the packaging metadata and
entry-point wiring, but its actual plugin code uses xonsh's ``_load_xontrib_``
convention, not pygwin's ``_load_pgtrib_`` one (see below), so it needs that
one rename before it will actually load in pygwin.

Structure
================
Pgtribs are modules with some special functions written
in either pygwin (``*.xsh``) or Python (``*.py``).

Here is a template:

.. code-block:: python

    from pygwin.built_ins import PygwinSession

    def _load_pgtrib_(xsh: PygwinSession, **kwargs) -> dict:
        """
        this function will be called when loading/reloading the pgtrib.

        Args:
            xsh: the current pygwin session instance, serves as the interface to manipulate the session.
                 This allows you to register new aliases, history backends, event listeners ...
            **kwargs: it is empty as of now. Kept for future proofing.
        Returns:
            dict: this will get loaded into the current execution context
        """

    def _unload_pgtrib_(xsh: PygwinSession, **kwargs) -> dict:
        """If you want your extension to be unloadable, put that logic here"""

.. warning::

    The pgtrib must implement ``_unload_pgtrib_`` itself. If this function
    is not provided, any registered event handlers, environment variables,
    aliases, and completers will remain active after ``pgtribs unload/reload``.

This _load_pgtrib_() function is called after your extension is imported,
and the currently active :py:class:`pygwin.built_ins.PygwinSession` instance is passed as the argument.

.. note::

    Pgtribs without ``_load_pgtrib_`` are still supported.
    But when such pgtrib is loaded, variables listed
    in ``__all__`` are placed in the current
    execution context if defined.

Normally, these are stored and found in an
`implicit namespace package <https://www.python.org/dev/peps/pep-0420/>`_
called ``pgtrib``. However, pgtribs may be placed in any package or directory
that is on the ``$PYTHONPATH``.

If a module is in the ``pgtrib`` namespace package, it can be referred to just
by its module name. If a module is in any other package, then it must be
referred to by its full package path, separated by ``.`` like you would in an
import statement.  Of course, a module in ``pgtrib`` may be referred to
with the full ``pgtrib.myext``. But just calling it ``myext`` is a lot shorter
and one of the main advantages of placing an extension in the ``pgtrib``
namespace package.

Here is a sample file system layout and what the pgtrib names would be::

    |- pgtrib/
       |- javert.xsh     # "javert", because in pgtrib
       |- your.py        # "your",
       |- eyes/
          |- __init__.py
          |- scream.xsh  # "eyes.scream", because eyes is in pgtrib
    |- mypkg/
       |- __init__.py    # a regular package with an init file
       |- other.py       # not a pgtrib
       |- show.py        # "mypkg.show", full module name
       |- tell.xsh       # "mypkg.tell", full module name
       |- subpkg/
          |- __init__.py
          |- done.py     # "mypkg.subpkg.done", full module name


You can also use xonsh's `xontrib template <https://github.com/xonsh/xontrib-cookiecutter>`_
to easily create the layout for a pgtrib package (with the same
``_load_xontrib_``-to-``_load_pgtrib_`` caveat as above).


Sharing a Pgtrib
================

pygwin is a personal, single-maintainer project (see ``AGENTS.md``): it has no
community registry of its own, and does not accept pull requests. A pgtrib is
just a regular Python package, so the ordinary way to share one is publishing
it to PyPI or a public git repository and telling people directly, the same
as any other Python package. Do not register it in xonsh's own
`awesome-xontribs <https://github.com/xonsh/awesome-xontribs>`_ registry or
tag it with the `xontrib <https://github.com/topics/xontrib>`_ GitHub topic:
those are for real xonsh xontribs, and a pgtrib is not one (see Authoring
Pgtribs above).

See also
========

* :doc:`events_tutorial` -- using events in pgtribs
* :doc:`env` -- registering environment variables for your pgtrib
* :doc:`completers` -- writing custom completers
* `Awesome-xontribs <https://github.com/xonsh/awesome-xontribs>`_ -- registry of community xontribs written for real xonsh
* `Xontrib template <https://github.com/xonsh/xontrib-template>`_ -- quickstart template (for a real xonsh xontrib; see the ``_load_xontrib_``/``_load_pgtrib_`` caveat above)
