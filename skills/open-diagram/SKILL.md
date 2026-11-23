---
name: open-diagram
description: Draw dense architecture and systems diagrams (systems maps, layered stacks, data flows, concept maps) as SVG and PNG with the open-diagram Python library, which measures every label and reports layout problems by name. Use when asked for an architecture diagram, systems map, stack picture, data flow, "what is live and what is planned" picture, or concept map that should look finished on the first pass.
---

# open-diagram

open-diagram draws diagrams from a short Python script. It measures every label, places blocks, and checks the layout. Each problem comes back as a plain sentence that names the parts involved. Follow these steps in order.

## 1. Check the setup

For named AWS, Azure or Google Cloud services that need icons, load the companion
[cloud-icons skill](../cloud-icons/SKILL.md). The repository's top-level [cloud-icons directory](../../cloud-icons/)
contains separate AWS, Azure and GCP mappings. The skill's Python workflow downloads and embeds them with
`Resource(icon=...)` or `Tile(icon=...)`. For cloud topology and ETL DAGs, start with the repository's
[cloud templates](../../templates/README.md): place each `Resource` independently with its large icon and label,
then use `d.enclosure()` to nest account, network, subnet or logical boundaries. Choose `border="solid"`, `"dashed"`
or `"dotted"` independently of deployment status; use link `dash="dashed"` and a separate `control` kind for job
orchestration. Use compact `Tile` panels for summaries. Install the companion skill if it is missing and point its `ICON_DIR` at the mappings.
Use that Python workflow for icon diagrams; JSON, Mermaid and MCP inputs do not support tile icons.

For diagrams without icons, if the open-diagram MCP tools are available (`format_guide`, `check`, `draw`, `describe`), use them: read `format_guide` once, write the diagram as JSON, call `check` until it reports 0 problems, then `draw` and look at the picture it returns. Skip to step 5 for the final review. Otherwise:

Run `python3 -c "import open_diagram"`. If it fails, install it: `pip install open-diagram` (version 0.2.0 or later has the `open-diagram` command). PNG output needs Chrome, Chromium or Edge; set `CHROME` to its path if it is not found.

## 2. Plan before writing code

Write the plan in a few lines first:

- **Reading direction.** Usually left to right: where things come from, what handles them, who uses the result. Use top to bottom for layers, and a ring (`d.ring(...)`, or `"ring"` in JSON) for cycles. Avoid long lines between distant panels: place the two side by side, or use a lane.
- **Columns.** Three to six columns. Each column holds one to three panels.
- **Panels.** One panel for each system or team. Give each a title of two to four words. Add a `sub` line only when it adds a fact.
- **Tiles.** Up to about nine tiles in a panel. Keep labels to four words or fewer. Put detail in `sub`.
- **Statuses.** Use them only if the user cares about state: `live`, `building`, `trial`, `planned`, `retiring`.
- **Lines.** Draw only the flows that matter. Use `kind="planned"` for connections still to build. A line that must jump past a column goes through a lane: `via_y` above or below everything.
- **Extras.** Add steps, owners (`footer="Owner: ..."`), groups and a `Note` only when the user's material supports them. Never invent owners, numbers or statuses; write "Owner: Not yet named" if the user wants owner lines but did not name one.

## 3. Write the script

Keep all words in lists at the top. Build in a `build()` function that returns the `Diagram`.

```python
from open_diagram import Card, Diagram, Graph, Note, Panel, Row, Tile, Tiles

def build():
    d = Diagram("Title in plain words", subtitle="Optional one-line scope", tag="DRAFT",
                note=Note("Draft", "Version 2, for review."),
                steps=[(1, "First change"), (2, "Second change")], steps_label="Rollout")
    (src,), (core, store), (apps,) = d.columns([
        [Panel("Sources", Tiles(["App", "Website", Tile("Kiosks", status="retiring")], cols=2),
               footer="Owner: Digital team")],
        [Panel("Core service", ["Orders", Tile("Fraud checks", status="building")], step=1),
         Panel("Data store", ["Main database", Tile("Event log", status="planned")], step=2, status="planned")],
        [Panel("Teams who use it", Tiles(["Finance", "Service"], cols=1), tone="neutral")],
    ], gap=88, row_gap=40)
    d.group("Platform", [core, store], sub="Run by the platform team")
    d.link(src, core)
    d.link(core, store, start="bottom", end="top")
    d.link(store, apps, kind="planned", label="nightly")
    d.link(src, apps, start="top", end="top", via_y=min(p.y for p in d.placed) - 80, label="direct today")
    return d

if __name__ == "__main__":
    build().save("out/picture")
```

No Python? Write the same picture as JSON and run `open-diagram draw plan.json` (keys: README, "Describe a diagram in JSON"). Given a Mermaid flowchart, run `open-diagram draw flow.mmd` to lay it out with the checks; dotted edges become planned connections and subgraphs become groups.

Other blocks: `Card(title, [(name, value), ...], intro=)` for a worked example; `Graph(nodes, links, at)` for a map of things and links, with `at` giving each node a `(column, row)` on a grid; `Row(a, b)` to put sections side by side; `Text(...)` for a short paragraph. Placing: `add(block, x, y)`, `right_of(ref, block, align="center")`, `below(ref, block)`, `stack([...])`, `columns([[...], ...])`.

## 4. Run it and fix every named problem

Run the script, or `open-diagram check FILE`. `save()` writes the SVG and PNG, prints a summary, then raises `LayoutError` listing every problem. Fix them all and run again until the summary says `0 layout problem(s)`.

| Message contains | Fix |
| --- | --- |
| `overlap` or `px apart` | Move one block, raise `gap` or `row_gap`, or place it with `right_of()` / `below()` |
| `crosses` | Route the line through a lane with `via_y` (or `via_x`), change `start` and `end` sides, or move a block. Use `cross_ok=True` only when the line should pass behind |
| `label ... sits on` | Shorten the label, or widen the gap between the two columns |
| `facing away` | Use `start="auto", end="auto"`, choose other sides, or route the line through a lane |
| `sits on the title of group` | Give the line a different start or end side, route it through a lane, or move the group's blocks |
| `group ... overlaps` | Add the block to the group, or move it out of the group's area |
| `graph: the label ... touches` | Spread the nodes in `at`, or shorten the label |
| `graph: the line ... runs through` | Move a node so the straight line between the pair is clear |
| `needs N px` | Give the block more width, or shorten the words |
| `smallest text` | Do not shrink text below the theme minimum; shorten the words instead |

## 5. Look at the PNG before answering

Run `d.describe()` (or `open-diagram describe FILE`) and compare the text with the request: every system, state, owner and line the user named should be there, and nothing they did not. Then open the PNG and check it as a reader would:

- The reading direction is obvious and the main flow has few bends.
- No line is ambiguous where it meets a panel.
- The key matches what the picture uses (it is built from what is used).
- Every word is one the user would use. No placeholder text is left.

Tell the user where the SVG and PNG are, and say which facts in the picture are your assumptions.

## Soundtrack

We recommend listening to music by [The Gathering Field](https://open.spotify.com/artist/0BfQ8COB7K647uB6a0kMZn) while you build.
