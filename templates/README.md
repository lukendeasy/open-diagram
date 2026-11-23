# Cloud resource templates

Start here for resource topology and ETL DAGs. A `Resource` is a 64 px service icon with
its workload label and service name underneath. Each resource is individually addressable
by `d.link()`. Enclosures represent accounts, VPCs, subnets or logical resource groups;
they can contain other enclosures.

| Template | Purpose | Preview |
| --- | --- | --- |
| [aws_etl.py](aws_etl.py) | MWAA orchestrates three Lambda extractors; raw S3, Glue, curated S3, a catalog, Athena and QuickSight are explicit resources | [PNG](../docs/images/aws_etl.png) |
| [aws_architecture.py](aws_architecture.py) | Account, VPC and subnet boundaries around API Gateway, Lambda, RDS and S3 connectivity | [PNG](../docs/images/aws_architecture.png) |

From the checkout, after installing the package's dependencies:

```sh
PYTHONPATH=src python templates/aws_etl.py
PYTHONPATH=src python -m open_diagram check templates/aws_etl.py templates/aws_architecture.py
```

Copy a template, edit its `RESOURCES` list, then edit the links and enclosure memberships.
Keep assets beside your copy or update `ASSETS`. The cached artwork makes both templates
work without network access. [Icon credits and licenses](assets/README.md) accompany the
SVG/PNG previews. These templates are in the Git checkout, not the Python package.

## Resource nodes

```python
from open_diagram import Diagram, Resource, Theme

d = Diagram("My cloud resources", theme=Theme(link_labels={"flow": "Data flow"}))
a = d.add(Resource("API extractor", sub="AWS Lambda", icon="assets/lambda.svg"))
b = d.right_of(a, Resource("Raw data", sub="Amazon S3", icon="assets/s3.svg"))
d.link(a, b, label="objects")
extract = d.enclosure("Extraction", [a], border="dashed")
d.enclosure("Cloud account", [extract, b], border="solid", pad=40)
```

`Resource` accepts `icon_size` (default 64), `max_width` (wrapped text width, default 180),
`sub`, `name` and an optional `border` (`None`, `solid`, `dashed`, `dotted`). Missing artwork
can be represented with a text-only `Resource`; an explicitly supplied missing file raises
a named error. PNG and SVG files are embedded locally. Connections attach to an unframed
icon's edges; labels remain inside the measured node bounds.

The same API works with [Azure and GCP mappings](../cloud-icons/). Download the appropriate
provider's SVGs using the [cloud-icons workflow](../skills/cloud-icons/SKILL.md), then pass
the local paths to `Resource`. These sample architectures are AWS-specific; changing the
provider also requires choosing appropriate services and boundaries.

## Boundaries and connection styles

`d.enclosure(label, members, sub=..., pad=24, border="dashed", fill=..., stroke=...)`
returns an enclosure that can be included in a later enclosure. Members must already
belong to the same diagram. The parent includes each child's full boundary and heading.
Borders can be solid, dashed or dotted. `fill="none"` makes the area transparent; leaving
colors unset uses `Theme.group_fill` and `Theme.group_stroke`. Styling does not imply that
resources are planned or deployed. `d.group()` retains its existing shaded-group behavior.

For orchestration, add a distinct kind and style it independently of deployment status:

```python
theme = Theme(link_labels={"flow": "Data", "control": "Task control"})
# Construct the diagram with this theme, then add resources.
# d.link(mwaa, extractor, kind="control", dash="dashed")
```

Use a distinct kind for each connection's meaning. If one kind uses multiple styles, the
legend lists each style separately. Link `dash` also
works in JSON/MCP descriptions. Resource icons and nested enclosures use Python only;
JSON and Mermaid still describe panels. Positions remain explicit; this adds no automatic
DAG scheduling or layout engine. All existing overlap, crossing and label checks apply.

The ETL example illustrates a scheduled batch design. It omits source systems, IAM and
network deployment details. The architecture example shows logical VPC attachment and
service connectivity; it does not provision subnets, endpoints or access policies.
