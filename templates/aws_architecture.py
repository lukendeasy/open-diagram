"""Cloud connectivity template with account, VPC and subnet enclosures.
Run from the repository: PYTHONPATH=src python templates/aws_architecture.py
"""
from pathlib import Path

from open_diagram import Diagram, Note, Resource, Theme

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets" / "aws"
RESOURCES = [
    ("gateway", "Public API", "Amazon API Gateway", "api-gateway.svg", 0, 240),
    ("function", "Application function", "VPC-connected Lambda", "lambda.svg", 320, 240),
    ("database", "Application database", "Amazon RDS", "rds.svg", 620, 240),
    ("objects", "Object storage", "Amazon S3", "s3.svg", 940, 240),
]


def build() -> Diagram:
    theme = Theme(link_labels={"flow": "Service connectivity"})
    d = Diagram("Cloud resources and connectivity", tag="TEMPLATE", theme=theme,
                subtitle="Large resource icons inside account, network and subnet enclosures.",
                note=Note("Illustrative workload", "Fictional account; no deployed resources", "Border styles are independently selectable"))
    nodes = {
        key: d.add(Resource(label, sub=service, icon=str(ASSETS / artwork), name=key), x, y)
        for key, label, service, artwork, x, y in RESOURCES
    }
    app = d.enclosure("Application subnet", [nodes["function"]], border="dotted", fill=theme.paper)
    data = d.enclosure("Database subnet", [nodes["database"]], border="dotted", fill=theme.paper)
    vpc = d.enclosure("VPC", [app, data], pad=24, border="dashed", fill=theme.paper)
    d.enclosure("AWS account", [nodes["gateway"], vpc, nodes["objects"]],
                border="solid", pad=40, fill=theme.paper, stroke=theme.line)
    d.link(nodes["gateway"], nodes["function"], label="invoke")
    d.link(nodes["function"], nodes["database"], label="SQL")
    d.link(nodes["function"], nodes["objects"], label="objects", start="right", end="top", via_y=185)
    return d


if __name__ == "__main__":
    build().save(str(HERE.parent / "docs" / "images" / "aws_architecture"))
