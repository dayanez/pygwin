"""Static lint rules for pygwin source code.

Where :mod:`pygwin.checker` answers "does it parse?" and :mod:`pygwin.formatter`
answers "is it formatted?", :mod:`pygwin.linter` answers "is it likely *wrong*?"
— without executing the code. It runs a small set of rules over the transformed
pygwin AST, drawing on pygwin's own registries (the environment-variable table in
:mod:`pygwin.environ`) for checks no generic linter could make.

Public API:

- :func:`lint_source` — lint a string of pygwin source, returning ``Finding``\\ s.
- :class:`Finding` — one diagnostic (line, col, code, message).

The CLI entry point used by ``pygwin lint ...`` lives in :mod:`pygwin.linter.cli`.
"""

from pygwin.linter.cli import lint_source
from pygwin.linter.rules import Finding

__all__ = ["lint_source", "Finding"]
