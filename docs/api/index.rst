.. _api:

=================
Pygwin API
=================

The ``pygwin.api`` package is a set of public libraries that can be used
in third-party projects as well as in pygwin extensions (xontribs).  If
you are writing a xontrib, using ``pygwin.api`` is the recommended way to
interact with pygwin internals.

.. warning::

    The API is under development and currently has a small number
    of methods.  Contributions are welcome!

For the full internal library reference, see :doc:`/lib/index`.


``pygwin.api.subprocess``
========================

Drop-in replacements for :mod:`subprocess` functions that use pygwin's
subprocess pipeline under the hood.

.. autofunction:: pygwin.api.subprocess.run

.. autofunction:: pygwin.api.subprocess.check_call

.. autofunction:: pygwin.api.subprocess.check_output


``pygwin.api.os``
================

Pygwin-powered utilities inspired by the :mod:`os` module.

.. autofunction:: pygwin.api.os.rmtree

.. autodata:: pygwin.api.os.indir
