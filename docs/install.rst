************************
Pygwin Installation Guide
************************

Before Installing
========================

Pygwin is a full-featured shell and can technically be used as a login shell,
but since it is not a POSIX‑compatible shell, we don't recommend doing
so unless you clearly understand the purpose and consequences.
Do not attempt to set it as your default shell using ``chsh``
or by any other method that would replace the system shell.

The recommended practice is to create a Pygwin profile in your terminal emulator.


Overview
========================

Pygwin targets Windows first, on Python 3.11 or newer. It also runs anywhere
its underlying engine does, since it is a fork of `xonsh <https://xon.sh/>`_,
but Windows is the platform this fork is tuned and tested for. There are two
ways to run it today:

.. raw:: html

    <table class="docutils align-default">
      <thead>
        <tr>
          <th></th>
          <th class="head"><p>Requires Python</p></th>
          <th class="head"><p>Automation</p></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th class="stub"><p>From source</p></th>
          <td align="center">🟢</td>
          <td align="center">🟢</td>
        </tr>
        <tr>
          <th class="stub"><p>Standalone executable</p></th>
          <td align="center"></td>
          <td align="center"></td>
        </tr>
      </tbody>
    </table>

From source
========================

.. code-block:: console

    $ git clone https://github.com/dayanez/pygwin.git
    $ cd pygwin
    $ pip install -e ".[full]"
    $ python scripts/build_parser_tables.py

That last line is optional but recommended: pygwin's parser tables are generated on
first use and cached from then on, but generating them from scratch takes about 1.8
seconds. Skipping this step just means whatever command you type first pays that
cost once, silently, instead of paying it here with an explanation.

The ``[full]`` extra pulls in the interactive line editor (``prompt_toolkit``) and
syntax highlighting (``pygments``). Pygwin still defaults to its own fast
``readline`` backend even with ``[full]`` installed; add ``$SHELL_TYPE =
'prompt_toolkit'`` (or ``'best'``) to your ``~/.pygwinrc`` to actually use the
richer editor once it's installed. On Windows, plain ``pip install pygwin`` (no
extras) also pulls in `pyreadline3 <https://pypi.org/project/pyreadline3/>`_,
since Windows ships no ``readline`` module of its own and the default backend
needs a real one to be worth using.

Pygwin is not currently published to PyPI, conda, mamba, WinGet, Flatpak, an
AppImage, or any container registry. Installing from source, above, is the only
supported way to get a development environment.

Standalone executable
========================

Every release publishes a Nuitka-compiled ``pygwin.exe`` for Windows under this
repository's `Releases <https://github.com/dayanez/pygwin/releases>`_ page.
Download it, run it, no Python installation required.

Updating pygwin
========================

**Installed from source**: pull the latest changes and reinstall:

.. code-block:: console

    $ git pull
    $ pip install -e ".[full]"

**Installed as the standalone executable**: download the latest ``pygwin.exe``
from the `Releases <https://github.com/dayanez/pygwin/releases>`_ page and
replace the old one. On Windows, the running ``pygwin.exe`` is locked by the
OS, so close the shell before overwriting it.


.. _default_shell:

Setting pygwin as the default shell
========================================

Setting pygwin as your default login shell is **not recommended**.
Pygwin is a full-featured shell and can technically be used as a login
shell, but since it is not POSIX-compatible, system scripts and tooling
that expect a POSIX shell may misbehave. Use it only if you clearly
understand the purpose and consequences — see the rationale in
`Before Installing`_ above. The recommended practice is to create a
pygwin profile in your terminal emulator instead.

If you still want to use pygwin as your default shell, you will have
to add pygwin to ``/etc/shells`` and switch:

.. code-block:: console

    $ which pygwin
    # which pygwin >> /etc/shells
    $ chsh -s $(which pygwin)

You will have to log out and log back in before the changes take effect.
