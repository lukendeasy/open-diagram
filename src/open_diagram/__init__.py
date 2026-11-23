"""open-diagram: building blocks for dense architecture diagrams that check their own layout."""
__version__ = "0.4.0"

from .blocks import Block, Card, Graph, Note, Panel, Resource, Row, Text, Tile, Tiles  # noqa: E402
from .diagram import Diagram, LayoutError, Link, Placed, Report  # noqa: E402
from .fonts import text_width, wrap  # noqa: E402
from .mermaid import MermaidError, from_mermaid  # noqa: E402
from .render import find_chrome, svg_to_png  # noqa: E402
from .spec import SpecError, from_spec  # noqa: E402
from .theme import Status, Theme  # noqa: E402

__all__ = [
    "Block", "Card", "Diagram", "Graph", "LayoutError", "Link", "MermaidError", "Note", "Panel", "Placed", "Report",
    "Resource", "Row", "SpecError", "Status", "Text", "Theme", "Tile", "Tiles", "find_chrome", "from_mermaid", "from_spec",
    "svg_to_png", "text_width", "wrap",
]
