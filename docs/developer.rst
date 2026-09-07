.. _developer:

Developer's Guide
=============================

.. image:: _static/knight-vs-snail.jpg

Welcome to the pygwin developer's guide! This is a place for developers to
place information that does not belong in the user's guide or the library
reference but is useful or necessary for the next people that come along to
develop pygwin.

.. note:: pygwin is a personal daily-driver project maintained by one person,
   not a team codebase; see AGENTS.md in the repository root for how changes
   are actually made (no pull request review process, no issue tracker).


Making Your First Change
-------------------------

Terminal-based workflow
^^^^^^^^^^^^^^^^^^^^^^^

The simplified terminal-based workflow to work on pygwin:

.. code-block:: bash

    mkdir -p ~/git && cd ~/git
    git clone https://github.com/dayanez/pygwin.git
    # You can setup IDE (see next section) to extremely speed up the work and test.
    cd pygwin

    # Install dev packages.
    # python -m ensurepip --upgrade  # install pip if you have python without pip
    pip install -U pip
    pip install '.[dev]' '.[doc]'

    # Make changes: add new environment variable.
    vim pygwin/environ.py

    # Create test.
    vim tests/environ.py
    python -m pytest

    # Live test.
    python -m pygwin --no-rc

    # Commit locally.
    git add pygwin/environ.py tests/environ.py
    git commit -m "Add new environment variable"

IDE-based workflow
^^^^^^^^^^^^^^^^^^

You can also use IDE like PyCharm:

1. Install IDE e.g. `PyCharm <https://www.jetbrains.com/pycharm/>`_.
2. Go to ``File -> Project from Version Control -> URL`` https://github.com/dayanez/pygwin
3. Go to the terminal and update pip and install full dependencies:

   .. code-block:: pygwin

       # Run from PyCharm terminal with appropriate environment.
       python -m pip install -U pip  # you need pip >= 24
       python -m pip install '.[full]' '.[dev]' '.[doc]'

4. Setup IDE e.g. PyCharm:

   .. code-block:: text

       Create project based on pygwin code directory.
       Click "Run" - "Run..." - "Edit Configurations"
       Click "+" and choose "Python". Set:
           Name: "pygwin --no-rc".
           Run: choose "module" and write "pygwin".
           Script parameters: "--no-rc -DFROM=PYCHARM" (here "FROM" will help to identify process using `ps ax | grep PYCHARM`).
           Working directory: "/tmp"  # to avoid corrupting the source code during experiments
           Environment variables: add ";PYGWIN_SHOW_TRACEBACK=1"
           Modify options: click "Emulate terminal in output console".
       Save settings.

       Open `pygwin/procs/specs.py` and `def run_subproc` function.
       Put breakpoint to `specs = cmds_to_specs` code. See also: https://www.jetbrains.com/help/pycharm/using-breakpoints.html
       Click "Run" - "Debug..." - "pygwin". Now you can see pygwin prompt.
       Run `echo 1` and now you're in the debug mode on the breakpoint.
       Press F8 to step forward. Good luck!

5. Create a git branch for your change and test it live in the debugger.


Changelog
----------

`CHANGELOG.md <CHANGELOG.md>`_ is maintained by hand, not generated from commit
messages. Add an entry under ``## Unreleased`` describing what changed and why
as part of the same change.


Style Guide
------------

pygwin is a pure Python project, and so we use PEP8 (with some additions) to
ensure consistency throughout the code base.

Rules to Write By
^^^^^^^^^^^^^^^^^^

It is important to refer to things and concepts by their most specific name.
When writing pygwin code or documentation please use technical terms
appropriately. The following rules help provide needed clarity.

Interfaces
"""""""""""

* User-facing APIs should be as generic and robust as possible.
* Tests belong in the top-level ``tests`` directory.
* Documentation belongs in the top-level ``docs`` directory.

Expectations
"""""""""""""

* Code must have associated tests and adequate documentation.
* User-interaction code (such as the Shell class) is hard to test.
  Mechanism to test such constructs should be developed over time.
* Have *extreme* empathy for your users.
* Be selfish. Since you will be writing tests you will be your first user.

Python Style Guide
^^^^^^^^^^^^^^^^^^^

pygwin follows `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ for all Python code. The following rules apply where
`PEP8 <https://www.python.org/dev/peps/pep-0008/>`_ is open to interpretation.

* Use absolute imports (``import pygwin.tools``) rather than explicit
  relative imports (``import .tools``). Implicit relative imports
  (``import tools``) are never allowed.
* We use sphinx with the numpydoc extension to autogenerate API documentation. Follow
  the `numpydoc <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_ standard for docstrings.
* Simple functions should have simple docstrings.
* Lines should be at most 80 characters long. The 72 and 79 character
  recommendations from PEP8 are not required here.
* Tests should be written with `pytest <https://docs.pytest.org/>`_ using a procedural style. Do not use
  unittest directly or write tests in an object-oriented style.
* Test generators make more dots and the dots must flow!
* We use `ruff <https://docs.astral.sh/ruff/>`_ for linting and formatting the code. It is used as a `pre-commit <https://pre-commit.com/>`_ hook. Enable it by running:

.. code-block:: bash

    pre-commit install
    pre-commit run --all-files


How to Test
------------

Dependencies
^^^^^^^^^^^^^

Prep your environment for running the tests:

.. code-block:: bash

    pip install -e '.[dev]'

Running the Tests - Basic
^^^^^^^^^^^^^^^^^^^^^^^^^^

Run all the tests using pytest. Use ``python -m pytest`` to prevent using pygwin code from ``site-packages`` if pygwin was installed in the same environment:

.. code-block:: bash

    python -m pytest -q

Use "-q" to keep pytest from outputting a bunch of info for every test.

Running the Tests - Advanced
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To perform all unit tests:

.. code-block:: bash

    python -m pytest

If you want to run specific tests you can specify the test names to
execute. For example to run test_aliases:

.. code-block:: bash

    python -m pytest test_aliases.py

Note that you can pass multiple test names in the above examples:

.. code-block:: bash

    python -m pytest test_aliases.py test_environ.py

Running the Tests in Parallel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

On a multi-core machine
`pytest-xdist <https://pypi.org/project/pytest-xdist/>`_ runs tests
several times faster by distributing work across worker processes:

.. code-block:: bash

    pip install pytest-xdist
    python -m pytest -n auto

``-n auto`` uses one worker per CPU core. Pass an explicit integer
(``-n 4``) to cap the worker count.

Writing the Tests - Advanced
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(refer to pytest documentation)

With the Pytest framework you can use bare ``assert`` statements on
anything you're trying to test, note that the name of the test function
has to be prefixed with ``test_``:

.. code-block:: python

    def test_whatever():
        assert is_true_or_false

The conftest.py in tests directory defines fixtures for mocking various
parts of pygwin for more test isolation. For a list of the various fixtures:

.. code-block:: bash

    python -m pytest --fixtures

when writing tests it's best to use pytest features i.e. parametrization:

.. code-block:: python

    @pytest.mark.parametrize('env', [test_env1, test_env2])
    def test_one(env, xession):
        # update the environment variables instead of setting the attribute
        # which could result in leaks to other tests.
        # each run will have the same set of default env variables set.
        xession.env.update(env)
        ...

this will run the test two times each time with the respective ``test_env``.
This can be done with a for loop too but the test will run
only once for the different test cases and you get less isolation.

With that in mind, each test should have the least ``assert`` statements,
preferably one.

At the moment, pygwin doesn't support any pytest plugins.

Happy Testing!


How to Document
----------------

Documentation takes many forms. This will guide you through the steps of
successful documentation.

Docstrings
^^^^^^^^^^^

No matter what language you are writing in, you should always have
documentation strings along with you code. This is so important that it is
part of the style guide. When writing in Python, your docstrings should be
in reStructured Text using the `numpydoc <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_ format.

Auto-Documentation Hooks
^^^^^^^^^^^^^^^^^^^^^^^^^^

The docstrings that you have written will automatically be connected to the
website, once the appropriate hooks have been setup. At this stage, all
documentation lives within pygwin's top-level ``docs`` directory.
We uses the sphinx tool to manage and generate the documentation, which
you can learn about from `the sphinx website <http://sphinx-doc.org/>`_.
If you want to generate the documentation, first pygwin itself must be installed
and then you may run the following command from the ``docs`` dir:

.. code-block:: bash

    cd docs/
    make html

For each new
module, you will have to supply the appropriate hooks. This should be done the
first time that the module appears in a pull request. From here, call the
new module ``mymod``. The following explains how to add hooks.

Python Hooks
^^^^^^^^^^^^^

Python API documentation is generated for the entries in ``docs/api.rst``.
`sphinx-autosummary <https://www.sphinx-doc.org/en/master/usage/extensions/autosummary.html>`_
is used to generate documentation for the modules.
Mention your module ``mymod`` under appropriate header.
This will discover all of the docstrings in ``mymod`` and create the
appropriate webpage.


Building the Website
---------------------

Building the website/documentation requires the following dependencies:

1. `Sphinx <http://sphinx-doc.org/>`_
2. `Furo Theme <https://pradyunsg.me/furo/>`_
3. `numpydoc <https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard>`_
4. `MyST Parser <https://myst-parser.readthedocs.io>`_

Note that pygwin itself needs to be installed too.

If you have cloned the git repository, you can install all of the doc-related
dependencies by running:

.. code-block:: bash

    pip install -e '.[doc]'

Procedure for modifying the website
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The pygwin website source files are located in the ``docs`` directory.
A developer first makes necessary changes, then rebuilds the website locally
by executing the command:

.. code-block:: bash

    cd docs/
    make html

This will generate html files for the website in the ``_build/html/`` folder.

You can watch for changes and automatically rebuild the documentation with the following command:

.. code-block:: bash

    make serve

The developer may view the local changes by opening these files with their
favorite browser, e.g.:

.. code-block:: bash

    firefox _build/html/index.html

This Sphinx documentation tree is not built or served by anything in this
repository; pygwin's real GitHub Pages site is the separate, plain
``docs/index.html`` (see AGENTS.md). Building it locally as above is useful as
a reference while writing docs, even though nothing publishes the result.


Branches and Releases
----------------------

Mainline pygwin development occurs on the ``main`` branch. Other branches
may be used for feature development (topical branches) or to represent
past and upcoming releases.

Maintenance Tasks
^^^^^^^^^^^^^^^^^^

You can cleanup your local repository of transient files such as \*.pyc files
created by unit testing by running:

.. code-block:: bash

    rm -f pygwin/parser_table.py pygwin/completion_parser_table.py
    rm -f pygwin/*.pyc tests/*.pyc
    rm -fr build

Performing the Release
^^^^^^^^^^^^^^^^^^^^^^^

pygwin has no automated release pipeline; releases are cut manually. Tagging a
release runs ``.github/workflows/cd.yml``, which builds a Nuitka-compiled
``pygwin.exe`` for Windows and attaches it to the GitHub release. See
SYNCING.md for what upstream's release automation looked like and why it
doesn't apply here.

Cross-platform testing
^^^^^^^^^^^^^^^^^^^^^^^

Most of the time, an actual VM machine is needed to test the nuances of cross platform testing.
But alas here are some other ways to test things

1. Windows

   - `wine <https://www.winehq.org/>`_ can be used to emulate the development environment. It provides cmd.exe with its default installation.

2. macOS

   - `darlinghq <https://www.darlinghq.org/>`_ can be used to emulate the development environment for Linux users.
     Windows users can use Linux inside a virtual machine or WSL to run the same.
   - `OSX KVM <https://github.com/kholia/OSX-KVM>`_ can be used for virtualization.

3. Linux

   - It far easier to test things for Linux. `docker <https://www.docker.com/>`_ is available on all three platforms.

One can leverage the Github Actions to provide a reverse shell to test things out.
Solutions like `actions-tmate <https://mxschmitt.github.io/action-tmate/>`_ are available,
but they should not in any way violate the Github Action policies.



Testing pygwin on Different Operating Systems
---------------------------------------------

pygwin dropped upstream xonsh's Nix (flake), conda, and Docker-in-Docker demo
infrastructure as not applicable to a Windows-first, Nuitka-distributed
personal shell; see SYNCING.md for the full list of what was removed and why.
There is no Nix package, no cachix binary cache, and no ``pygwin-in-docker.py``
helper script for this fork.

Container
^^^^^^^^^

It is often useful to try pygwin in a clean environment on a distribution
other than your own — for example to reproduce a bug report or to
validate a change against a pristine setup. The recipe below uses a
rootless ``podman`` container; ``docker`` would work just as well if you
prefer it.

Arch Linux Container
""""""""""""""""""""

.. code-block:: bash

    podman run --rm -it archlinux/archlinux
    pacman -Syu git python-pip
    pacman -Syu man-db man-pages bash-completion
    git clone https://github.com/dayanez/pygwin.git
    cd pygwin
    pip install --break-system-packages '.[dev]' '.[test]' '.[doc]'
    python -m pytest


Document History
-----------------

Portions of this page have been forked from the PyNE documentation,
Copyright 2011-2015, the PyNE Development Team. All rights reserved.

Chronicle
-----------------

.. toctree::
    :titlesonly:
    :maxdepth: 1
    :hidden:

    changelog
    talks_and_articles
    faq
