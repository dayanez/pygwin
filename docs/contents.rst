#########################
The Pygwin Shell
#########################

.. include:: intro.rst

.. include:: comparison.rst

.. include:: installation.rst


Docs
====

Beginner
--------

The fundamentals of using Pygwin, including basic commands, syntax,
and how subprocesses work in practice. This section introduces key concepts
step by step and helps you build a solid foundation for working in the shell.

.. toctree::
    :titlesonly:
    :maxdepth: 1

    tutorial
    strings
    subprocess
    python
    error_handling
    Extensions on Github <https://github.com/topics/xontrib>

Regular User
-------------

How to use Pygwin efficiently in daily workflows by configuring
environment variables, aliases, and history. It also covers customization
options, keyboard shortcuts, and practical tips to improve productivity
and streamline your command-line experience.

.. toctree::
    :titlesonly:
    :maxdepth: 1

    pygwinrc
    envvars
    aliases
    history
    keyboard_shortcuts
    prompt
    events
    globbing
    macros
    pygwin_session
    launch
    platforms

Creator
-------

How to extend Pygwin by building projects, creating extensions,
and customizing tab-completion. This section also explores deeper integrations,
event handling, and advanced customization techniques for building powerful
developer tools.

.. toctree::
    :titlesonly:
    :maxdepth: 1

    editors
    python_virtual_environments
    pygwin_projects
    callable_aliases
    events_tutorial
    env
    completers
    xontrib
    embedding
    debug
    api/index
    Create an extension <https://github.com/xonsh/xontrib-template>

Contributor
-----------

The internal architecture of Pygwin and how to work with its API.
It also guides you through contributing to the project, understanding the codebase,
and collaborating with others.

.. toctree::
    :titlesonly:
    :maxdepth: 1
    :hidden:

    developer
    lib/index
    history_backend

* `Developer’s Guide <developer.html>`_
* `Pygwin Library Reference <lib/index.html>`_
* `History Backend <history_backend.html>`_

Pygwin is a personal daily-driver project built and maintained by one person,
not a community project: see AGENTS.md in the repository root for how it
handles contributions (it doesn't accept pull requests or issues).


Links
=====

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
