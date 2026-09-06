"""Token-stream based formatter for pygwin source code.

The formatter walks the raw token stream produced by
:mod:`pygwin.parsers.tokenize` (which preserves comments, blank lines and
all pygwin-specific tokens such as ``$(``, ``!(``, ``${``, ``@$``, IO
redirects and globs) and re-emits the source with normalized whitespace
and indentation.

The public API is intentionally small:

- :func:`format_source` — format a string of pygwin source.
- :class:`FormatError` — raised on unrecoverable tokenizer errors.

The CLI entry point used by ``pygwin format ...`` lives in
:mod:`pygwin.formatter.cli`.
"""

from pygwin.formatter.core import DEFAULT_INDENT, FormatError, format_source

__all__ = ["DEFAULT_INDENT", "FormatError", "format_source"]
