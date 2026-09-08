# Cutting a release

1. Bump `__version__` in `pygwin/__init__.py`.
2. Add a `## vX.Y.Z` section at the top of `CHANGELOG.md` (above the previous
   version's section) describing what changed.
3. Commit both files:
   ```
   git add pygwin/__init__.py CHANGELOG.md
   git commit -m "Cut vX.Y.Z: <one-line summary>"
   ```
4. Create an annotated tag with the same summary:
   ```
   git tag -a vX.Y.Z -m "vX.Y.Z: <one-line summary>"
   ```
5. Push the commit, then the tag:
   ```
   git push origin main
   git push origin vX.Y.Z
   ```

Pushing the tag is what matters: `.github/workflows/cd.yml` triggers on any
pushed tag matching `v*`, builds `pygwin.exe` with Nuitka, and — only when the
tag also matches `refs/tags/v*` (i.e. every normal release tag) — publishes a
GitHub Release with the exe attached and auto-generated release notes.

Steps 1-4 are all local and safe to redo; nothing public happens until the
`git push origin vX.Y.Z` in step 5.

# Running from source (no build needed)

For testing changes, you don't need to build an exe at all — the exe is only for
distributing to people without Python installed. After `pip install -e ".[full]"`
(needed once regardless), any of these run the real thing from the repo root:

```
python -m pygwin
python pygwin/__main__.py
pygwin
```

The third works because the editable install registers `pygwin` as a console-script
entry point on your PATH (`pyproject.toml`'s `[project.scripts]`); all three call the
same `pygwin.main:main()`.

Expect the very first run, or the first run after a change that touches the parser,
to hang for about 1.8s while it generates the LALR parser tables from scratch — the
same cost `scripts/build_parser_tables.py` pre-bakes for the compiled exe. It's
harmless here; the tables get cached and later runs are fast.

# Building pygwin.exe locally

Pushing the tag makes GitHub Actions build the release exe for you, so this is only
needed to test a compile before tagging, or to get an exe without cutting a release
at all.

```
pip install -e ".[full]"
pip install nuitka zstandard
python scripts/build_parser_tables.py
python -m nuitka --standalone --onefile --onefile-cache-mode=cached --output-filename=pygwin.exe --enable-plugin=no-qt --no-deployment-flag=self-execution --company-name=pygwin --product-name=pygwin --windows-icon-from-ico=docs/_static/pygwin.ico --include-module=pygwin.parser_table --include-module=pygwin.completion_parser_table --include-package=pgtrib --include-package=pgcompletions pygwin/__main__.py
```

Add `--jobs=N` (or a negative number, meaning "all cores minus N") to cap CPU use;
the default uses every core and can make the machine sluggish for several minutes.

Every flag here matters — see "Building the standalone executable" in README.md for
what each one does and what breaks if it's dropped (missing parser tables, missing
pgtrib/pgcompletions loading, no cache reuse between runs, etc).
