---
name: cloud-icons
description: Select consistent AWS, Azure, and Google Cloud service icons from pinned SVG links and embed them in open-diagram architecture, deployment, network, and data-flow diagrams.
---

# Cloud icons

The mappings live separately from this skill in the repository's top-level `cloud-icons/` directory:

| Provider | Mapping file |
| --- | --- |
| AWS | [cloud-icons/aws.json](../../cloud-icons/aws.json) |
| Azure | [cloud-icons/azure.json](../../cloud-icons/azure.json) |
| GCP | [cloud-icons/gcp.json](../../cloud-icons/gcp.json) |

Each file maps service keys directly to SVG URLs, without a provider wrapper. For example, the `s3` entry in
`aws.json` is the Amazon S3 icon. Read the selected provider's keys before choosing services; do not construct URLs
from names.

## Choose icons that explain the diagram

| Diagram | Useful choices |
| --- | --- |
| Application or deployment | Compute, containers, registry, database, storage |
| Network or security | VPC / virtual network, load balancer, gateway, DNS, identity, key management |
| Events or data pipeline | Queue, topic, event bus, data processing, database, analytics |
| AI application | Bedrock, Azure OpenAI, or Vertex AI, plus the services actually in the request |
| Multi-cloud | Select each service from its own provider group; group panels by cloud and keep labels explicit |

Use a service icon when the request names that service. For abstract concepts such as "backend", unspecified
clouds, or services absent from the mapping, use labeled resources or tiles without icons. Do not infer a provider or replace a
missing service with a different product's logo. The Azure `block-blob` key is specifically a **Block Blob** resource
in Blob Storage; `event-grid` uses the Event Grid Topics symbol. Label those resources accordingly.

Keep one icon family per provider. Preserve colors, orientation and proportions, with the product name beside or below
each icon. For cloud topology or an ETL DAG, prefer `Resource(icon=...)`: it draws a 64 px standalone icon with labels
underneath, and every resource can connect independently. Start with the repository's
[cloud templates](../../templates/README.md); use `d.enclosure()` for nested accounts, networks and logical groups,
with `border="solid"`, `"dashed"` or `"dotted"`. For dense panel summaries, `Tile` retains its 16 px icon box.
Use spacing and labels to unify a multi-cloud picture.

## Download first, then embed local files

`Resource(icon=...)` and `Tile(icon=...)` accept local PNG or SVG paths, not HTTP URLs. The Python API is the icon workflow: JSON tile
specs, Mermaid input and MCP tools do not accept an icon field. Keep using those formats for diagrams without icons.

The mapping files stay in the repository even when the skill is copied to an agent's skills folder. Neither the
skill nor the mappings are bundled in the Python package. In the example below, run from the repository root;
when running elsewhere, set `ICON_DIR` to the checkout's `cloud-icons/` directory (or a separate copy of those three
JSON files). Set `ASSET_DIR` to a local directory for this diagram's downloaded assets. All imports and asset
preparation belong at module scope, before `build()`.

```python
import hashlib
import json
from pathlib import Path
import warnings
from urllib.request import urlopen
import xml.etree.ElementTree as ET

from open_diagram import Diagram, Panel, Tile

ICON_DIR = Path("cloud-icons").resolve()
ASSET_DIR = Path("out/cloud-icons/assets")
ICONS = {
    provider: json.loads((ICON_DIR / f"{provider}.json").read_text(encoding="utf-8"))
    for provider in ("aws", "azure", "gcp")
}


def icon_file(provider, service):
    url = ICONS.get(provider, {}).get(service)
    if url is None:
        warnings.warn(f"No mapped icon for {provider}/{service}; using a text-only tile")
        return None
    # Including the URL in the filename avoids reusing an older snapshot's artwork.
    version = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    path = ASSET_DIR / provider / f"{service}-{version}.svg"
    try:
        if path.is_file():
            data = path.read_bytes()
        else:
            with urlopen(url, timeout=20) as response:
                data = response.read()
        if ET.fromstring(data).tag != "{http://www.w3.org/2000/svg}svg":
            raise ValueError("the icon response is not SVG")
        if not path.is_file():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        return str(path)
    except (OSError, ValueError, ET.ParseError) as error:
        warnings.warn(f"Icon {provider}/{service} unavailable: {error}; using a text-only tile")
        return None


GATEWAY_ICON = icon_file("aws", "api-gateway")
FUNCTION_ICON = icon_file("aws", "lambda")
DATABASE_ICON = icon_file("aws", "rds")


def build():
    d = Diagram("Example service flow", subtitle="Illustrative architecture")
    (edge,), (app,), (data,) = d.columns([
        [Panel("Public edge", [Tile("API Gateway", icon=GATEWAY_ICON)])],
        [Panel("Application", [Tile("Lambda", icon=FUNCTION_ICON)])],
        [Panel("Data store", [Tile("RDS", icon=DATABASE_ICON)])],
    ])
    d.link(edge, app)
    d.link(app, data)
    return d


if __name__ == "__main__":
    build().save("out/cloud-icons/service-flow")
```

The example uses compact panel tiles. For a resource diagram, pass those same downloaded paths to `Resource` and
place them individually, then connect the returned placements and add enclosures. Enclosure borders and optional
link `dash="dashed"` are visual styles; do not assign `status="planned"` or `kind="planned"` just to obtain dashes.
Give orchestration its own theme line kind, such as `control`, so the key explains the connection's meaning.

The URL is the download source. During rendering, open-diagram embeds each local SVG as a base64 data URI in the
compiled SVG. PNG generation uses that embedded image, so sharing either output does not require the recipient to
reach the icon host. Keep the local assets to rebuild offline; rendering an existing downloaded icon needs no network.

If a download fails, tell the user which service is missing and retain its text label. Do not silently present a
text-only diagram as if all icons loaded. An invalid cached SVG also produces a warning; remove that file before
retrying its download. A pinned URL fixes the selected content version, not the availability of the host.

After embedding, run `open-diagram check` on the script, fix every named layout problem, and inspect the PNG for
legibility and missing icons. Compare `describe()` with the requested services and connections. Use the main
[open-diagram skill](../open-diagram/SKILL.md) for the rest of the layout and review workflow when it is installed.

## Sources, family versions and attribution

The links use theSVG as a third-party host for provider architecture icons, pinned to
[commit 551229c188b4ab6e2d8b5763b9633ec91206d04c](https://github.com/glincker/thesvg/tree/551229c188b4ab6e2d8b5763b9633ec91206d04c).
Every selected file belongs to that provider's collection, uses its `default` variant, and has the catalog's
`2026-Q1` collection version. These labels describe the catalog snapshot, not the providers' latest releases.

| Provider | Selected family | Official source and guidance |
| --- | --- | --- |
| AWS | Colored service architecture icons, square backgrounds | [AWS architecture icons](https://aws.amazon.com/architecture/icons/) |
| Azure | Colored Azure architecture/portal service and resource icons | [Azure architecture icons and terms](https://learn.microsoft.com/en-us/azure/architecture/icons/) |
| GCP | Blue console/product icon family | [Google Cloud icon library](https://cloud.google.com/icons) |

Google also offers a refreshed 2025 core/category family. This mapping consistently uses the blue family available
in the pinned catalog; do not mix the two families within a GCP diagram. Some keys retain names from that snapshot,
such as `cloud-functions` and `cache-for-redis`; do not imply that the artwork represents a newer product edition.

Provider artwork and trademarks retain their own terms; the repository's MIT license does not relicense them.
The catalog identifies AWS assets as [CC BY-ND 2.0](https://creativecommons.org/licenses/by-nd/2.0/); credit Amazon Web
Services and link to the AWS source and license when distributing diagrams using them. Follow Microsoft's icon
terms for Azure and Google's applicable guidance for GCP. Preserve required notices and credit the icon owner and
source alongside shared SVG/PNG files. See also the catalog's
[legal notice](https://github.com/glincker/thesvg/blob/551229c188b4ab6e2d8b5763b9633ec91206d04c/LEGAL.md).

To refresh the mapping, use Exa to locate the official catalogs and Firecrawl to extract their download links and
guidance. Enumerate the candidate host's actual files and metadata, select one family per provider, and pin a full
commit SHA. Fetch every changed URL, confirm that it returns an SVG, and render samples before replacing links.
Update the family/version notes together with the mapping. No Firecrawl or Exa credentials are needed to use the
existing links or render downloaded assets.
