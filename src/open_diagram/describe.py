"""Describe a diagram in plain words: what each block holds, what connects to what, and what state each part is in.

The text serves as alt text for screen readers (it is written into the SVG as <desc>), and lets an agent check that a
picture says what was asked without looking at it.
"""
from __future__ import annotations

from typing import List, Optional

from .blocks import Block, Card, Graph, Note, Panel, Resource, Row, Text, Tile, Tiles


def _status_word(theme, key: Optional[str]) -> Optional[str]:
    if not key or key == "live":
        return None
    st = theme.statuses.get(key)
    return st.label.lower() if st else key


def _tile(theme, tile: Tile) -> str:
    extra = [x for x in (tile.sub, _status_word(theme, tile.status)) if x]
    return f"{tile.label} ({'; '.join(extra)})" if extra else tile.label


def _block(theme, block: Block) -> str:
    if isinstance(block, Resource):
        return f"{block.label} ({block.sub})" if block.sub else block.label
    if isinstance(block, Tiles):
        items = "; ".join(_tile(theme, t) for t in block.items)
        return f"{block.label}: {items}" if block.label else items
    if isinstance(block, Tile):
        return _tile(theme, block)
    if isinstance(block, Text):
        return block.text
    if isinstance(block, Card):
        rows = "; ".join(f"{k} {v}" for k, v in block.rows)
        return f"example '{block.title}': {rows}"
    if isinstance(block, Graph):
        links = "; ".join(f"{block.nodes[a]} {label or 'to'} {block.nodes[b]}" for a, b, label in block.links)
        return f"map: {links}"
    if isinstance(block, Row):
        return ". ".join(_block(theme, b) for b in block.items)
    if isinstance(block, Note):
        return " ".join([block.title + "."] + block.lines)
    return ""


def _name(placed) -> str:
    """The words a reader sees: a panel's title or a tile's label, not an internal id."""
    block = placed.block
    if isinstance(block, Panel):
        return block.title
    if isinstance(block, (Tile, Resource)):
        return block.label
    return placed.name


def _placed(theme, placed) -> str:
    block = placed.block
    if isinstance(block, Panel):
        tags = []
        if block.step is not None:
            tags.append(f"step {block.step}")
        word = _status_word(theme, block.status)
        if word:
            tags.append(word)
        head = _name(placed) + (f" [{', '.join(tags)}]" if tags else "") + (f" ({block.sub})" if block.sub else "")
        body = ". ".join(x for x in (_block(theme, b) for b in block.body) if x)
        text = f"{head}: {body}" if body else head
        if block.footer:
            text += f". {block.footer.replace(chr(10), ' ')}"
        return text
    if isinstance(block, Resource):
        return _block(theme, block)
    if isinstance(block, Tile):
        return _tile(theme, block)
    inner = _block(theme, block)
    return f"{placed.name}: {inner}" if inner else placed.name


def describe(diagram) -> str:
    """Return a plain-text description of a Diagram. Blocks are listed left to right, then top to bottom."""
    t = diagram.theme
    out: List[str] = [diagram.title]
    if diagram.subtitle:
        out.append(diagram.subtitle)
    used = {k for p in diagram.placed for k in p.block.statuses()}
    words = [t.statuses[k].label for k in t.statuses if (k in used or (k == "live" and "" in used))]
    kinds = {line.kind for line in diagram.links}
    key = []
    if words:
        key.append("States shown: " + ", ".join(words) + ".")
    for kind in t.link_labels:
        if kind in kinds:
            styles = list(dict.fromkeys((line.dash or ("dotted" if kind == "planned" else "solid")).capitalize()
                                        for line in diagram.links if line.kind == kind))
            key.append(f"{'/'.join(styles)} lines: {t.link_labels[kind].lower()}.")
    if key:
        out.append(" ".join(key))
    if diagram.steps:
        owners = {}
        for p in diagram.placed:
            step = getattr(p.block, "step", None)
            if step is not None:
                owners.setdefault(step, _name(p))
        parts = [f"{n}. {text}" + (f" ({owners[n]})" if n in owners else "") for n, text in diagram.steps]
        out.append(f"{diagram.steps_label}: " + "; ".join(parts) + ".")
    out.append("")
    out.append("Blocks, left to right:")
    for p in sorted(diagram.placed, key=lambda p: (round(p.x), round(p.y))):
        out.append(f"- {_placed(t, p)}")
    if diagram.groups:
        out.append("Groups:")
        for g in diagram.groups:
            sub = f" ({g.sub})" if g.sub else ""
            out.append(f"- {g.label}{sub}: " + ", ".join(_name(m) for m in g.members))
    if diagram.links:
        out.append("Lines:")
        for line in diagram.links:
            text = f"- {_name(line.a)} -> {_name(line.b)}"
            if line.kind == "planned":
                text += f" ({t.link_labels['planned'].lower()})"
            if line.label:
                text += f', labeled "{line.label}"'
            if line.dash:
                text += f" ({line.dash} line)"
            out.append(text)
    if diagram.note is not None:
        out.append("Note: " + _block(t, diagram.note))
    return "\n".join(out)
