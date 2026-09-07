"""Pre-build pygwin's parser tables.

parser_table.py and completion_parser_table.py are gitignored build
artifacts: PLY generates them the first time something actually parses
pygwin code, and reuses the cached file on every run after that. Without
this script, that first parse eats a one-time ~1.8 second LALR
table-generation hang, silently, on whatever command a fresh install's
first user happens to type.

Run this once after `pip install -e .` (or any fresh clone) to avoid that:

    python scripts/build_parser_tables.py

The CD release workflow (.github/workflows/cd.yml) runs this before the
Nuitka build so it ships pre-built inside the compiled exe too.
"""

import os

from pygwin.parser import Parser
from pygwin.parsers.completion_context import CompletionContextParser


def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    outputdir = os.path.join(root, "pygwin")
    print("Building parser tables...")
    Parser(yacc_table="parser_table", outputdir=outputdir, yacc_debug=False)
    CompletionContextParser(
        yacc_table="completion_parser_table", outputdir=outputdir, debug=False
    )
    print(f"Wrote {outputdir}\\parser_table.py and completion_parser_table.py")


if __name__ == "__main__":
    main()
