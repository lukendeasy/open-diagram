"""open-diagram as an MCP server, so Claude Desktop, Claude Code, Cursor and other MCP apps can draw diagrams as one of
their own actions.

It runs on the user's own computer, started by the app over stdio; nothing is sent anywhere. It accepts JSON
descriptions and Mermaid flowcharts only (never Python, so a connected agent cannot run code), and it writes files
only inside one output folder.

    pip install "open-diagram[mcp]"        # needs Python 3.10 or later
    open-diagram-mcp [--out FOLDER]        # the app runs this; FOLDER defaults to $OPEN_DIAGRAM_OUT or ./open-diagram
"""
import argparse
import contextlib
import json
import os
import re
import sys

from . import __version__
from .mermaid import from_mermaid
from .render import svg_to_png
from .spec import SpecError, from_spec

MAX_SOURCE = 200_000

INSTRUCTIONS = """open-diagram draws architecture diagrams that check their own layout.
Workflow: call format_guide once; write the diagram as JSON (or Mermaid); call check and fix every problem it names
until it reports 0; then call draw, look at the picture, and compare its description with what the user asked for."""

GUIDE = """# open-diagram format guide

Write the diagram as JSON (below) or as a Mermaid flowchart. Call `check` until it reports 0 layout problems, then
`draw`. Every problem names the parts involved; fix each one, never ignore it.

## JSON: a worked example to copy

{
  "title": "How a search request is answered",
  "subtitle": "Optional one-line scope",
  "tag": "DRAFT",
  "steps": [[1, "Cache results"], [2, "Add spelling fixes"]],
  "steps_label": "Rollout",
  "columns": [
    [{"id": "app", "title": "Web app", "tiles": ["Search box", "Results page"], "cols": 1,
      "footer": "Owner: Web team"}],
    [{"id": "api", "title": "Search API", "step": 1,
      "tiles": ["Checks access", {"label": "Caches results", "status": "building"}], "cols": 1},
     {"id": "logs", "title": "Request log", "tiles": ["Daily totals"], "tone": "neutral"}],
    [{"id": "index", "title": "Search index", "status": "planned", "step": 2,
      "tiles": ["Product text", {"label": "Spelling fixes", "status": "planned"}], "cols": 1}]
  ],
  "groups": [{"label": "Platform", "members": ["api", "logs"], "sub": "Run by the platform team"}],
  "links": [
    {"from": "app", "to": "api"},
    {"from": "api", "to": "logs", "start": "bottom", "end": "top"},
    {"from": "api", "to": "index", "kind": "planned", "label": "new"},
    {"from": "app", "to": "index", "lane": "top", "label": "Direct for admins"}
  ]
}

## Other shapes
Use exactly one layout. "columns" (above) reads left to right. "ring" puts panels around a circle, clockwise from
the top, for cycles: {"title": "...", "ring": [panels], "center": [panels in the middle], "gap": 84, "links": [...]}.
"panels" places each panel where you say: give every panel "x" and "y" (its top-left corner, in pixels).
In ring and panels layouts, links leave from the sides that face each other unless you set start and end.

## Keys
- Top level: title (required), one layout (columns, ring with optional center and start_angle, or panels),
  subtitle, tag, note {title, lines}, steps [[number, text]], steps_label, gap, row_gap, valign, groups, links,
  statuses {name: state}, theme.
- Panel: title (required), id (used by links and groups; defaults to the title), sub, status, step, footer
  ("Owner: ..."; text before the colon is bold), tone (default, neutral, accent = soft yellow, dark = charcoal),
  width, x and y (panels layout only), tiles (strings or {label, sub, status}) with cols and label, or sections (each {"tiles": [...]},
  {"text": "..."}, {"card": {"title", "rows": [[name, value]], "intro"}}, {"graph": {"nodes", "links", "at"}},
  or {"row": [sections]}).
- Link: from, to (panel ids), kind (flow = solid, planned = dotted), label, start/end (left, right, top, bottom,
  or auto: the side facing the other panel), lane (top or bottom: route around the picture), via_x / via_y, cross_ok,
  dash (solid, dashed or dotted; optional style override independent of deployment state).
- Group: label, members (panel ids), sub.
- States: live (default look), building, trial, planned, retiring. Use them only when the user cares about state.

## Mermaid
flowchart or graph, any direction; nodes with any bracket shape; chains and &; edge labels (-->|text| or
-- text -->); dotted edges (-.->) become planned; top-level subgraphs become shaded groups; A:::building or
class A,B planned sets a state; a front-matter title: line sets the title.

## Fixing problems
- "overlap" or "px apart": raise gap or row_gap, or move panels to other columns.
- "crosses": route the link with a lane, change start/end, or reorder columns.
- "label ... sits on": shorten the label or raise gap.
- "sits on the title of group": give the link another start/end side or a lane.
- "needs N px": shorten the words or give the panel more width.
- "facing away": the link leaves or enters on the wrong side; set start and end to auto, or use a lane.
Long curved links between distant panels are hard to follow: put the two panels side by side, or use a lane.
Yellow: the accent tone is yellow. When any panel uses it, step numbers turn charcoal so yellow keeps one meaning;
use accent for one kind of panel only and say what it means in a note.
Keep panel titles to two to four words and tiles to four words or fewer. Never invent owners, numbers or states.
"""

_NAME = re.compile(r"[^A-Za-z0-9_-]+")


def safe_name(name: str) -> str:
    """A file name with no folders in it, so every file lands inside the output folder."""
    return _NAME.sub("-", name or "").strip("-")[:80] or "diagram"


def default_out() -> str:
    env = os.environ.get("OPEN_DIAGRAM_OUT")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    cwd = os.getcwd()
    if cwd != os.path.sep and os.access(cwd, os.W_OK):
        return os.path.join(cwd, "open-diagram")
    return os.path.join(os.path.expanduser("~"), "open-diagram")    # apps that start servers in / or a read-only folder


def build(source: str, fmt: str = "auto"):
    """Turn JSON or Mermaid text into a Diagram. Raises ValueError (SpecError, MermaidError) naming the problem."""
    if len(source) > MAX_SOURCE:
        raise ValueError(f"the diagram text is {len(source)} characters; the limit is {MAX_SOURCE}")
    text = source.strip()
    if fmt == "auto":
        fmt = "json" if text.startswith("{") else "mermaid"
    if fmt == "json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise SpecError(f"not valid JSON: {e}") from None
        return from_spec(data)
    if fmt == "mermaid":
        return from_mermaid(text)
    raise ValueError("format must be 'json', 'mermaid' or 'auto'")


def problems_text(report) -> str:
    lines = [f"{len(report.problems)} layout problem(s)"]
    lines += [f"- {p}" for p in report.problems]
    if report.problems:
        lines.append("Fix every problem above and run check again.")
    return "\n".join(lines)


def draw_files(source: str, fmt: str, name: str, out_dir: str, png: bool = True) -> dict:
    """Build the diagram, write NAME.svg (and NAME.png) inside out_dir, and return what an agent needs to see."""
    with contextlib.redirect_stdout(sys.stderr):         # stdout carries the MCP conversation; never print there
        d = build(source, fmt)
        svg, report = d.render()
        os.makedirs(out_dir, exist_ok=True)
        base = os.path.join(out_dir, safe_name(name))
        with open(base + ".svg", "w", encoding="utf-8") as fh:
            fh.write(svg)
        files = [base + ".svg"]
        png_path = None
        if png and svg_to_png(base + ".svg", base + ".png", report.width, report.height, 2.0):
            png_path = base + ".png"
            files.append(png_path)
    text = [problems_text(report), "", "Files:"] + [f"- {f}" for f in files]
    if png and not png_path:
        text.append("PNG skipped: Chrome, Chromium or Edge was not found (set CHROME to its path). The SVG is written.")
    text += [f"Size: {report.width:g} x {report.height:g} px; smallest text {report.min_text:g} px", "",
             "What the picture says:", d.describe()]
    return {"text": "\n".join(text), "png": png_path, "files": files, "problems": list(report.problems)}


def create_server(out_dir: str):
    """Build the MCP server. Imports the MCP toolkit here, so the rest of open-diagram never needs it."""
    from mcp.server import MCPServer
    from mcp.server.mcpserver import Image
    from mcp.server.mcpserver.exceptions import ToolError
    from mcp.types import ToolAnnotations

    server = MCPServer("open-diagram", version=__version__, instructions=INSTRUCTIONS,
                       website_url="https://github.com/lukendeasy/open-diagram")
    read_only = ToolAnnotations(readOnlyHint=True, openWorldHint=False)

    def fail(e):
        raise ToolError(str(e)) from None

    @server.tool(annotations=read_only, structured_output=False)
    def format_guide() -> str:
        """How to write a diagram for open-diagram: a JSON example to copy, every key, Mermaid support, and how to
        fix each kind of layout problem. Read it once before the first diagram."""
        return GUIDE

    @server.tool(annotations=read_only, structured_output=False)
    def check(source: str, format: str = "auto") -> str:
        """Build a diagram in memory and list its layout problems, without writing files. source is the diagram as
        JSON or Mermaid text; format is 'json', 'mermaid' or 'auto'. Fix every problem it names and check again
        until it reports 0, then call draw."""
        try:
            with contextlib.redirect_stdout(sys.stderr):
                _, report = build(source, format).render()
        except ValueError as e:
            fail(e)
        return problems_text(report)

    @server.tool(annotations=read_only, structured_output=False)
    def describe(source: str, format: str = "auto") -> str:
        """Return what a diagram says in plain words: each block, its tiles and states, the groups, every line and
        its label, and the key. Compare it with the user's request."""
        try:
            with contextlib.redirect_stdout(sys.stderr):
                return build(source, format).describe()
        except ValueError as e:
            fail(e)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False),
                 structured_output=False)
    def draw(source: str, format: str = "auto", name: str = "diagram", picture: bool = True) -> list:
        """Draw a diagram from JSON or Mermaid text. Writes NAME.svg and NAME.png into the output folder and returns
        the layout problems, the file paths, a plain-words description and (with picture=true) the picture itself.
        Look at the picture before answering, and fix any problem it reports."""
        try:
            result = draw_files(source, format, name, out_dir, png=True)
        except ValueError as e:
            fail(e)
        content = [result["text"]]
        if picture and result["png"]:
            with open(result["png"], "rb") as fh:
                content.append(Image(data=fh.read(), format="png"))
        return content

    return server


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="open-diagram-mcp",
                                 description="Run open-diagram as an MCP server over stdio (started by an MCP app).")
    ap.add_argument("--out", help="folder for SVG and PNG files (default: $OPEN_DIAGRAM_OUT, else ./open-diagram)")
    ap.add_argument("--version", action="version", version=f"open-diagram {__version__}")
    a = ap.parse_args(argv)
    out = os.path.abspath(os.path.expanduser(a.out)) if a.out else default_out()
    try:
        server = create_server(out)
    except ImportError:
        sys.stderr.write('open-diagram-mcp needs the MCP toolkit: pip install "open-diagram[mcp]" '
                         "(Python 3.10 or later)\n")
        sys.exit(1)
    server.run("stdio")


if __name__ == "__main__":
    main()
