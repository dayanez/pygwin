************************
Pygwin Installation Guide
************************

The guide is new so in case of error please open the issue in the `tracker <https://github.com/xonsh/xonsh/issues>`_.

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

Pygwin is a Python-based shell that requires Python to be packaged, preinstalled or compiled in order to run.
Since there are many ways to install Python, there are also many ways to run pygwin. The table describes
the main approaches and their advantages.

.. raw:: html

    <table class="docutils align-default">
      <thead>
        <tr>
          <th></th>
          <th class="head"><p>Use as <br>core shell</p></th>
          <th class="head"><p>Isolated env</p></th>
          <th class="head"><p>Fresh version</p></th>
          <th class="head"><p>Automation</p></th>
          <th class="head"><p>Portable</p></th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th class="stub"><p>Independent install</p></th>
          <td align="center">🟢</td>
          <td align="center">🟢</td>
          <td align="center">🟢</td>
          <td align="center">◯</td>
          <td align="center"></td>
        </tr>
        <tr>
          <th class="stub"><p>Package</p></th>
          <td align="center"></td>
          <td align="center"></td>
          <td align="center">🟢</td>
          <td align="center">🟢</td>
          <td align="center"></td>
        </tr>
        <tr>
          <th class="stub"><p>AppImage</p></th>
          <td align="center"></td>
          <td align="center">🟢</td>
          <td align="center">🟢</td>
          <td align="center">◯</td>
          <td align="center">🟢</td>
        </tr>
        <tr>
          <th class="stub"><p>Container</p></th>
          <td align="center"></td>
          <td align="center">🟢</td>
          <td align="center">🟢</td>
          <td align="center">🟢</td>
          <td align="center"></td>
        </tr>
        <tr>
          <th class="stub"><p>System package</p></th>
          <td align="center"></td>
          <td align="center"></td>
          <td align="center">◯</td>
          <td align="center"></td>
          <td align="center"></td>
        </tr>
      </tbody>
    </table>

Work in progress:
`binary build <https://github.com/xonsh/xonsh/issues/2895#issuecomment-3665753657>`_,
`running in RustPython <https://github.com/xonsh/xonsh/issues/5082#issue-1611837062>`_,
`pygwin Flatpak <https://github.com/xonsh/xonsh-flatpak>`_.
Check out `Nightly build <https://github.com/xonsh/xonsh/releases/tag/nightly-build>`_ page.

Independent install
========================

When pygwin is used as a core shell, it is necessary to keep the Python environment with pygwin
stable, predictable, and independent of system changes. Lightweight environment managers
such as ``venv``, ``pipx``, or ``rye`` do not fully address this requirement.
Package managers that can install fully isolated Python environments as a core feature,
such as Miniconda or Micromamba, should be used.

Linux / macOS / WSL
-------------------

Install Pygwin independently using Micromamba:

.. code-block:: console

    $ TARGET_DIR=$HOME/.local/pygwin-env PYTHON_VER=3.11 PYGWIN_VER='pygwin[full]' \
      /bin/bash -c "$(curl -fsSL https://xon.sh/install/mamba-install-xonsh.sh)"

Learn more: `Mamba installer <install_mamba.html>`_.


Windows
-------

.. note::

   The installation instructions for Windows were recently updated.
   If you run into any issues, please report them to the
   `issue tracker <https://github.com/xonsh/xonsh/issues>`_.

We provide an experimental Pygwin installer for Windows (no admin rights required). Download the ``.exe`` from the
`Pygwin WinGet releases page <https://github.com/xonsh/xonsh-winget/releases>`_:

* ``inno6`` — for Windows 10/11 (latest Python 3).
* ``inno5`` — for Windows 8.1+ (pinned to Python 3.13).

Or install via the script (no admin rights required):

.. code-block:: doscon

    > curl -L -o install_pygwin.cmd https://xon.sh/install/windows_install_xonsh.cmd
    > install_pygwin.cmd  # Install to ~/pygwin-env/

Package
========================

**pip:**

You can install the pygwin package from PyPI with any pip-compatible installer
(``pip``, ``pipx``, ``uv``, ``rye``, ``poetry``, etc.).

.. code-block:: console

    $ pip install 'pygwin[full]'

Pip can also install the most recent pygwin source code from the
`pygwin project repository <https://github.com/xonsh/xonsh>`_:

.. code-block:: console

    $ pip install 'https://github.com/xonsh/xonsh/archive/main.zip#egg=pygwin[full]'

**mamba:**

.. code-block:: console

    $ mamba install pygwin

**conda:**

.. code-block:: console

    $ conda config --add channels conda-forge
    $ conda install pygwin


AppImage
========================

Pygwin is available as a single AppImage bundled with Python, allowing you to run it on Linux without installation:

.. code-block:: console

    $ wget 'https://github.com/xonsh/xonsh/releases/latest/download/pygwin-x86_64.AppImage' -O pygwin
    $ chmod +x pygwin
    $ ./pygwin

Study how to package your libraries in `Pygwin AppImage <appimage.html>`_ article.

Container
========================

Pygwin publishes a handful of containers, primarily targeting CI and automation use cases.
All of them are published on `Docker Hub <https://hub.docker.com/u/xonsh>`__.

Example of running an interactive pygwin session in a container:

.. code-block:: console

    $ podman run --rm -it pygwin/pygwin-interactive

Learn more: `Containers <containers.html>`_.


Android / Termux
========================

On Android, install pygwin inside `Termux <https://termux.dev>`_:

.. code-block:: console

    $ pkg install python git bash-completion
    $ pip install 'pygwin[full]'
    $ pygwin

Also works inside UserLAnd, proot-distro, Linux Deploy, and similar
Android-userland sandboxes. See :doc:`Cross-platform <platforms>` for
the Android-specific section, including ``ON_ANDROID`` / ``ON_TERMUX``
flags and known sandbox limitations.


System package
========================

Various operating system distributions provide platform-specific package managers that may offer a pygwin package.
This approach is **not recommended** for the following reasons:

* On non-rolling-release operating systems, the pygwin version is often outdated.
* The package may be missing important dependencies.
* System package managers install pygwin into the system Python environment, which means that any significant system update or change has a high probability of breaking the shell.

**Arch Linux:**

.. code-block:: console

    $ pacman -S pygwin  # not recommended but possible

**Debian/Ubuntu:**

.. code-block:: console

    $ apt install pygwin  # not recommended but possible

**Fedora:**

.. code-block:: console

    $ dnf install pygwin  # not recommended but possible

**GNU guix:**

.. code-block:: console

    $ guix install pygwin  # not recommended but possible

**macOS:**

.. code-block:: console

    $ brew install pygwin  # not recommended but possible

WIP Binary build
========================

Using Nuitka (a Python compiler), it is possible to build a binary version of pygwin.
Learn more in `pygwin/2895 <https://github.com/xonsh/xonsh/issues/2895>`_.

WIP RustPython build
========================

Using RustPython (a Python Interpreter written in Rust), it is possible to run pygwin using Rust.
Learn more in `pygwin/5082 <https://github.com/xonsh/xonsh/issues/5082>`_.


Updating pygwin
========================

How you update pygwin depends on the install method.

**pygwin installed via pip**

If pygwin was installed via pip (possibly into a virtual environment), you can
update it from within pygwin itself using :ref:`xpip <aliases-xpip>` — a
predefined alias pointing to the ``pip`` command associated with the Python
executable that runs the current pygwin session:

.. code-block:: pygwincon

   @ xpip install --upgrade pygwin  # install the latest release
   @ xpip install -U --force-reinstall git+https://github.com/xonsh/xonsh  # install from the repository

**On Windows** the running ``pygwin.exe`` is locked by the OS, so pip cannot
replace it from inside pygwin itself. Grab the interpreter path with
:ref:`xcontext <aliases-xcontext>`, leave the shell, then run pip from
another terminal (``cmd``, PowerShell, etc.):

.. code-block:: pygwincon

   @ xcontext            # note the "xpython" path
   @ exit                # release the lock on pygwin.exe
   > <xpython> -m pip install --upgrade pygwin

**pygwin installed via a package manager**

If you installed pygwin via a package manager, it is recommended to update it
through the package manager's appropriate command. For example, on macOS with
homebrew:

.. code-block:: console

   $ brew upgrade pygwin


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


GitHub Actions
========================

The `pygwin/actions <https://github.com/xonsh/actions>`_ repository provides a composite
action that installs pygwin on a GitHub Actions runner, so subsequent steps can run pygwin
code natively. Tested on ``ubuntu-latest``, ``macos-latest``, and ``windows-latest``.

Declare ``defaults.run.shell: pygwin {0}`` once for the whole job and every ``run:``
block in that job executes as pygwin:

.. code-block:: yaml

    jobs:
      my-job:
        runs-on: ubuntu-latest
        defaults:
          run:
            shell: pygwin {0}
        steps:
          - uses: actions/checkout@v4
          - uses: pygwin/actions@v2

          - run: |
              echo "hello from pygwin"
              $PATH.append('/mypath')

Or set ``shell: pygwin {0}`` on individual steps when only some should run as pygwin:

.. code-block:: yaml

    jobs:
      my-job:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: pygwin/actions@v2

          - name: Run pygwin
            shell: pygwin {0}
            run: |
              echo "hello from pygwin"
              $PATH.append('/mypath')
              print($PATH)

See the `pygwin/actions README <https://github.com/xonsh/actions>`_ for inputs, outputs,
and reusable workflows for testing xontribs.
