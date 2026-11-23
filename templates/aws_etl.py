"""AWS ETL resources in pastel sections with the original OpenDiagram panel depth.
Run from the repository: PYTHONPATH=src python templates/aws_etl.py
"""
from pathlib import Path

from open_diagram import Diagram, Resource, Theme

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets" / "aws"
BOUNDARY = "solid"  # "solid", "dashed" or "dotted"; no deployment-status implication.
CONTAINER = "panel"  # "panel" for sloped lids and header bands; "outline" for simple boundaries.
RESOURCES = [
    # id, workload label, service, artwork, x, y
    ("mwaa", "ETL orchestration", "Amazon MWAA", "mwaa.svg", 0, 0),
    ("api", "API extractor", "AWS Lambda", "lambda.svg", 0, 240),
    ("saas", "SaaS extractor", "AWS Lambda", "lambda.svg", 0, 400),
    ("database", "Database extractor", "AWS Lambda", "lambda.svg", 0, 560),
    ("raw", "Raw landing", "Amazon S3", "s3.svg", 300, 400),
    ("glue", "Transform + validate", "AWS Glue", "glue.svg", 600, 400),
    ("curated", "Curated Parquet", "Amazon S3", "s3.svg", 900, 400),
    ("catalog", "Table metadata", "Glue Data Catalog", "glue.svg", 900, 80),
    ("athena", "Analytics SQL", "Amazon Athena", "athena.svg", 1200, 400),
    ("dashboards", "Business dashboards", "Amazon QuickSight", "quicksight.png", 1500, 400),
]


def build() -> Diagram:
    theme = Theme(paper="#FFF9E8", panel_fill="#FFF3C8", panel_stroke="#CCB776",
                  link_labels={"flow": "Data and metadata", "control": "MWAA task control"})
    theme.tones["accent"] = "#F4DEA0"
    d = Diagram("AWS Data Ingestion with MWAA", theme=theme, legend=False)
    nodes = {
        key: d.add(Resource(label, sub=service, icon=str(ASSETS / artwork), name=key), x, y)
        for key, label, service, artwork, x, y in RESOURCES
    }
    extractors = [nodes[key] for key in ("api", "saas", "database")]
    for resource in extractors:
        d.link(resource, nodes["raw"])
    for a, b, label in (("raw", "glue", "read"), ("glue", "curated", "Parquet"),
                        ("curated", "athena", "query"), ("athena", "dashboards", "results")):
        d.link(nodes[a], nodes[b], label=label)
    d.link(nodes["curated"], nodes["catalog"], start="top", end="bottom", label="register")
    d.link(nodes["catalog"], nodes["athena"], start="right", end="top", via_x=1140, label="schema")

    for index, resource in enumerate(extractors):
        d.link(nodes["mwaa"], resource, kind="control", dash="dashed",
               start="left", end="left", via_x=-36 - 16 * index)
    d.link(nodes["mwaa"], nodes["glue"], kind="control", dash="dashed",
           label="after extraction", start="right", end="top", via_x=550)

    sections = [
        ("01  Orchestrate", [nodes["mwaa"]]),
        ("02  Extract", extractors),
        ("03  Land", [nodes["raw"]]),
        ("04  Transform", [nodes["glue"]]),
        ("05  Curate + catalog", [nodes["curated"], nodes["catalog"]]),
        ("06  Query + visualize", [nodes["athena"], nodes["dashboards"]]),
    ]
    containers = [d.enclosure(label, members, border=BOUNDARY, style=CONTAINER, tone="accent")
                  for label, members in sections]
    d.enclosure("AWS account / Data platform", containers,
                sub="Logical service sections; networking and IAM omitted", pad=64, border=BOUNDARY,
                style=CONTAINER, tone="accent", fill="#FFFCF1")
    return d


if __name__ == "__main__":
    build().save(str(HERE.parent / "docs" / "images" / "aws_etl"))
