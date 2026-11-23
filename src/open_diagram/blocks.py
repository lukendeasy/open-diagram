"""Building blocks. Each block measures itself from its words first, then draws itself at a given place.

A block never guesses its size: `measure()` returns the width and height its text needs, and `draw()` may be given
more width (to line up a column) but never less.
"""
from __future__ import annotations

import base64
import math
import mimetypes
import os
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Set, Tuple, Union

from .fonts import cap_height, fmt, lines_width, text_width, wrap
from .svg import Canvas
from .theme import Theme, shade

Report = Callable[[str], None]
ICON = 16.0


class Block:
    """Base class: something with a size that can be drawn at a position."""

    name: Optional[str] = None

    def measure(self, t: Theme) -> Tuple[float, float]:
        raise NotImplementedError

    def draw(self, c: Canvas, x: float, y: float, w: float, h: float, t: Theme, report: Report) -> None:
        raise NotImplementedError

    def statuses(self) -> Set[str]:
        return set()

    def ports(self, side: str, w: float, h: float, t: Theme) -> Tuple[float, float]:
        """The stretch of one side where lines may attach, as offsets from the top or left corner."""
        length = h if side in ("left", "right") else w
        return length * 0.2, length * 0.8

    def anchor(self, side: str, offset: float, w: float, h: float, t: Theme) -> Tuple[float, float]:
        """A connection point, relative to this block's top-left corner."""
        return {"left": (0, offset), "right": (w, offset),
                "top": (offset, 0), "bottom": (offset, h)}[side]


def _data_uri(path: str) -> str:
    kind = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as fh:
        return f"data:{kind};base64,{base64.b64encode(fh.read()).decode('ascii')}"


class Resource(Block):
    """A standalone cloud resource: a large local icon above measured labels, without a panel.

    Missing artwork stays text-only. border optionally frames the resource independently of deployment state.
    """

    def __init__(self, label: str, icon: Optional[str] = None, sub: Optional[str] = None,
                 icon_size: float = 64, max_width: float = 180, border: Optional[str] = None,
                 name: Optional[str] = None):
        if not label:
            raise ValueError("resource: label must not be empty")
        for key, value in (("icon_size", icon_size), ("max_width", max_width)):
            if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"resource {label!r}: {key} must be a positive finite number")
        if border not in (None, "solid", "dashed", "dotted"):
            raise ValueError(f"resource {label!r}: border must be solid, dashed, dotted or None")
        if icon and not os.path.isfile(icon):
            raise FileNotFoundError(f"resource {label!r}: icon file not found: {icon}")
        self.label, self.icon, self.sub = label, icon, sub
        self.icon_size, self.max_width, self.border = icon_size, max_width, border
        self.name = name or label

    def _lines(self, t):
        room = max(1, self.max_width - 2 * t.pad)
        return (wrap(self.label, t.tile, room, "semibold"),
                wrap(self.sub, t.tile_sub, room) if self.sub else [])

    def measure(self, t):
        main, sub = self._lines(t)
        image_h = self.icon_size + t.tile_gap if self.icon else 0
        w = max(self.icon_size if self.icon else 0, lines_width(main, t.tile, "semibold"),
                lines_width(sub, t.tile_sub)) + 2 * t.pad
        h = 2 * t.pad + image_h + (len(main) + len(sub)) * t.line_h + (4 if sub else 0)
        return w, h

    def draw(self, c, x, y, w, h, t, report):
        need_w, need_h = self.measure(t)
        if w + 0.5 < need_w or h + 0.5 < need_h:
            report(f"resource {self.label!r} needs {need_w:g} x {need_h:g} px but has {w:g} x {h:g} px")
        if self.border:
            c.rect(x, y, w, h, t.paper, t.tile_stroke, 1, t.radius,
                   None if self.border == "solid" else self.border)
        cy = y + t.pad
        if self.icon:
            c.image(_data_uri(self.icon), x + (w - self.icon_size) / 2, cy, self.icon_size, self.icon_size)
            cy += self.icon_size + t.tile_gap
        main, sub = self._lines(t)
        for line in main:
            c.text_centered(line, x + w / 2, cy + t.line_h / 2, t.tile, "semibold", t.ink)
            cy += t.line_h
        if sub:
            cy += 4
        for line in sub:
            c.text_centered(line, x + w / 2, cy + t.line_h / 2, t.tile_sub, "regular", t.muted)
            cy += t.line_h

    def ports(self, side, w, h, t):
        if self.icon and side in ("left", "right"):
            return t.pad + self.icon_size / 2, t.pad + self.icon_size / 2
        return super().ports(side, w, h, t)

    def anchor(self, side, offset, w, h, t):
        if self.icon and self.border is None:
            if side in ("left", "right"):
                return (w + (-self.icon_size if side == "left" else self.icon_size)) / 2, offset
            if side == "top":
                return offset, t.pad
        return super().anchor(side, offset, w, h, t)


# --------------------------------------------------------------------------------------------------------- tiles

class Tile(Block):
    """A small box: a label, an optional second line, an optional status and an optional icon file."""

    def __init__(self, label: str, sub: Optional[str] = None, status: Optional[str] = None,
                 icon: Optional[str] = None, width: Optional[float] = None):
        self.label, self.sub, self.status, self.icon, self.width = label, sub, status, icon, width
        if icon and not os.path.exists(icon):
            raise FileNotFoundError(f"tile {label!r}: icon file not found: {icon}")

    def _lines(self, t: Theme) -> Tuple[List[str], List[str]]:
        room = t.tile_max_w - 2 * t.pad
        main = wrap(self.label, t.tile, room - (ICON + 6 if self.icon else 0), "semibold")
        sub = wrap(self.sub, t.tile_sub, room) if self.sub else []
        return main, sub

    def measure(self, t: Theme) -> Tuple[float, float]:
        main, sub = self._lines(t)
        icon = ICON + 6 if self.icon else 0
        w = max(lines_width(main, t.tile, "semibold") + icon, lines_width(sub, t.tile_sub)) + 2 * t.pad
        h = t.tile_h + (len(main) - 1) * t.line_h + len(sub) * (t.line_h - 1.5)
        return max(w, self.width or 0) + t.depth, h + t.depth

    def draw(self, c, x, y, w, h, t, report):
        st = t.status(self.status)
        fill, stroke = (st.fill, st.stroke) if st else (t.tile_fill, t.tile_stroke)
        dash = st.dash if st else None
        need = self.measure(t)[0]
        if need > w + 0.5:
            report(f"tile {self.label!r} needs {need:.0f} px but has {w:.0f} px")
        d = t.depth
        if d:
            # The raised look: a thin top face and right face behind the front face.
            top = (f"M{fmt(x)} {fmt(y + d)}L{fmt(x + d)} {fmt(y)}H{fmt(x + w)}"
                   f"L{fmt(x + w - d)} {fmt(y + d)}Z")
            side = (f"M{fmt(x + w - d)} {fmt(y + d)}L{fmt(x + w)} {fmt(y)}V{fmt(y + h - d)}"
                    f"L{fmt(x + w - d)} {fmt(y + h)}Z")
            c.path(top, fill=shade(fill, 0.05), stroke=stroke, width=0.8, dash=dash)
            c.path(side, fill=shade(fill, 0.15), stroke=stroke, width=0.8, dash=dash)
            y, w, h = y + d, w - d, h - d
        c.rect(x, y, w, h, fill, stroke, 1.1, 2 if d else 4, dash)
        main, sub = self._lines(t)
        steps = [t.line_h] * (len(main) - 1) + [t.line_h - 1.5] * len(sub)
        centres = [y + h / 2 - sum(steps) / 2]
        for s in steps:
            centres.append(centres[-1] + s)
        icon = ICON + 6 if self.icon else 0
        for i, line in enumerate(main):
            cy = centres[i]
            lw = text_width(line, t.tile, "semibold") + (icon if i == 0 else 0)
            lx = x + w / 2 - lw / 2
            if i == 0 and self.icon:
                c.image(_data_uri(self.icon), lx, cy - ICON / 2, ICON, ICON)
                lx += icon
            c.text(line, lx, cy + cap_height(t.tile, "semibold") / 2, t.tile, "semibold", t.ink)
        for line, cy in zip(sub, centres[len(main):]):
            c.text_centered(line, x + w / 2, cy, t.tile_sub, "regular", t.muted)

    def statuses(self):
        # A tile with no status is drawn in the default (live) style, so the key lists it as such.
        return {self.status or ""}


TileLike = Union[Tile, str]


def as_tile(item: TileLike) -> Tile:
    return item if isinstance(item, Tile) else Tile(str(item))


class Tiles(Block):
    """A grid of tiles with one cell size. A short last row is centred. An optional label sits above."""

    def __init__(self, items: Sequence[TileLike], cols: Optional[int] = None, label: Optional[str] = None):
        if not items:
            raise ValueError("Tiles needs at least one item")
        self.items = [as_tile(i) for i in items]
        self.cols = max(1, min(cols or 3, len(self.items)))
        self.label = label

    def _cell(self, t: Theme) -> Tuple[float, float]:
        sizes = [i.measure(t) for i in self.items]
        return max(s[0] for s in sizes), max(s[1] for s in sizes)

    def _label_h(self, t: Theme) -> float:
        return t.line_h + 4 if self.label else 0

    def measure(self, t):
        cw, ch = self._cell(t)
        rows = math.ceil(len(self.items) / self.cols)
        w = self.cols * cw + (self.cols - 1) * t.tile_gap
        if self.label:
            w = max(w, text_width(self.label, t.small, "semibold"))
        return w, self._label_h(t) + rows * ch + (rows - 1) * t.tile_gap

    def draw(self, c, x, y, w, h, t, report):
        _, ch = self._cell(t)
        g = t.tile_gap
        cw = (w - (self.cols - 1) * g) / self.cols
        if self.label:
            c.text(self.label, x, y + 11, t.small, "semibold", t.muted)
        top = y + self._label_h(t)
        for start in range(0, len(self.items), self.cols):
            row = self.items[start:start + self.cols]
            row_w = len(row) * cw + (len(row) - 1) * g
            rx = x + (w - row_w) / 2
            for item in row:
                item.draw(c, rx, top, cw, ch, t, report)
                rx += cw + g
            top += ch + g

    def statuses(self):
        return set().union(*(i.statuses() for i in self.items))


# ---------------------------------------------------------------------------------------------- text and cards

class Text(Block):
    """A paragraph, wrapped to a maximum width."""

    def __init__(self, text: str, size: Optional[float] = None, weight: str = "regular", color: Optional[str] = None,
                 max_width: float = 320):
        self.text, self.size, self.weight, self.color, self.max_width = text, size, weight, color, max_width

    def _lines(self, t):
        return wrap(self.text, self.size or t.body, self.max_width, self.weight)

    def measure(self, t):
        lines = self._lines(t)
        return lines_width(lines, self.size or t.body, self.weight), len(lines) * t.line_h

    def draw(self, c, x, y, w, h, t, report):
        size = self.size or t.body
        for i, line in enumerate(self._lines(t)):
            c.text(line, x, y + t.line_h * i + t.line_h / 2 + cap_height(size) / 2, size, self.weight,
                   self.color or t.ink)


class Card(Block):
    """A worked example: a title, an optional intro line, then rows of name and value."""

    def __init__(self, title: str, rows: Sequence[Tuple[str, str]], intro: Optional[str] = None,
                 max_width: float = 380):
        self.title, self.rows, self.intro, self.max_width = title, list(rows), intro, max_width

    def _layout(self, t):
        key_w = max((text_width(k, t.body, "semibold") for k, _ in self.rows), default=0)
        room = self.max_width - 2 * t.pad
        values = [wrap(v, t.body, room - key_w - 14) for _, v in self.rows]
        intro = wrap(self.intro, t.body, room) if self.intro else []
        return key_w, values, intro

    def measure(self, t):
        key_w, values, intro = self._layout(t)
        inner = max(text_width(self.title, t.tile, "semibold"), lines_width(intro, t.body),
                    key_w + 14 + max((lines_width(v, t.body) for v in values), default=0))
        lines = 1 + len(intro) + sum(len(v) for v in values)
        return inner + 2 * t.pad, 2 * t.pad + lines * t.line_h + (4 if intro else 0) + 4

    def draw(self, c, x, y, w, h, t, report):
        key_w, values, intro = self._layout(t)
        c.rect(x, y, w, h, t.tile_fill, t.panel_stroke, 1, 4)

        def base(row):
            return y + t.pad + row * t.line_h + t.line_h / 2 + cap_height(t.body) / 2

        c.text(self.title, x + t.pad, base(0), t.tile, "semibold", t.ink)
        row, extra = 1, 4
        for line in intro:
            c.text(line, x + t.pad, base(row) + 2, t.body, "regular", t.muted)
            row += 1
        if intro:
            extra += 4
        for (key, _), lines in zip(self.rows, values):
            c.text(key, x + t.pad, base(row) + extra, t.body, "semibold", t.ink)
            for line in lines:
                c.text(line, x + t.pad + key_w + 14, base(row) + extra, t.body, "regular", t.ink)
                row += 1


class Note(Block):
    """A boxed note for the top right of a diagram, such as 'Draft' with a line or two under it."""

    def __init__(self, title: str, *lines: str, max_width: float = 330):
        self.title, self.lines, self.max_width = title, list(lines), max_width

    def _wrapped(self, t):
        out = []
        for line in self.lines:
            out += wrap(line, t.body, self.max_width - 2 * t.pad)
        return out

    def measure(self, t):
        lines = self._wrapped(t)
        w = max(text_width(self.title, 13, "semibold"), lines_width(lines, t.body)) + 2 * t.pad
        return w, 2 * t.pad + 18 + len(lines) * t.line_h

    def draw(self, c, x, y, w, h, t, report):
        c.rect(x, y, w, h, t.note_fill, t.note_stroke, 1.2, t.radius)
        c.text(self.title, x + t.pad, y + t.pad + 12, 13, "semibold", t.ink)
        for i, line in enumerate(self._wrapped(t)):
            c.text(line, x + t.pad, y + t.pad + 18 + t.line_h * i + 11, t.body, "regular", t.muted)


# ----------------------------------------------------------------------------------------------------- graph

class Graph(Block):
    """A small map of things and how they connect: nodes on a grid, with a labelled line between pairs.

    nodes: {key: label}. links: [(from_key, to_key, label_or_None)]. at: {key: (column, row)}; fractions allowed.
    The build reports any line label that touches a node or another label, and any line that runs through a node.
    """

    NODE_H = 26.0
    MARGIN = 16.0

    def __init__(self, nodes: Dict[str, str], links: Iterable[Sequence], at: Dict[str, Tuple[float, float]],
                 spacing: Tuple[float, float] = (132, 58)):
        self.nodes = dict(nodes)
        self.links = [tuple(l) + (None,) * (3 - len(l)) for l in links]
        self.at = dict(at)
        self.spacing = spacing
        missing = [k for k in self.nodes if k not in self.at]
        if missing:
            raise ValueError(f"Graph: no position given for {', '.join(missing)}")
        for a, b, _ in self.links:
            for k in (a, b):
                if k not in self.nodes:
                    raise ValueError(f"Graph: link names unknown node {k!r}")

    def _node_w(self, t, key):
        return text_width(self.nodes[key], t.body, "semibold") + 26

    def _boxes(self, t) -> Dict[str, Tuple[float, float, float, float]]:
        sx, sy = self.spacing
        boxes = {}
        for k in self.nodes:
            col, row = self.at[k]
            w = self._node_w(t, k)
            boxes[k] = (col * sx - w / 2, row * sy - self.NODE_H / 2, w, self.NODE_H)
        return boxes

    def _extent(self, t):
        boxes = self._boxes(t).values()
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[0] + b[2] for b in boxes)
        y1 = max(b[1] + b[3] for b in boxes)
        return x0, y0, x1, y1

    def measure(self, t):
        x0, y0, x1, y1 = self._extent(t)
        return x1 - x0 + 2 * self.MARGIN, y1 - y0 + 2 * self.MARGIN

    def draw(self, c, x, y, w, h, t, report):
        c.rect(x, y, w, h, t.graph_fill, t.panel_stroke, 0.8, 4)
        gx = x + 18
        while gx < x + w - 1:
            c.line(gx, y + 1, gx, y + h - 1, t.graph_grid, 0.6)
            gx += 18
        gy = y + 18
        while gy < y + h - 1:
            c.line(x + 1, gy, x + w - 1, gy, t.graph_grid, 0.6)
            gy += 18
        x0, y0, x1, y1 = self._extent(t)
        ox = x + (w - (x1 - x0)) / 2 - x0
        oy = y + (h - (y1 - y0)) / 2 - y0
        boxes = {k: (bx + ox, by + oy, bw, bh) for k, (bx, by, bw, bh) in self._boxes(t).items()}
        centres = {k: (b[0] + b[2] / 2, b[1] + b[3] / 2) for k, b in boxes.items()}
        labels = []
        for a, b, label in self.links:
            (ax, ay), (bx, by) = centres[a], centres[b]
            p, q = _clip(boxes[a], (ax, ay), (bx, by)), _clip(boxes[b], (bx, by), (ax, ay))
            c.line(p[0], p[1], q[0], q[1], t.graph_line, 1)
            for k, box in boxes.items():
                if k not in (a, b) and _segment_hits(box, p, q):
                    report(f"graph: the line {self.nodes[a]!r} to {self.nodes[b]!r} runs through {self.nodes[k]!r}")
            if label:
                lw = text_width(label, t.small) + 12
                mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
                labels.append((label, (mx - lw / 2, my - 8, lw, 16)))
        for k, (bx, by, bw, bh) in boxes.items():
            c.rect(bx, by, bw, bh, t.tile_fill, t.ink, 1, bh / 2)
            c.text_centered(self.nodes[k], bx + bw / 2, by + bh / 2, t.body, "semibold", t.ink)
        for i, (label, box) in enumerate(labels):
            for k, nb in boxes.items():
                if _overlap(box, nb, 2):
                    report(f"graph: the label {label!r} touches the node {self.nodes[k]!r}")
            for other, ob in labels[i + 1:]:
                if _overlap(box, ob, 2):
                    report(f"graph: the labels {label!r} and {other!r} touch")
            c.rect(*box, t.paper, t.graph_line, 0.7, 8)
            c.text_centered(label, box[0] + box[2] / 2, box[1] + 8, t.small, "regular", t.muted)


def _clip(box, inside, toward):
    """Point where the line from the box centre toward another point leaves the box, plus a 2 px gap."""
    bx, by, bw, bh = box
    dx, dy = toward[0] - inside[0], toward[1] - inside[1]
    hw, hh = bw / 2 + 2, bh / 2 + 2
    s = min(hw / abs(dx) if dx else math.inf, hh / abs(dy) if dy else math.inf)
    return inside[0] + dx * s, inside[1] + dy * s


def _overlap(a, b, pad=0.0) -> bool:
    return (a[0] < b[0] + b[2] + pad and b[0] < a[0] + a[2] + pad and
            a[1] < b[1] + b[3] + pad and b[1] < a[1] + a[3] + pad)


def _segment_hits(box, p, q, steps=40) -> bool:
    bx, by, bw, bh = box
    for i in range(1, steps):
        s = i / steps
        x, y = p[0] + (q[0] - p[0]) * s, p[1] + (q[1] - p[1]) * s
        if bx + 1 < x < bx + bw - 1 and by + 1 < y < by + bh - 1:
            return True
    return False


# ------------------------------------------------------------------------------------------------------- rows

class Row(Block):
    """Blocks side by side, tops aligned. Extra width goes to the last block."""

    def __init__(self, *items: "BlockLike", gap: Optional[float] = None):
        self.items = [as_block(i) for i in items]
        self.gap = gap

    def measure(self, t):
        g = t.section_gap if self.gap is None else self.gap
        sizes = [i.measure(t) for i in self.items]
        return sum(s[0] for s in sizes) + g * (len(sizes) - 1), max(s[1] for s in sizes)

    def draw(self, c, x, y, w, h, t, report):
        g = t.section_gap if self.gap is None else self.gap
        sizes = [i.measure(t) for i in self.items]
        extra = w - (sum(s[0] for s in sizes) + g * (len(sizes) - 1))
        cx = x
        for n, (item, (iw, ih)) in enumerate(zip(self.items, sizes)):
            if n == len(self.items) - 1:
                iw += extra
            item.draw(c, cx, y, iw, ih, t, report)
            cx += iw + g

    def statuses(self):
        return set().union(*(i.statuses() for i in self.items))


# ------------------------------------------------------------------------------------------------------ panel

BlockLike = Union[Block, str, Sequence[TileLike]]


def as_block(item: BlockLike) -> Block:
    if isinstance(item, Block):
        return item
    if isinstance(item, str):
        return Text(item)
    return Tiles(list(item))


def _top_rounded(x, y, w, h, r) -> str:
    return (f"M{fmt(x)} {fmt(y + h)}V{fmt(y + r)}Q{fmt(x)} {fmt(y)} {fmt(x + r)} {fmt(y)}"
            f"H{fmt(x + w - r)}Q{fmt(x + w)} {fmt(y)} {fmt(x + w)} {fmt(y + r)}V{fmt(y + h)}Z")


def _panel_frame(c, x, y, w, h, t, tone, fill, stroke, width=1, dash=None):
    """The shared sloped lid and filled body of a panel or resource container."""
    lid = t.lid
    if lid:
        inset = min(lid * 0.7, w / 4)
        c.path(f"M{fmt(x)} {fmt(y + lid)}L{fmt(x + inset)} {fmt(y)}H{fmt(x + w - inset)}"
               f"L{fmt(x + w)} {fmt(y + lid)}Z", fill=shade(tone, 0.16), stroke=shade(tone, 0.32), width=0.8)
        y, h = y + lid, h - lid
    c.rect(x, y, w, h, fill, stroke, width, 2 if lid else t.radius, dash)
    return y, h


class Panel(Block):
    """The main block: a colored header with a title, then sections stacked inside, then an optional footer.

    Sections can be Tiles, Card, Graph, Text, Row, a plain list of labels (made into Tiles) or a string (Text).
    status: shows the panel border in that status's style and puts the status word in the header.
    step: a number in a circle before the title, to show which change comes first.
    footer: small text under a rule, for example "Owner: Data team". Text before the first colon is bold.
    tone: header color, a key of theme.tones or a hex color.
    """

    def __init__(self, title: str, *body: BlockLike, sub: Optional[str] = None, status: Optional[str] = None,
                 step: Optional[int] = None, footer: Optional[str] = None, tone: str = "default",
                 width: Optional[float] = None, name: Optional[str] = None):
        self.title, self.sub, self.status, self.step, self.footer = title, sub, status, step, footer
        self.body = [as_block(b) for b in body]
        self.tone, self.width, self.name = tone, width, name or title

    def head_h(self, t):
        return t.header_h_sub if self.sub else t.header_h

    def _badge_w(self):
        return 30 if self.step is not None else 0

    def _tag(self, t):
        st = t.status(self.status)
        if not st:
            return None, 0.0
        return st, text_width(st.label, t.small, "semibold") + 16

    def _footer_lines(self):
        return self.footer.split("\n") if self.footer else []

    def _footer_h(self, t):
        n = len(self._footer_lines())
        return 8 + n * t.line_h + 6 if n else 0

    def measure(self, t):
        _, tag_w = self._tag(t)
        head = t.pad + self._badge_w() + text_width(self.title, t.panel_title, "semibold") + \
            (12 + tag_w if tag_w else 0) + t.pad
        sub = t.pad + self._badge_w() + text_width(self.sub, t.panel_sub) + t.pad if self.sub else 0
        sizes = [b.measure(t) for b in self.body]
        body_w = max((s[0] for s in sizes), default=0)
        body_h = sum(s[1] for s in sizes) + t.section_gap * max(0, len(sizes) - 1)
        foot = lines_width(self._footer_lines(), t.small) + 2 * t.pad + 4
        w = max(head, sub, body_w + 2 * t.pad, foot, t.panel_min_w, self.width or 0)
        h = t.lid + self.head_h(t) + (2 * t.pad + body_h if sizes else t.pad) + self._footer_h(t)
        return w, h

    def draw(self, c, x, y, w, h, t, report):
        st = t.status(self.status)
        hh = self.head_h(t)
        tone = t.tone(self.tone)
        y, h = _panel_frame(c, x, y, w, h, t, tone, st.fill if st else t.panel_fill,
                            st.stroke if st else t.panel_stroke, 1.3 if st else 1, st.dash if st else None)
        if t.lid:
            c.rect(x, y, w, hh, tone)
        else:
            c.path(_top_rounded(x, y, w, hh, t.radius), fill=tone)
        title_color, sub_color = t.header_colors(tone)
        tx = x + t.pad
        title_cy = y + (18 if self.sub else hh / 2)
        if self.step is not None:
            c.circle(tx + 11, title_cy, 10.5, t.badge_fill or t.paper)
            c.text_centered(str(self.step), tx + 11, title_cy, 11.5, "bold", t.badge_text or tone)
            tx += self._badge_w()
        c.text_centered(self.title, tx + text_width(self.title, t.panel_title, "semibold") / 2, title_cy,
                        t.panel_title, "semibold", title_color)
        if self.sub:
            c.text(self.sub, tx, y + 36 + cap_height(t.panel_sub) / 2, t.panel_sub, "regular", sub_color)
        tag, tag_w = self._tag(t)
        if tag:
            c.rect(x + w - t.pad - tag_w, title_cy - 9, tag_w, 18, t.paper, None, radius=9)
            c.text_centered(tag.label, x + w - t.pad - tag_w / 2, title_cy, t.small, "semibold", tag.stroke)
        cy = y + hh + t.pad
        for block in self.body:
            bw, bh = block.measure(t)
            block.draw(c, x + t.pad, cy, w - 2 * t.pad, bh, t, report)
            cy += bh + t.section_gap
        lines = self._footer_lines()
        if lines:
            fy = y + h - self._footer_h(t)
            c.line(x + t.pad, fy, x + w - t.pad, fy, t.panel_stroke, 0.8)
            for i, line in enumerate(lines):
                base = fy + 8 + t.line_h * i + t.line_h / 2 + cap_height(t.small) / 2
                head, colon, rest = line.partition(":")
                if colon and len(head) < 40:
                    hw = c.text(head + ":", x + t.pad, base, t.small, "semibold", t.ink)
                    c.text(rest, x + t.pad + hw, base, t.small, "regular", t.muted)
                else:
                    c.text(line, x + t.pad, base, t.small, "regular", t.muted)

    def statuses(self):
        found = {self.status} if self.status else set()
        return found.union(*(b.statuses() for b in self.body))

    def ports(self, side, w, h, t):
        if side in ("left", "right"):
            return t.lid + self.head_h(t) + 8, h - 10
        return 18, w - 18
