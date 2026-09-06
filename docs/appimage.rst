AppImage
========

`AppImage <https://appimage.org/>`_ is a format for distributing portable software on Linux without needing superuser permissions to install the application. It tries also to allow Linux distribution-agnostic binary software deployment for application developers, also called Upstream packaging.

In short the AppImage is one executable file which contains both pygwin and Python. AppImage allows pygwin to be run on any AppImage supported Linux distribution without installation or root access.

Get AppImage from Github
------------------------
You can get the pygwin AppImage from GitHub and run it on your Linux machine without installing it:

.. code-block:: bash

    wget https://github.com/xonsh/xonsh/releases/latest/download/xonsh-x86_64.AppImage -O pygwin
    chmod +x pygwin
    ./pygwin

If you don't have Python on your host, you may want to get it from AppImage:

.. code-block:: python

    ./pygwin
    $PATH = [f'{$APPDIR}/usr/bin'] + $PATH
    python -m pip install tqdm --user  # the package will be installed to ~/.local/
    import tqdm

Extracting and running from a directory
---------------------------------------

An AppImage can be extracted to a regular directory.  This is useful when
FUSE is not available (Docker containers, WSL1, older kernels) or when you
want to install pip packages directly into the extracted directory:

.. code-block:: bash

    ./pygwin-x86_64.AppImage --appimage-extract   # creates squashfs-root/
    squashfs-root/AppRun                          # run pygwin from the extracted dir

The extracted ``squashfs-root/`` directory is fully self-contained.  You can
rename or move it anywhere:

.. code-block:: bash

    mv squashfs-root ~/.local/pygwin-app
    ~/.local/pygwin-app/AppRun

To use the bundled Python directly (e.g. to install packages or run scripts):

.. code-block:: bash

    export APPDIR=~/.local/pygwin-app
    $APPDIR/usr/bin/python3 -m pip install tqdm --user
    $APPDIR/usr/bin/python3 my_script.py

Or from inside the extracted pygwin session:

.. code-block:: pygwincon

    @ ~/.local/pygwin-app/AppRun
    @ $PATH = [f'{$APPDIR}/usr/bin'] + $PATH
    @ python --version   # bundled Python
    @ xpip install rich  # install into ~/.local/


Building your own pygwin AppImage
--------------------------------

The best way to build pygwin AppImage in 5 minutes is to using `python-appimage <https://github.com/niess/python-appimage>`_:

.. code-block:: bash

    mkdir -p /tmp/build && cd /tmp/build
    git clone --depth 1 https://github.com/xonsh/xonsh
    cd pygwin/appimage
    echo 'pygwin' > requirements.txt
    cat pre-requirements.txt >> requirements.txt  # here you can add your additional PyPi packages to pack them into AppImage
    cd ..
    pip install git+https://github.com/niess/python-appimage
    python -m python_appimage build app ./appimage
    ./pygwin-x86_64.AppImage

Links
-----

 * `How to run pygwin AppImage on Alpine? <https://github.com/xonsh/xonsh/discussions/4158>`_
