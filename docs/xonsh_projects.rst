.. _pygwin_projects:

**************
Pygwin Projects
**************
Bam! Suppose you want to get beyond scripting and write a whole
library, utility, or other big project in pygwin. Here is how you do
that. Spoiler alert: it is easy, powerful, and fun!

Overview
================================
Pygwin is fully interoperable with Python. Writing a pygwin library is
very similar to writing a Python library, using all of the same tooling
and infrastructure for packaging pure Python code.

Structure
==========
Pygwin modules are written in pygwin files (``*.xsh``), side-by-side with Python files
(``*.py``). Suppose we have a package called ``mypkg`` which uses pygwin files.
Here is a sample file system layout would be::

    |- mypkg/
       |- __init__.py    # a regular package with an init file
       |- other.py       # not a pygwin file
       |- show.py        # "mypkg.show", full module name
       |- tell.xsh       # "mypkg.tell", full module name
       |- subpkg/
          |- __init__.py
          |- a.py      # "mypkg.subpkg.a", full module name
          |- b.xsh     # "mypkg.subpkg.b", full module name

To ensure that these files are installed, you need to declare the
``*.xsh`` files as package data in your project's ``pyproject.toml``.
For the above structure, this looks like the following.

.. code-block:: toml

    [build-system]
    requires = ["setuptools>=61"]
    build-backend = "setuptools.build_meta"

    [project]
    name = "mypkg"
    version = "0.1.0"

    [tool.setuptools]
    packages = ["mypkg", "mypkg.subpkg"]

    [tool.setuptools.package-data]
    mypkg = ["*.xsh"]
    "mypkg.subpkg" = ["*.xsh"]

With this, the pygwin code will be installed and included in any source
distribution you create!

Setting up pygwin sessions
=========================
Pygwin code requires a ``PygwinSession`` to exist as ``builtins.__pygwin__`` and for
be that object to be setup correctly. This can be quite a bit of work and
the exact setup depends on the execution context. To simplify the process
of constructing the session properly, pygwin provides the ``pygwin.main.setup()``
function specifically for use in 3rd party packages.

While ``pygwin.main.setup()`` is safely re-entrant, it is a good idea to add the following
snippet to the root-level ``__init__.py`` of your project. With the ``mypkg`` example
above, the session setup is as follows:

``mypkg/__init__.py``

.. code-block:: python

    from pygwin.main import setup
    setup()
    del setup

Enjoy!

.. _formatting_pygwin_code:

Formatting pygwin code
=====================
Pygwin ships a built-in formatter, available as the ``pygwin format``
subcommand. It re-emits the source with normalized indentation,
spacing and blank-line rules while preserving every pygwin-specific
construct.

Format a single file in place:

.. code-block:: pygwincon

    @ pygwin format mypkg/tell.xsh

Format several files at once — every path that needs reformatting is
rewritten on disk, and a status line is printed for each:

.. code-block:: pygwincon

    @ pygwin format mypkg/tell.xsh mypkg/subpkg/b.xsh

Read from standard input and write the result to standard output —
the canonical way to produce a separate output file or to plug the
formatter into an editor / pipeline:

.. code-block:: pygwincon

    @ pygwin format - < 1.xsh > 2.xsh

Useful flags:

* ``--check`` — don't touch any files. Exits with code ``1`` if at
  least one file would be reformatted, ``0`` otherwise. Handy for CI.
* ``--diff`` — print a unified diff for each file that would change,
  again without touching disk.
* ``-q`` / ``--quiet`` — suppress per-file status messages on stderr.

For example, to fail a CI job when any file needs reformatting:

.. code-block:: pygwincon

    @ pygwin format --check mypkg


CLI app on Pygwin
================

Building a command-line application on Pygwin is easy: you write and package it
like any other Python project, so it is installable, testable, and
distributable out of the box. For a basic implementation to start from, see the
`pygwin-awesome-cli-app`_ template — fork it and add your own commands.

For commands that live inside a session rather than a standalone app, Pygwin also
ships built-in :ref:`Click CLI Integration <click_cli_integration>` that
registers a Click command as an alias.

.. _pygwin-awesome-cli-app: https://github.com/anki-code/xonsh-awesome-cli-app/
