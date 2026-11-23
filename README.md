# open-diagram

Python building blocks for dense architecture diagrams that check their own layout.

![A systems map for an invented video platform, drawn with open-diagram](https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/systems_map.png)

You describe panels, tiles, lines and groups in a short Python script. open-diagram measures every label from the font, places the blocks, and checks the result. If two panels collide or a line runs through a panel, the build says so by name. The output is an SVG (a picture made of shapes, sharp at any size) and a PNG.

The same blocks draw software systems, release pipelines, layered stacks, data models and business processes. It is built to be written by an AI agent such as Claude, Codex or Cursor, as well as by people. The checks catch layout mistakes before anyone looks at the picture, so a first attempt usually comes out clean.

## Install

```bash
pip install open-diagram
```

For the newest unreleased code: `pip install git+https://github.com/lukendeasy/open-diagram`.

open-diagram needs Python 3.9 or later and fontTools, which pip installs for you. To make PNG files it also needs Google Chrome, Chromium or Microsoft Edge. If yours is not in the usual place, set the `CHROME` environment variable to its path. The SVG is always written, browser or not.

## Quick start

```python
from open_diagram import Diagram, Panel, Tile

d = Diagram("How a search request is answered", tag="EXAMPLE")
app = d.add(Panel("Web app", ["Search box", "Results page", "Filters"], footer="Owner: Web team"))
api = d.right_of(app, Panel("Search API", [Tile("Checks access"), Tile("Caches results", status="building")],
                            footer="Owner: Platform team"), align="center")
index = d.right_of(api, Panel("Search index", ["Product text", Tile("Spelling fixes", status="planned")],
                              status="planned"), align="center")
d.link(app, api)
d.link(api, index, kind="planned", label="new")
d.save("quickstart")   # writes quickstart.svg and quickstart.png
```

![The quick start diagram](https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/quickstart.png)

The key at the top lists only the statuses and line kinds the picture uses.

## Why a first attempt comes out clean

- **Every label is measured before it is placed.** Widths come from the font's own spacing and kerning, so each box fits its words.
- **The build checks the layout and names each problem.** For example: `'Storage' and 'Recommendations' are only 9 px apart (minimum 16)` or `line 'Where videos come from' -> 'Storage' crosses 'Processing'; route it with via_x/via_y, move a block, or pass cross_ok=True`. `save()` writes the files, prints a summary, then raises `LayoutError` with the full list.
- **Text is drawn as shapes.** The SVG looks the same in a browser, PowerPoint, Keynote or Figma, with or without the font installed. Inter comes bundled.
- **Words stay apart from layout.** Keep labels in lists at the top of the script. Changing a word does not move anything by hand.

![How open-diagram turns a script into a picture, drawn with open-diagram](https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/how_it_works.png)

## Examples

Each example is one script in [`examples/`](https://github.com/lukendeasy/open-diagram/tree/main/examples). Run any of them with `python3 examples/<name>.py`.

| Example | Shows |
| --- | --- |
| [`systems_map.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/systems_map.py) | A video platform from upload to screen: columns, a group, steps, statuses, owners, a small data map with a worked example, and lanes above and below the picture |
| [`how_it_works.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/how_it_works.py) | How open-diagram itself works, drawn with open-diagram |
| [`pipeline.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/pipeline.py) | A release pipeline from pull request to production, with a rollback lane |
| [`card_payment.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/card_payment.py) | What happens when you tap a card: numbered steps for the order of events, return paths above and below |
| [`layers.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/layers.py) | A web product as stacked layers, with a side panel |
| [`concept_map.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/concept_map.py) | How git stores a project: its objects and links, with a worked example |
| [`smart_home.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/smart_home.py) | A smart home from sensor to phone, with a planned overnight update path |
| [`incident_response.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/incident_response.py) | How a team handles an outage, from the first alert to the lessons learned |
| [`business_map.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/business_map.py) | Not only software: a furniture store from order to doorstep |
| [`email_delivery.json`](https://github.com/lukendeasy/open-diagram/blob/main/examples/email_delivery.json) | How an email is delivered, written as JSON instead of Python |
| [`signup_flow.mmd`](https://github.com/lukendeasy/open-diagram/blob/main/examples/signup_flow.mmd) | A sign-up flow imported from a Mermaid flowchart |
| [`release_cycle.json`](https://github.com/lukendeasy/open-diagram/blob/main/examples/release_cycle.json) | A release cycle as a ring, with goals in the middle |
| [`quickstart.py`](https://github.com/lukendeasy/open-diagram/blob/main/examples/quickstart.py) | The code above |

<p>
  <img src="https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/pipeline.png" alt="Release pipeline example" width="54%">
  <img src="https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/layers.png" alt="Stacked layers example" width="40%">
</p>
<p>
  <img src="https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/card_payment.png" alt="Card payment example" width="49%">
  <img src="https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/smart_home.png" alt="Smart home example" width="45%">
</p>
<p>
  <img src="https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/concept_map.png" alt="Git data model example" width="47%">
  <img src="https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/incident_response.png" alt="Outage response example" width="47%">
</p>
<p>
  <img src="https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/business_map.png" alt="Business process example" width="70%">
</p>

## Building blocks

| Block | What it draws |
| --- | --- |
| `Panel(title, *sections, sub=, status=, step=, footer=, tone=)` | The main box: a colored header, sections stacked inside, an optional footer such as "Owner: Data team" |
| `Tiles(items, cols=, label=)` | A grid of tiles with one cell size. A plain list of labels inside a `Panel` becomes `Tiles` |
| `Tile(label, sub=, status=, icon=)` | One small box. `icon` takes a PNG or SVG file you supply; for AWS, Azure and Google Cloud, see [Cloud service icons](https://github.com/lukendeasy/open-diagram#cloud-service-icons) |
| `Resource(label, icon=, sub=, icon_size=64, border=)` | A standalone cloud resource: large icon above its workload label and service name, with no panel or raised tile |
| `Card(title, rows, intro=)` | A worked example: rows of name and value |
| `Graph(nodes, links, at)` | Things on a grid, joined by labelled lines. The build reports labels that touch nodes |
| `Row(*sections)` | Sections side by side inside a panel |
| `Text(text)` | A wrapped paragraph |
| `Note(title, *lines)` | A boxed note for the top right, such as "Draft" |

| Diagram method | What it does |
| --- | --- |
| `add(block, x, y)` | Place a block at a position |
| `right_of(ref, block, align=)` and `below(ref, block, align=)` | Place a block next to another, with the theme's gap |
| `columns([[...], [...]])` and `stack([...])` | Place columns left to right, each one top to bottom |
| `ring(blocks, center=[...])` | Place blocks around a circle, with optional blocks in the middle; returns both lists |
| `group(label, members, sub=)` | A shaded, dashed area around some blocks |
| `enclosure(label, members, border=, sub=, pad=, fill=, stroke=)` | A boundary around resources or nested enclosures; `border` is `solid`, `dashed` or `dotted`, independent of deployment state |
| `link(a, b, kind=, label=, start=, end=, via_x=, via_y=, dash=)` | An arrow. `kind="planned"` is dotted. `dash` optionally overrides the stroke style. `start="auto"` and `end="auto"` pick the sides that face each other. `via_y` routes it through a lane, for example above everything |
| `save(path)` | Write the SVG and PNG, print a summary, raise `LayoutError` if there are problems |
| `render()` | Return the SVG text and a report without writing files |
| `describe()` | Return what the picture says in plain words |
| `set_statuses({name: state})` | Set states by panel title, id or tile label, for example from a file |

## Statuses, colors and sizes

Panels have light gray headers and yellow step numbers (charcoal instead when any panel uses the yellow `accent` header, so yellow keeps one meaning). Each panel has a sloped top and each tile a raised edge, for a light 3D look; `Theme(lid=0, depth=0)` turns it off. `tone="accent"` gives a panel a soft yellow header, and `tone="dark"` a charcoal one. Header text turns white by itself on a dark header.

Statuses are shown by color and by word: Live, Being built, In trial, Planned and Retiring. Change them, or anything else, with a `Theme`:

```python
from open_diagram import Diagram, Status, Theme

theme = Theme(tones={"default": "#2B3036", "neutral": "#6A7078", "accent": "#FFC83D", "dark": "#111418"})
theme.statuses["pilot"] = Status("Pilot", stroke="#8E24AA", fill="#F6EDF9", dash="dashed")
d = Diagram("My picture", theme=theme)
```

## Command line

```bash
open-diagram draw plan.json       # writes plan.svg and plan.png; exits with 1 if the layout has problems
open-diagram check docs/*.json    # checks without writing files, for scripts and CI
open-diagram describe plan.json   # prints what the picture says, in plain words
```

Each command takes a JSON description (`.json`), a Mermaid flowchart (`.mmd` or `.mermaid`), or a Python script with a `build()` function that returns a `Diagram` (`.py`). Add `--statuses states.json` to set states by name before drawing.

## Describe a diagram in JSON

Any agent or language can describe a picture as plain data, with no Python:

```json
{
  "title": "How an email is delivered",
  "columns": [
    [{"id": "app", "title": "Mail app", "tiles": ["Write", "Send"], "cols": 1}],
    [{"id": "out", "title": "Sending server", "tiles": ["Queue", {"label": "Digital signature", "status": "building"}]}]
  ],
  "links": [{"from": "app", "to": "out"}]
}
```

![The JSON email example](https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/email_delivery.png)

| Part | Keys |
| --- | --- |
| Top level | `title` (required); one layout: `columns` (a list of columns, each a list of panels), `ring` (panels around a circle, with optional `center` and `start_angle`) or `panels` (each with `x` and `y`); `subtitle`, `tag`, `note` (`title`, `lines`), `steps` (`[[1, "First"]]`), `steps_label`, `gap`, `row_gap`, `valign`, `groups`, `links`, `statuses`, `theme` |
| Panel | `title` (required), `id`, `sub`, `status`, `step`, `footer`, `tone`, `width`, `x` and `y` (in `panels` only), `tiles` with `cols` and `label`, or `sections` (each `{"tiles": [...]}`, `{"text": "..."}`, `{"card": {...}}`, `{"graph": {...}}` or `{"row": [...]}`) |
| Tile | a string, or `{"label", "sub", "status"}` |
| Link | `from` and `to` (panel ids), `kind` (`flow` or `planned`), `label`, `start` and `end` (a side, or `auto` for the side facing the other panel: the default in `ring` and `panels`), `lane` (`top` or `bottom`, to route around the picture), `via_x`, `via_y`, `cross_ok`, `dash` (`solid`, `dashed` or `dotted`, independent of state) |
| Group | `label`, `members` (panel ids), `sub` |

Every mistake names its place, for example `columns[0][0].tiles[2]: unknown key(s) 'colour'`. From Python, use `from_spec(data)`. The full example is [`examples/email_delivery.json`](https://github.com/lukendeasy/open-diagram/blob/main/examples/email_delivery.json).

### Rings and free placement

Cycles read best as a ring. Use `"ring"` instead of `"columns"`, optionally with panels in the `"center"`; links then leave from the sides that face each other. For any other shape, use `"panels"` and give each panel an `x` and `y`. In Python, the same is `d.ring(blocks, center=[...])` and `d.add(block, x, y)`, with `link(a, b, start="auto", end="auto")`.

![A release cycle drawn with the ring layout](https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/release_cycle.png)

The example is [`examples/release_cycle.json`](https://github.com/lukendeasy/open-diagram/blob/main/examples/release_cycle.json).

## Bring your Mermaid

Already have a Mermaid flowchart? open-diagram lays it out again, with the same measuring and checks:

```bash
open-diagram draw signup_flow.mmd
```

![A Mermaid flowchart drawn by open-diagram](https://raw.githubusercontent.com/lukendeasy/open-diagram/main/docs/images/signup_flow.png)

It reads `flowchart` and `graph` in any direction, nodes of any bracket shape, chains, `&`, edge labels, and front-matter titles. Dotted edges (`-.->`) become planned connections. Each top-level `subgraph` becomes a shaded group with its own band, so groups never cover other nodes. A class named like a state (`A:::building`, or `class A,B planned`) sets that state. Lines that skip a step or point backwards travel above or below the picture. From Python, use `from_mermaid(text)`. The example is [`examples/signup_flow.mmd`](https://github.com/lukendeasy/open-diagram/blob/main/examples/signup_flow.mmd).

## The picture explains itself

`d.describe()`, or `open-diagram describe`, returns what the picture says in plain words: each block and its tiles with their states, the groups, every line and its label, and the key. The same text goes into the SVG as its description, so screen readers can read it. An agent can compare it with the request without looking at the picture.

```text
- Processing [step 1]: Upload checks; Transcoding; GPU encoding (being built); Auto captions (planned). Owner: Media team
- Video record -> Recommendations (connection to build)
```

## Keep diagrams from going stale

Add this GitHub Action and every push redraws your diagrams and fails the check if a layout problem appears:

```yaml
# .github/workflows/diagrams.yml
name: diagrams
on: [push, pull_request]
jobs:
  diagrams:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: lukendeasy/open-diagram@v0.4.0
        with:
          files: docs/diagrams/*.json docs/diagrams/*.mmd
          statuses: docs/diagrams/states.json   # optional
          mode: check                           # or draw, to write SVG and PNG next to each file
```

Keep states in a small file, such as `{"Fraud checks": "live", "Parcel lockers": "building"}`. When work ships, change one word; the pictures follow. Names match panel titles, panel ids and tile labels, and `live` returns a part to the default look. From Python, use `d.set_statuses(...)`.

## Use it from Claude Desktop, Claude Code or Cursor (MCP)

open-diagram can run as an MCP server: a small program that AI apps start on your computer, so the AI can draw diagrams as one of its own actions. Nothing is hosted and nothing leaves your computer. It accepts JSON and Mermaid only, never Python, and writes files only inside one output folder.

The commands below use [uv](https://docs.astral.sh/uv/), which fetches open-diagram and the Python it needs (3.10 or later) the first time.

**Claude Code**

```bash
claude mcp add open-diagram -- uvx --python 3.12 --from "open-diagram[mcp]" open-diagram-mcp
```

**Claude Desktop** (`claude_desktop_config.json`) **or Cursor** (`~/.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "open-diagram": {
      "command": "uvx",
      "args": ["--python", "3.12", "--from", "open-diagram[mcp]", "open-diagram-mcp",
               "--out", "/Users/you/Documents/open-diagram"]
    }
  }
}
```

Without uv: `pip install "open-diagram[mcp]"`, then use `open-diagram-mcp` as the command. uv keeps a copy of what it downloaded; to pick up a new release, add `--refresh` once after `uvx`.

| Action | What the AI gets |
| --- | --- |
| `format_guide` | A JSON example to copy, every key, Mermaid support, and how to fix each kind of problem |
| `check` | The layout problems, without writing files, so it can fix and retry quickly |
| `draw` | Writes the SVG and PNG, and returns the problems, the file paths, the plain-words description and the picture itself |
| `describe` | What the picture says, in plain words |

Files go to `--out`, else the `OPEN_DIAGRAM_OUT` environment variable, else an `open-diagram` folder where the app starts the server (or in your home folder if that one cannot be written).

## Use it with an AI agent

The folder [`skills/open-diagram/`](https://github.com/lukendeasy/open-diagram/tree/main/skills/open-diagram) is an Agent Skill: instructions an agent loads when it needs them. For Claude Code, copy it into your skills folder:

```bash
cp -r skills/open-diagram ~/.claude/skills/
```

Then ask for a picture in plain words, for example: "Draw a systems map of our checkout, warehouse and reporting, with what is live and what is planned." The skill tells the agent to plan the columns, write the script, run it, fix each named problem, and look at the PNG before it answers.

Agents changing the library itself should start with [AGENTS.md](https://github.com/lukendeasy/open-diagram/blob/main/AGENTS.md).

### Cloud service icons

The [`cloud-icons/`](https://github.com/lukendeasy/open-diagram/tree/main/cloud-icons) folder has one file each for [AWS](https://github.com/lukendeasy/open-diagram/blob/main/cloud-icons/aws.json), [Azure](https://github.com/lukendeasy/open-diagram/blob/main/cloud-icons/azure.json) and [Google Cloud](https://github.com/lukendeasy/open-diagram/blob/main/cloud-icons/gcp.json). Each file lists service keys, such as `s3` or `lambda`, with the web address of that service's SVG icon. AWS also includes `mwaa`, `glue` and `athena` for ETL diagrams. Every address points to one fixed version of the icon file, so later changes to the icon collection do not change your diagrams. A third party, theSVG, hosts the files; once downloaded, they work offline.

The [cloud-icons skill](https://github.com/lukendeasy/open-diagram/blob/main/skills/cloud-icons/SKILL.md) tells an agent how to pick icons, download them, and pass each file to `Resource(icon=...)` or `Tile(icon=...)`. The finished SVG and PNG contain the icons themselves, so you can share them without the icon links. Icons work from Python only: JSON, Mermaid and the MCP server do not take them. For Claude Code, copy the skill into your skills folder:

```bash
cp -r skills/cloud-icons ~/.claude/skills/
```

The icon lists stay in your copy of this repo. If you run the skill's example from another folder, set its `ICON_DIR` to the `cloud-icons/` folder in your copy.

The icons belong to Amazon, Microsoft and Google, and keep their own terms; this project's MIT license does not cover them. The skill links each provider's terms and says how to credit the icons when you share a diagram.

### Cloud resource and ETL templates

For cloud topology, start with the [cloud templates](templates/README.md). Resources have large service icons with
labels underneath, and connect individually inside nested account, VPC, subnet or logical enclosures.
Enclosure borders can be solid, dashed or dotted. Dashed task-control connections are independent of planned status.

The [AWS ETL template](templates/aws_etl.py) shows MWAA coordinating three Lambda extractors, with separate S3,
Glue, catalog, Athena and QuickSight resources. The [connectivity template](templates/aws_architecture.py) shows
nested network boundaries. Both include cached icons and render offline. The resource/enclosure API accepts
Azure and GCP artwork too. These Python templates live in the checkout, alongside [icon credits](templates/assets/README.md).

![AWS ETL resource DAG with large icons and dashed nested boundaries](docs/images/aws_etl.png)

```python
from open_diagram import Diagram, Resource, Theme

d = Diagram("Cloud resources", theme=Theme(link_labels={"flow": "Data flow"}))
extractor = d.add(Resource("Extractor", sub="AWS Lambda", icon="assets/lambda.svg"))
bucket = d.right_of(extractor, Resource("Raw data", sub="Amazon S3", icon="assets/s3.svg"))
d.link(extractor, bucket, label="objects")
workers = d.enclosure("Extraction", [extractor], border="dashed")
d.enclosure("AWS account", [workers, bucket], border="solid", pad=40)
```

## Contributing

Issues and pull requests are welcome.

**To report a bug or ask for a change,** [open an issue](https://github.com/lukendeasy/open-diagram/issues). Include the script, JSON or Mermaid file that shows the problem, and the problem message or picture you got.

**To make the change yourself,** open a pull request. For a large change, such as a new block or layout, open an issue first so we can agree on the approach before you write the code.

1. Fork the repo and create a branch.
2. Make the change. [AGENTS.md](https://github.com/lukendeasy/open-diagram/blob/main/AGENTS.md) lists the commands, the rules the code must keep, and what a finished change looks like. It is written for coding agents, and people can follow it the same way.
3. Run the tests:

   ```bash
   python3 -m unittest discover -s tests
   ```

4. If your change alters a picture, rebuild the examples and commit the new SVG and PNG files with the code:

   ```bash
   for f in examples/*.py; do PYTHONPATH=src python3 "$f"; done
   ```

5. Open the pull request. Say what changed and why, and attach a picture if the change alters how diagrams look.

New examples use an invented organization, never real company names, logos or data. To add or update a cloud icon, follow "Sources, family versions and attribution" in the [cloud-icons skill](https://github.com/lukendeasy/open-diagram/blob/main/skills/cloud-icons/SKILL.md): each new address must point to a fixed version of the file and return an SVG.

Contributions are released under the MIT license, like the rest of the project.

## Soundtrack

We recommend listening to music by [The Gathering Field](https://open.spotify.com/artist/0BfQ8COB7K647uB6a0kMZn) while you build.

## License

MIT, in [LICENSE](https://github.com/lukendeasy/open-diagram/blob/main/LICENSE). The bundled Inter font is by The Inter Project Authors, under the SIL Open Font License 1.1, in [src/open_diagram/fonts/OFL.txt](https://github.com/lukendeasy/open-diagram/blob/main/src/open_diagram/fonts/OFL.txt).
