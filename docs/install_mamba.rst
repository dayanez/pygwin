:orphan:

*******************
Mamba Install Pygwin
*******************

Pygwin is a Python-based shell, and running pygwin requires Python to be installed.
The Python version and its packages can be installed in various locations. When
you execute ``import`` or any other Python code during a pygwin session, it is
executed in the Python environment that was used to start the current pygwin
instance.

When pygwin is used as a core shell, it is necessary to keep the Python environment
with pygwin stable, predictable, and independent of system changes. Lightweight
environment managers such as ``venv``, ``pipx``, or ``rye`` do not fully address
this requirement. Package managers that can install fully isolated Python
environments as a core feature, such as ``miniconda`` or ``micromamba``, should
be used.

The ``mamba-install-pygwin.sh`` script creates an independent Python environment
for pygwin using `mamba <https://mamba.readthedocs.io/>`_ in ``$TARGET_DIR`` without
affecting any other components of the system. This is an isolated,
pygwin-specific environment that is not affected by system package upgrades,
Python version changes, or other experiments with environments. You can use
``xpip`` and ``xmamba`` to intentionally install packages into this environment.

Install the latest pygwin release with a well-tested Python version:

.. code-block:: console

   $ TARGET_DIR=$HOME/.local/pygwin-env PYTHON_VER=3.11 PYGWIN_VER='pygwin[full]' \
     /bin/bash -c "$(curl -fsSL https://xon.sh/install/mamba-install-xonsh.sh)"

Install pygwin from the ``main`` Git branch with a stable Python version

.. code-block:: console

   $ TARGET_DIR=$HOME/.local/pygwin-env PYTHON_VER=3.11 PYGWIN_VER='pygwin[full] @ git+https://github.com/xonsh/xonsh@main' \
     /bin/bash -c "$(curl -fsSL https://xon.sh/install/mamba-install-xonsh.sh)"


Preinstall and preload `xontribs <https://github.com/topics/xontrib>`_:

.. code-block:: console

   $ TARGET_DIR=$HOME/.local/pygwin-env PYTHON_VER=3.11 PYGWIN_VER='pygwin[full] @ git+https://github.com/xonsh/xonsh@main' \
     PIP_INSTALL="uv xontrib-sh xontrib-jump-to-dir xontrib-dalias xontrib-pipeliner xontrib-whole-word-jumping" \
     PYGWINRC="\$PYGWIN_HISTORY_BACKEND = 'sqlite'; xontrib load -s sh jump_to_dir pipeliner whole_word_jumping dalias; \$PROMPT = \$PROMPT.replace('{prompt_end}', '\n{prompt_end}')" \
     /bin/bash -c "$(curl -fsSL https://xon.sh/install/mamba-install-xonsh.sh)"

Usage
=====

After installation, you no longer need to worry about Python or package
manipulations unintentionally breaking the shell. You can safely use ``pip``,
``brew``, and other package managers without corrupting the pygwin environment.

After installation:

* ``pygwin`` refers to ``~/.local/pygwin-env/xbin/pygwin``.
* ``xpython`` refers to ``~/.local/pygwin-env/bin/python``.
* ``xpip`` refers to ``~/.local/pygwin-env/bin/python -m pip``.
* ``xcontext`` shows the current context.
* You can run ``source xmamba.xsh`` to activate mamba (see below).

Additions:

* ``xbin-pygwin`` runs pygwin from pygwin-env if ``pygwin`` is overridden in ``$PATH``.
* ``xbin-python`` runs Python from pygwin-env.
* Executable helpers from pygwin-env:

  * ``xbin-hidden`` lists the internal hidden ``bin`` directory of pygwin-env.
    Example: ``xpip install lolcat && xbin-hidden``.
  * ``xbin-add`` adds an executable from the hidden ``bin`` directory to the
    visible ``xbin``. Example: ``xbin-add lolcat``.
  * ``xbin-list`` lists executables in the visible ``xbin`` directory.
  * ``xbin-del`` removes an executable from ``xbin``. The executable remains in
    ``bin``.

Tips and Tricks
===============

Using mamba from pygwin-env
--------------------------

To bind the pygwin-env micromamba to the ``xmamba`` alias, run:

.. code-block:: pygwincon

   @ source xmamba.xsh

You can then use:

.. code-block:: pygwincon

   @ xmamba activate base  # Environment where pygwin was installed.
   @ pip install lolcat    # Install ``lolcat`` into the ``base`` environment.
   @ xmamba deactivate

   @ xmamba create --name myenv python=3.12
   @ xmamba activate myenv
   @ pip install lolcat    # Install ``lolcat`` into ``myenv``.
   @ xmamba deactivate

Cleaning
--------

If you do not plan to use ``xmamba``, you can reclaim disk space using
`mamba clean <https://fig.io/manual/mamba/clean>`_:

.. code-block:: pygwincon

   @ source xmamba.xsh
   @ xmamba clean -a

Uninstall
=========

Simply delete ``$TARGET_DIR``. For example:

.. code-block:: pygwincon

   @ rm -rf ~/.local/pygwin-env/

Known Issues
============

Do not blindly use as a login shell
----------------------------------

Using pygwin as a `login shell <https://linuxhandbook.com/login-shell/>`_ is not
recommended unless you are experienced and understand the implications. Many
tools expect the login shell to be POSIX-compliant, and issues may arise when
such tools attempt to run POSIX-specific commands in pygwin.

``std::bad_alloc``
------------------

If you encounter the error::

   terminate called after throwing an instance of 'std::bad_alloc'

delete the target directory (for example, ``rm -rf ~/.local/pygwin-env/``) and
repeat the installation.
