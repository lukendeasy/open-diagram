# AGENTS.md

Instructions for coding agents working on the open-diagram library itself. To **draw a diagram with** the library,
read [`skills/open-diagram/SKILL.md`](skills/open-diagram/SKILL.md) instead.

## What this is

A pure-Python library that turns a short script into a dense architecture diagram (SVG, plus PNG through a headless
browser). Its core promise: every label is measured from the font before anything is placed, and the build reports
layout problems as plain sentences that name the parts involved, so an agent can fix them without looking at the
picture. Preserve that promise in every change.

## Commands

```bash
python3 -m unittest discover -s tests                         # all tests; they add src/ to sys.path themselves
PYTHONPATH=src python3 examples/systems_map.py                # build one example into docs/images/
for f in examples/*.py; do PYTHONPATH=src python3 "$f"; done  # rebuild every picture
pip install -e .                                               # optional: editable install instead of PYTHONPATH
python3 -m build                                               # sdist and wheel into dist/ (needs `pip install build`)
PYTHONPATH=src python3 -m open_diagram check examples/*.py examples/*.json examples/*.mmd   # the CLI, without installing
```

PNG output needs Chrome, Chromium or Edge; set `CHROME` to the binary if `find_chrome()` misses it. SVG output never
needs a browser. CI (`.github/workflows/test.yml`) runs the tests on Python 3.10 and 3.14.

## Map

| Path | Role |
| --- | --- |
| `src/open_diagram/fonts.py` | `Face` (fontTools): glyph outlines, advance widths, GPOS pair kerning. `text_width`, `cap_height`, `wrap`, `fmt` |
| `src/open_diagram/svg.py` | `Canvas`: SVG primitives; `text()` emits outline paths with a `<title>` holding the string |
| `src/open_diagram/theme.py` | `Theme` (colors, statuses, tones, type sizes, spacing, 3D `lid`/`depth`), `Status`, `shade()` |
| `src/open_diagram/blocks.py` | `Block` base and `Resource`, `Tile`, `Tiles`, `Text`, `Card`, `Note`, `Graph`, `Row`, `Panel` |
| `src/open_diagram/diagram.py` | `Diagram`: placement, `link`/`group`, routing, `_check()`, legend and header, `render()`, `save()` |
| `src/open_diagram/describe.py` | `describe(diagram)`: the plain-text description behind `Diagram.describe()` and the SVG `<desc>` |
| `src/open_diagram/spec.py` | `from_spec(dict)` / `load_spec(path)`: JSON descriptions; `SpecError` names the place of every mistake |
| `src/open_diagram/mermaid.py` | `parse()` and `from_mermaid(text)`: Mermaid flowchart subset (listed in the module docstring) and its layered, banded layout |
| `src/open_diagram/cli.py` | The `open-diagram` command (`draw`, `check`, `describe`, `png`) and `load(path)` for .json, .mmd and .py |
| `src/open_diagram/mcp_server.py` | The MCP server (`open-diagram-mcp`): tools `format_guide`, `check`, `draw`, `describe`; the MCP toolkit is imported only inside `create_server()` |
| `tests/test_mcp_server.py` | Helper tests (any Python) and protocol tests over memory and stdio (skipped without the `mcp` extra) |
| `src/open_diagram/render.py` | `find_chrome()`, `svg_to_png()` (headless browser screenshot, optional Pillow crop) |
| `src/open_diagram/fonts/` | Inter 4.1, four weights, under the SIL OFL (`OFL.txt`). Do not replace or subset without updating the license note |
| `examples/` | One script per example; each defines `build() -> Diagram` and saves to `docs/images/<name>` |
| `templates/` | Python cloud resource/ETL starters, cached provider artwork and attribution; `build() -> Diagram`, offline rendering |
| `docs/images/` | Committed SVG and PNG output of the examples; the README embeds them |
| `skills/open-diagram/SKILL.md` | Agent Skill for *using* the library; its fix table keys on problem-message wording |
| `action.yml` | The GitHub Action (composite): installs the package from the action's own checkout, then runs `open-diagram check` or `draw` |
| `.github/workflows/diagrams.yml` | Runs that action on this repo's examples (`uses: ./`) |
| `tests/test_open_diagram.py` | unittest suite; `EXAMPLES` lists every example that must build with zero problems |
| `tests/test_cloud.py` | Resource measurement/attachment, enclosure nesting/styles, template checks, and byte-identical existing SVGs |

## How a build flows

1. `Block.measure(theme)` returns `(w, h)` computed from text widths. It never guesses.
2. `Diagram.add / right_of / below / stack / columns` place blocks and return `Placed` records.
3. `Diagram.link` and `Diagram.group` record lines and shaded areas.
4. `render()`: `_route()` and `_shape()` compute line paths, `_check()` collects problems, everything is drawn,
   and a `Report(svg, width, height, min_text, problems, files)` comes back.
5. `save(path)` writes the SVG (and PNG), prints a one-line summary, then raises
   `LayoutError(problems, files)` when `strict=True` and problems exist. Files are written before it raises.

## Invariants (do not break)

- **Measure, then draw.** `draw()` may receive more space than `measure()` asked for, never less. If it gets less,
  call `report(...)` with a named problem rather than clipping or shrinking text.
- **Everything drawn stays inside the measured box.** The 3D lid on panels and the raised faces on tiles are counted
  in `measure()`, so overlap and crossing checks see the whole shape. Any new decoration must do the same.
- **Text is drawn as outlines and measured from the font.** Use `text_width` / `wrap` / `Canvas.text`. Never
  estimate width from character counts, and never emit `<text>` elements.
- **Output is deterministic.** The same script must produce a byte-identical SVG (the example test asserts this).
  No timestamps, randomness, absolute paths or environment-dependent values in the SVG.
- **Problem messages are an API.** Agents act on them. Each message names parts by their labels and, where
  possible, says how to fix it. Keep these substrings stable: `overlap`, `px apart`, `crosses`, `sits on`,
  `needs N px`, `smallest text`, `group ... overlaps`, `sits on the title of group`, `facing away`, `graph: the label ... touches`,
  `graph: the line ... runs through`. If you add or change one, update the fix table in `skills/open-diagram/SKILL.md`.
- **Existing layouts must not move.** New shapes and options are opt-in (`ring`, `panels`, `start="auto"`); the
  `columns` layout and explicit sides behave exactly as before, and every committed picture must stay byte-identical
  unless a change is meant to alter it.
- **Colors come from `Theme`.** Blocks read colors from the theme (derived shades via `shade()` are fine). Do not
  hard-code hex values in blocks or the diagram code. Header text color is chosen by contrast in
  `Theme.header_colors()`; keep tones usable with either light or dark headers.
- **Minimum text size.** Nothing is drawn below `theme.min_text` (10 px); `Report.min_text` tracks the smallest.
- **Python 3.9+.** Modules use `from __future__ import annotations`. No `match`, no runtime `X | Y` unions, no
  3.10+ standard-library APIs.
- **Dependencies.** Runtime depends on `fonttools` only; Pillow is optional (the `png` extra). Do not add others.
- **Public API** is `__all__` in `src/open_diagram/__init__.py`. Changing it means updating the README tables.
- **JSON and Mermaid errors name the place** (`columns[1][0].tiles[2]`, `line 7`). Keep that when adding keys or syntax,
  and keep the README key table in step with `spec.py`.
- **`describe()` wording is relied on** by tests and by agents comparing a picture with a request: `->` for lines,
  `labeled "..."`, state words in parentheses, `[step N, state]` after panel titles.
- **MCP server rules.** Never print to stdout (it carries the protocol; wrap work in `redirect_stdout(sys.stderr)`
  and never call `Diagram.save()`, which prints). Accept JSON and Mermaid only, never Python. Write only inside the
  output folder (`safe_name()`). Keep the `GUIDE` example clean (a test draws it). The MCP toolkit stays an optional
  extra (`mcp`, Python 3.10+); the core keeps Python 3.9 and fontTools only.
- **Easter egg:** `open-diagram --soundtrack` prints The Gathering Field's Spotify link and is hidden from `--help`.
  Keep it, and keep it hidden.

## Common changes

**Add a block.** Subclass `Block` in `blocks.py`. Implement `measure`, `draw`, `statuses()` (what the key should
list) and, if lines attach to it, `ports()`. Export it in `__init__.py`, add a row to the README "Building blocks"
table, and add a test.

**Add a layout check.** Add it to `Diagram._check()`. Write the message in plain words with the parts' labels and a
fix. Add a test that triggers it, and a row to the SKILL.md fix table.

**Change the default look** (`Theme` defaults, header, tiles, 3D). Rebuild every example, look at every PNG, and
commit the SVG and PNG files together with the code. All examples must still report `0 layout problem(s)`.

**Add an example.** One script in `examples/` with all words in lists at the top, a `build()` that returns the
`Diagram`, and a `__main__` block that saves to `docs/images/<name>`. Use an invented organization and say so in a
`Note`; never real company names, logos or data. Prefer technical subjects that show a different kind of diagram.
Add the name to `EXAMPLES` in the tests and a row to the README examples table.

Cloud resource starters live separately in `templates/`. They may name cloud services and use unmodified provider
architecture icons, with pinned provenance and license notices in `templates/assets/README.md`. Use fictional
workloads, test every template offline, and commit its SVG/PNG preview together with its source. Keep resource and
enclosure additions opt-in; existing example SVGs must remain byte-identical.

**Edit the README quick start.** It mirrors `examples/quickstart.py` line for line; change both.

## Releasing

1. Set the same version in `pyproject.toml` and `src/open_diagram/__init__.py` (`__version__`), and update the
   `lukendeasy/open-diagram@vX.Y.Z` line in the README's GitHub Action example.
2. Make sure tests pass and every picture is rebuilt.
3. Publish a GitHub release tagged `vX.Y.Z`. `.github/workflows/publish.yml` builds the package and uploads it to
   PyPI through trusted publishing (no token). PyPI never accepts the same version twice; fix forward with a new
   patch version.

## Done means

- `python3 -m unittest discover -s tests` passes.
- Every example builds with `0 layout problem(s)` and the committed pictures match the code.
- README, SKILL.md and this file still describe the code as it is.
