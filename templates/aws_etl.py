"""Icon-first AWS ETL DAG. Copy this template and edit RESOURCES and connections.
Run from the repository: PYTHONPATH=src python templates/aws_etl.py
"""
from pathlib import Path

from open_diagram import Diagram, Note, Resource, Theme

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets" / "aws"
BOUNDARY = "dashed"  # "solid", "dashed" or "dotted"; no deployment-status implication.
RESOURCES = [
    # id, workload label, service, artwork, x, y
    ("mwaa", "ETL orchestration", "Amazon MWAA", "mwaa.svg", 0, 0),
    ("api", "API extractor", "AWS Lambda", "lambda.svg", 0, 220),
    ("saas", "SaaS extractor", "AWS Lambda", "lambda.svg", 0, 380),
    ("database", "Database extractor", "AWS Lambda", "lambda.svg", 0, 540),
    ("raw", "Raw landing", "Amazon S3", "s3.svg", 300, 380),
    ("glue", "Transform + validate", "AWS Glue", "glue.svg", 600, 380),
    ("curated", "Curated Parquet", "Amazon S3", "s3.svg", 900, 380),
    ("catalog", "Table metadata", "Glue Data Catalog", "glue.svg", 900, 80),
    ("athena", "Analytics SQL", "Amazon Athena", "athena.svg", 1200, 380),
    ("dashboards", "Business dashboards", "Amazon QuickSight", "quicksight.png", 1500, 380),
]


def build() -> Diagram:
    theme = Theme(link_labels={"flow": "Data and metadata", "control": "MWAA task control"})
    d = Diagram("AWS ETL resource DAG", tag="TEMPLATE", theme=theme,
                subtitle="Separate Lambda extractors, explicit AWS resources, and nested account boundaries.",
                note=Note("Illustrative workload", "Fictional account; no deployed resources", "Dashed arrows: orchestration"))
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
    d.link(nodes["catalog"], nodes["athena"], start="right", end="top", label="schema")

    for index, resource in enumerate(extractors):
        d.link(nodes["mwaa"], resource, kind="control", dash="dashed",
               start="left", end="left", via_x=-36 - 16 * index)
    d.link(nodes["mwaa"], nodes["glue"], kind="control", dash="dashed",
           label="after extraction", start="right", end="top", via_y=180)

    extraction = d.enclosure("Lambda extraction tasks", extractors, border=BOUNDARY, fill=theme.paper)
    lake = d.enclosure("Curated lake + catalog", [nodes["curated"], nodes["catalog"]],
                       border=BOUNDARY, fill=theme.paper)
    serving = d.enclosure("Analytics and visualization", [nodes["athena"], nodes["dashboards"]],
                          border=BOUNDARY, fill=theme.paper)
    d.enclosure("AWS account", [extraction, lake, serving, nodes["mwaa"], nodes["raw"], nodes["glue"]],
                sub="Logical service boundaries; networking and IAM omitted", pad=64, border=BOUNDARY,
                fill=theme.paper, stroke=theme.line)
    return d


if __name__ == "__main__":
    build().save(str(HERE.parent / "docs" / "images" / "aws_etl"))
