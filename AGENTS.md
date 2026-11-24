# AGENTS.md

Guidance for AI agents working in this repository.

## What this repo is

This is the **md-gost** toolchain: Markdown sources become a GOST-styled
Microsoft Word `.docx` via Pandoc. The repository holds the command, the
builder, the linter, the postlinter, the IDEF0 library, editor extensions, and
one demonstration document.

- **Document language:** Russian. Prose, captions, and labels in a document are Russian.
- **Source format:** Pandoc-flavored Markdown.
- **Output:** one `.docx` per directory that contains a `book.toml` (Times New Roman
  14pt, 1.5 line spacing, margins 30/10/20/20mm, bordered tables).

A human-facing overview lives in `README.md` (Russian). Install steps for
Pandoc, PlantUML and Graphviz live in `INSTALL.md`. Contributor checks live in
`CONTRIBUTING.md`. This file covers what an agent needs on top of them.

## Repository layout

```
.
├── README.md                  # repository overview (Russian, for humans)
├── INSTALL.md                 # Pandoc, PlantUML, Graphviz
├── CONTRIBUTING.md            # human contributor checks (Russian)
├── CLAUDE.md                  # one line: loads this file
├── AGENTS.md
├── example/                   # demonstration document (book.toml + example.docx)
├── .claude/skills/gost-doc/   # prose rules for writing chapters
├── editors/                   # Zed and VS Code / Cursor extensions
└── packages/
    ├── md-gost/               # the only command: imports the other packages
    ├── md-gost-build/         # gost_builder (see its README.md)
    ├── md-gost-lint/          # gost_lint
    ├── md-gost-postlint/      # gost_docx_lint
    └── idef0/
```

Every directory holding a `book.toml` is an independently buildable document.
In this repository that directory is `example/`. Files not listed in `chapters`
are ignored by the build.

## Building

Pass the directory that contains the manifest:

```bash
md-gost build example/
```

One command does everything: lints the sources, renders PlantUML diagrams to PNG,
generates the GOST `reference.docx`, runs Pandoc with the Lua filter, post-processes
the `.docx`, and verifies ZIP integrity. Any error — including an undefined
cross-reference or a lint error — aborts the build with a non-zero exit.
`md-gost build --no-lint` skips the lint step; use it only to check a build in isolation.

Intermediate artifacts land in that document's `.md-to-gost/` (gitignored). The
build is idempotent; `reference.docx` is regenerated every run, so stale styles
cannot accumulate.

### Toolchain (must be available on PATH)

- **Pandoc** 3.9.x
- **PlantUML** — a `plantuml` command, or `plantuml.jar` on PATH / `PLANTUML_JAR` (needs Java)
- **Graphviz** (`dot`) for diagrams PlantUML does not lay out itself
- **python3** ≥ 3.11 (needs `tomllib`)

Install steps for macOS and Windows (Homebrew, winget, Chocolatey, the
PlantUML jar, `pypandoc.download_pandoc()`) live in the root `INSTALL.md`.
On Windows `shutil.which("plantuml")` only searches `PATHEXT`,
so a lone `plantuml.jar` is invisible to it. The build scans PATH for that
filename and runs `java -jar`. A `.bat` / `.cmd` wrapper is used only when
`plantuml.jar` sits next to it, because Pandoc cannot execute the wrapper.

Install the command from the repository root with `uv tool install .`, or into
an existing virtual environment with `uv pip install .`. That install registers
one script, `md-gost`, plus the packages that script imports. Install Pandoc and
PlantUML separately. Use `uv tool install '.[plots]'` for plot support.

`md-gost` does not reimplement the packages. It calls them:

- `lint`, `format`, `lsp` — `gost_lint` in `packages/md-gost-lint/`
- `build` — `gost_builder.pipeline.build` in `packages/md-gost-build/`
- `postlint` — `gost_docx_lint.check` in `packages/md-gost-postlint/`

The builder still runs the linter and the postlinter as separate processes
(`md_lint.py`, `gost_docx_lint/post_lint.py`). Those runners stay on the
standard library. Typer lives only in `packages/md-gost/`.

`packages/md-gost/`, `packages/md-gost-lint/`, `packages/md-gost-build/` and `packages/idef0/`
each have their own `pyproject.toml`. Dependencies, ruff, pyrefly and pytest
settings live there, not in a repository-wide config. `packages/md-gost-postlint/`
has no manifest of its own; the root `pyproject.toml` maps it to `gost_docx_lint`.
Edit the manifest of the tool you are touching.

Every Python code change must pass Ruff, Pyrefly, and wemake-python-styleguide
(WPS) before it is considered finished. Ruff and WPS run through the root
`.pre-commit-config.yaml`; run `pre-commit run --files <changed-python-files>`
(or `pre-commit run --all-files`) to check them. Ruff is pinned at v0.16.8 and
the hooks run `ruff-check --fix` followed by `ruff-format`. Pyrefly is not part
of pre-commit: run `uvx pyrefly check` from the changed tool's directory
(`packages/md-gost/`, `packages/md-gost-lint/` or `packages/md-gost-build/`). WPS config
is that tool's `setup.cfg`; use it. Formatting width is the `line-length` in
its `pyproject.toml` (100). A tool that already has a `[tool.pyrefly]` block is
held to the `strict` preset with zero findings, so a missing annotation is a
regression rather than a backlog item.

Python under `example/` is document fixture code (listings and plots). Root
`ruff.toml` excludes that directory. Do not treat those files as tool source.

### The `book.toml` manifest

Chapter order lives in the document's `book.toml`, **not** in the directory structure.
Only files listed in `chapters` are built; any other `.md` is ignored. A new chapter
file must be added to that list or it silently will not appear.

- `chapters` — required, ordered list of `.md` files.
- `output` — output file name, default `output.docx`.
- `toc` — default `true`. A one-chapter document often sets `toc = false`.
  `example/` leaves the default on.
- `page_break_before_h1` — default `true`: every level-1 heading starts on a new
  page. Set it to `false` when sections themselves sit at level 1, or each of
  them would start on a page of its own.
- `number_sections` — default `false`. With it on, the build numbers the headings
  and the source carries no numbers at all; `{-}` marks a section that stays
  unnumbered, and a hand-typed number aborts the build.
- `[frame]` — presence of this table enables the GOST frame. `example/` uses it.

To add a document: create the directory, write the Markdown, add a `book.toml`
with `chapters` and `output`, then build. `example/` is the reference for markup.

## Authoring conventions

Two sources, split by who enforces the rule:

- **Markup syntax** — diagrams, table markers, cross-references, bibliography,
  raster images, GOST frame, Word styles: `packages/md-gost-build/README.md`. This is the
  contract the build enforces; violating it aborts the build with a non-zero exit.
- **Prose rules** — section structure, no bold in body text, how to phrase a
  cross-reference, where a `[@bib:…]` goes: the `gost-doc` skill
  (`.claude/skills/gost-doc/SKILL.md`). The build does not check any of it, so a
  document that builds cleanly can still be wrong. Load the skill before writing or
  editing any `.md` listed in a `book.toml`.

Do not restate either set of rules here — a third copy is what this split removed.

`packages/md-gost-lint/` checks the mechanical part of both sets and runs as the first step
of every build. Run it directly while editing — it is instant and needs no venv:

```bash
md-gost lint example/          # a document directory, or a single .md
md-gost format example/
```

Errors block the build, warnings do not. The rule list is
`md-gost lint --list-rules`.

Severity lives in `mdlint.toml`, and those cascade: the root one sets the baseline,
a document's own — next to its `book.toml` — overrides it for that directory only.
A rule that is wrong for a given document is turned off in that document's config,
not in the root one and not worked around in the text. `example/` turns the prose
rules off because it demonstrates markup, not exposition; see the root `mdlint.toml`.

## Editing the pipeline

The builder package lives in `packages/md-gost-build/gost_builder/`.

- `pipeline.py` runs the build stages in order. `render.py` invokes Pandoc.
- `filters/plantuml.lua` transforms the Markdown AST, resolves references and
  numbers diagrams, captions and bibliography entries.
- `reference/` defines the Word template. `postprocess/` applies formatting
  to the generated document, including table layout in `postprocess/tables/`.
- `frame/` owns the optional GOST frame, its settings and XML templates.

The tool is generic. When changing the pipeline, build `example/` and run the
package tests. `example/` is the fixture the golden test compares.

Tests run from the tool's own directory:

```bash
cd packages/md-gost       && uv run --group dev pytest
cd packages/md-gost-build && uv run --group dev --extra plots pytest  # golden + features
cd packages/md-gost-lint  && uv run --group dev pytest  # rules, CLI, config cascade, parser
```

Rule changes belong in `packages/md-gost-lint/gost_lint/rules/` plus a fixture in
`packages/md-gost-lint/tests/fixtures/`; the expected rule set in `test_rules.py` is exact,
so a new rule that fires on an old fixture must be reviewed, not silenced.

## Verifying changes

After a build, confirm:

- `md-gost lint example/` is clean, or every remaining warning is a conscious decision.
- The build of `example/` exits 0.
- Captions render as `Рисунок N` / `Таблица N` in sequential order.
- Prose citations resolve to bare numbers.

## Git

- `example/example.docx` is the committed sample of the demonstration document.
  Rebuild it when its sources change.
- Build caches (`.md-to-gost/`, `.venv/`) are gitignored; do not force-add them.
- Only commit when the user requests it.
