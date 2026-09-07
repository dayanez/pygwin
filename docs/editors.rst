
==============
Editor and IDE
==============

Sublime Text
============
There is an `xonsh package`_ for **Sublime Text 4** (build > 4075), which also
works for editing pygwin's `.xsh` scripts since they share the same underlying
syntax. To install:

- Via **Package Control**: open (``^``/``⌘`` ``⇧`` ``P``) ``Command Palette`` → ``Package Control: Install Package`` → ``xonsh``
- **Manually**: clone the repository to your `Sublime Text packages`_ directory

  .. code-block:: sh

    cd /path/to/sublime/packages/directory
    git clone https://github.com/eugenesvk/sublime-xonsh.git

.. _xonsh package: https://packagecontrol.io/packages/xonsh
.. _Sublime Text packages: https://www.sublimetext.com/docs/packages.html


Visual Studio Code (VS Code)
============================
There is an `xonsh extension for VS Code`_, which also highlights pygwin's `.xsh`
scripts. To install search "xonsh" using the extensions menu or just press ``F1``
and run without `>` preceding:

.. code-block::

    ext install jnoortheen.xonsh

.. https://github.com/microsoft/vscode/issues/200374

Since version 1.86 of VS Code, the editor also supports loading the environment for users with pygwin as their default shell.

.. _xonsh extension for VS Code: https://marketplace.visualstudio.com/items?itemName=jnoortheen.xonsh


JetBrains: IntelliJ IDEA, PyCharm
========================================
There is an `xonsh-jetbrains <https://github.com/nahoj/xonsh-jetbrains>`_ plugin for JetBrains products, which also works for pygwin's `.xsh` scripts.

Emacs
=====

Emacs xonsh-mode
----------------

There is an emacs mode (`xonsh-mode`) for editing pygwin scripts available from the
`MELPA repository`_. If you are not familiar see the installation
instructions there.

Then just add this line to your emacs configuration file:

.. code-block:: emacs-lisp

    (require 'xonsh-mode)


.. _MELPA repository: https://melpa.org/#/xonsh-mode


Pygwin Comint buffer
-------------------

You can use pygwin as your `interactive shell in Emacs
<https://www.gnu.org/software/emacs/manual/html_node/emacs/Interactive-Shell.html>`_
in a Comint buffer. This way you keep all the Emacs editing power
in the shell, but you lose pygwin's completion feature.

Make sure you install pygwin with readline support and in your
:doc:`pygwin RC <pygwinrc>` define

.. code-block:: pygwin

    $SHELL_TYPE = 'readline'

Also, in Emacs set ``explicit-shell-file-name`` to your pygwin executable.

Pygwin Ansi-term buffer
----------------------

The second option is to run pygwin in an Ansi-term buffer inside
Emacs. This way you have to switch modes if you want do Emacs-style
editing, but you keep pygwin's impressive completion.

For this it is preferred to have pygwin installed with the
prompt-toolkit. Then you can leave ``$SHELL_TYPE`` at its default.

Emacs will prompt you for the path of the pygwin executable when you
start up ``ansi-term``.

Vim
===

There is an `xonsh syntax file for vim`_, which also works for pygwin's `.xsh`
scripts. To install run:

.. code-block::

    git clone --depth 1 https://github.com/linkinpark342/xonsh-vim ~/.vim

.. _xonsh syntax file for vim: https://github.com/linkinpark342/xonsh-vim


Formatting pygwin code
=====================

Pygwin ships a built-in code formatter accessible as the ``pygwin format``
subcommand. It can be wired into any editor that lets you pipe the
current buffer through an external command — point the editor at
``pygwin format -`` to read the buffer from stdin and replace it with
the formatted output.

See :ref:`formatting_pygwin_code` for the full set of invocations and
flags.
