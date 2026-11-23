"""Build a Diagram from plain data (JSON), so any agent or language can describe a picture without writing Python.

    {
      "title": "How an email is delivered",
      "columns": [[{"id": "app", "title": "Mail app", "tiles": ["Compose", "Send"]}],
                  [{"id": "out", "title": "Outgoing server", "tiles": ["Queue", {"label": "Signing", "status": "building"}]}]],
      "links": [{"from": "app", "to": "out"}]
    }

Every mistake raises SpecError with the place it happened, for example `columns[1][0].tiles[1]: unknown key 'colour'`.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from .blocks import Card, Graph, Note, Panel, Row, Text, Tile, Tiles
from .diagram import Diagram
from .theme import Status, Theme


class SpecError(ValueError):
    """A problem in a diagram description, naming where it is."""


TOP_KEYS = {"title", "subtitle", "tag", "note", "steps", "steps_label", "legend", "theme", "columns", "panels", "ring",
            "center", "gap", "row_gap", "valign", "start_angle", "groups", "links", "statuses"}
LAYOUTS = ("columns", "panels", "ring")
PANEL_KEYS = {"id", "title", "sub", "status", "step", "footer", "tone", "width", "tiles", "cols", "label", "sections",
              "x", "y"}
TILE_KEYS = {"label", "sub", "status"}
LINK_KEYS = {"from", "to", "kind", "label", "start", "end", "lane", "via_x", "via_y", "cross_ok", "dash"}
GROUP_KEYS = {"label", "members", "sub"}


def _keys(obj: Any, allowed: set, where: str, required: tuple = ()) -> None:
    if not isinstance(obj, dict):
        raise SpecError(f"{where}: expected an object, got {type(obj).__name__}")
    extra = sorted(set(obj) - allowed)
    if extra:
        raise SpecError(f"{where}: unknown key(s) {', '.join(map(repr, extra))}; allowed: {', '.join(sorted(allowed))}")
    for key in required:
        if key not in obj:
            raise SpecError(f"{where}: missing required key '{key}'")


def _tile(item: Any, where: str) -> Tile:
    if isinstance(item, str):
        return Tile(item)
    _keys(item, TILE_KEYS, where, ("label",))
    return Tile(item["label"], sub=item.get("sub"), status=item.get("status"))


def _tiles(items: Any, where: str, cols=None, label=None) -> Tiles:
    if not isinstance(items, list) or not items:
        raise SpecError(f"{where}: tiles must be a non-empty list")
    return Tiles([_tile(i, f"{where}[{n}]") for n, i in enumerate(items)], cols=cols, label=label)


def _section(obj: Any, where: str):
    if isinstance(obj, list):
        return _tiles(obj, where)
    if isinstance(obj, str):
        return Text(obj)
    if not isinstance(obj, dict):
        raise SpecError(f"{where}: a section is a list of tiles, a string, or an object")
    if "tiles" in obj:
        _keys(obj, {"tiles", "cols", "label"}, where)
        return _tiles(obj["tiles"], f"{where}.tiles", obj.get("cols"), obj.get("label"))
    if "text" in obj:
        _keys(obj, {"text"}, where)
        return Text(obj["text"])
    if "card" in obj:
        _keys(obj, {"card"}, where)
        c = obj["card"]
        _keys(c, {"title", "rows", "intro"}, f"{where}.card", ("title", "rows"))
        return Card(c["title"], [tuple(r) for r in c["rows"]], intro=c.get("intro"))
    if "graph" in obj:
        _keys(obj, {"graph"}, where)
        g = obj["graph"]
        _keys(g, {"nodes", "links", "at"}, f"{where}.graph", ("nodes", "links", "at"))
        return Graph(g["nodes"], [tuple(x) for x in g["links"]], {k: tuple(v) for k, v in g["at"].items()})
    if "row" in obj:
        _keys(obj, {"row"}, where)
        return Row(*[_section(s, f"{where}.row[{n}]") for n, s in enumerate(obj["row"])])
    raise SpecError(f"{where}: a section needs one of 'tiles', 'text', 'card', 'graph' or 'row'")


def panel_from_spec(obj: Any, where: str = "panel") -> Panel:
    """Build one Panel from its JSON object (the same keys as in a full description). Public, for scripts that
    place panels themselves."""
    _keys(obj, PANEL_KEYS, where, ("title",))
    body = []
    if "tiles" in obj:
        body.append(_tiles(obj["tiles"], f"{where}.tiles", obj.get("cols"), obj.get("label")))
    body += [_section(s, f"{where}.sections[{n}]") for n, s in enumerate(obj.get("sections", []))]
    return Panel(obj["title"], *body, sub=obj.get("sub"), status=obj.get("status"), step=obj.get("step"),
                 footer=obj.get("footer"), tone=obj.get("tone", "default"), width=obj.get("width"),
                 name=obj.get("id") or obj["title"])


def theme_from_spec(obj: Any) -> Theme:
    """Build a Theme from the JSON "theme" object. Public, for scripts that place panels themselves."""
    t = Theme()
    if obj is None:
        return t
    if not isinstance(obj, dict):
        raise SpecError("theme: expected an object")
    for key, value in obj.items():
        if key == "tones":
            t.tones.update(value)
        elif key == "statuses":
            for name, s in value.items():
                _keys(s, {"label", "stroke", "fill", "dash"}, f"theme.statuses.{name}", ("label", "stroke", "fill"))
                t.statuses[name] = Status(**s)
        elif hasattr(t, key) and not callable(getattr(t, key)):
            setattr(t, key, value)
        else:
            raise SpecError(f"theme: unknown setting '{key}'")
    return t


_panel = panel_from_spec        # older names, kept for scripts that already use them
_theme = theme_from_spec


def from_spec(spec: Dict[str, Any]) -> Diagram:
    """Build a Diagram from a dict (parsed JSON). Raises SpecError naming the place of any mistake."""
    _keys(spec, TOP_KEYS, "diagram", ("title",))
    chosen = [k for k in LAYOUTS if k in spec]
    if len(chosen) != 1:
        raise SpecError("diagram: give exactly one layout: 'columns' (left to right), 'panels' (each with x and y) "
                        "or 'ring' (around a circle)" + (f"; got {', '.join(chosen)}" if chosen else ""))
    layout = chosen[0]
    note = None
    if spec.get("note"):
        n = spec["note"]
        _keys(n, {"title", "lines"}, "note", ("title",))
        note = Note(n["title"], *n.get("lines", []))
    d = Diagram(spec["title"], subtitle=spec.get("subtitle"), tag=spec.get("tag"), note=note,
                theme=theme_from_spec(spec.get("theme")), legend=spec.get("legend", True),
                steps=[tuple(s) for s in spec.get("steps", [])], steps_label=spec.get("steps_label", "Steps"))
    if "center" in spec and layout != "ring":
        raise SpecError("center: only works with the 'ring' layout")

    def plain(obj, where):
        if isinstance(obj, dict) and ("x" in obj or "y" in obj):
            raise SpecError(f"{where}: x and y only work in the 'panels' layout")
        return panel_from_spec(obj, where)

    items = spec[layout]
    if not isinstance(items, list) or not items:
        raise SpecError(f"{layout}: expected a non-empty list")
    if layout == "columns":
        panels = [[plain(p, f"columns[{i}][{j}]") for j, p in enumerate(col if isinstance(col, list) else [col])]
                  for i, col in enumerate(items)]
        placed = [p for col in d.columns(panels, gap=spec.get("gap"), row_gap=spec.get("row_gap"),
                                         valign=spec.get("valign", "center")) for p in col]
    elif layout == "panels":
        placed = []
        for n, obj in enumerate(items):
            where = f"panels[{n}]"
            if not isinstance(obj, dict) or not all(isinstance(obj.get(k), (int, float)) for k in ("x", "y")):
                raise SpecError(f"{where}: each panel needs numbers for x and y (its top-left corner, in pixels)")
            placed.append(d.add(panel_from_spec(obj, where), obj["x"], obj["y"]))
    else:
        middle = spec.get("center", [])
        if not isinstance(middle, list):
            raise SpecError("center: expected a list of panels")
        around, inside = d.ring([plain(p, f"ring[{n}]") for n, p in enumerate(items)], gap=spec.get("gap"),
                                start_angle=spec.get("start_angle", -90.0),
                                center=[plain(p, f"center[{n}]") for n, p in enumerate(middle)])
        placed = around + inside
    by_id = {p.name: p for p in placed}

    def find(name, where):
        if name not in by_id:
            raise SpecError(f"{where}: no panel with id '{name}'; ids: {', '.join(by_id)}")
        return by_id[name]

    for n, g in enumerate(spec.get("groups", [])):
        _keys(g, GROUP_KEYS, f"groups[{n}]", ("label", "members"))
        d.group(g["label"], [find(m, f"groups[{n}].members") for m in g["members"]], sub=g.get("sub"))

    top = min(p.y for p in placed)
    bottom = max(p.bottom for p in placed)
    default_sides = ("right", "left") if layout == "columns" else ("auto", "auto")
    lanes = {"top": 0, "bottom": 0}
    for n, link in enumerate(spec.get("links", [])):
        where = f"links[{n}]"
        _keys(link, LINK_KEYS, where, ("from", "to"))
        a, b = find(link["from"], f"{where}.from"), find(link["to"], f"{where}.to")
        start, end = link.get("start", default_sides[0]), link.get("end", default_sides[1])
        via_y = link.get("via_y")
        lane = link.get("lane")
        if lane is not None:
            if lane not in lanes:
                raise SpecError(f"{where}.lane: use 'top' or 'bottom'")
            k = lanes[lane]
            lanes[lane] += 1
            via_y = top - 70 - 30 * k if lane == "top" else bottom + 44 + 30 * k
            start, end = link.get("start", lane), link.get("end", lane)
        try:
            d.link(a, b, kind=link.get("kind", "flow"), label=link.get("label"), start=start, end=end,
                   via_x=link.get("via_x"), via_y=via_y, cross_ok=link.get("cross_ok", False), dash=link.get("dash"))
        except (TypeError, ValueError) as e:
            raise SpecError(f"{where}: {e}") from None
    if spec.get("statuses"):
        d.set_statuses(spec["statuses"])
    return d


def load_spec(path: str) -> Diagram:
    with open(path, encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError as e:
            raise SpecError(f"{path}: not valid JSON ({e})") from None
    return from_spec(data)
