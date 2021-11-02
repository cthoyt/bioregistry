# -*- coding: utf-8 -*-

"""Export components of the bioregistry to YAML."""

import click
import yaml

from ..constants import DOCS_DATA
from ..resolve import manager
from ..schema import sanitize_mapping
from ..utils import read_collections, read_metaregistry

REGISTRY_YAML_PATH = DOCS_DATA / "registry.yml"
METAREGISTRY_YAML_PATH = DOCS_DATA / "metaregistry.yml"
COLLECTIONS_YAML_PATH = DOCS_DATA / "collections.yml"


@click.command()
def export_yaml():
    """Export the registry as YAML."""
    registry = manager.rasterize()
    metaregistry = sanitize_mapping(read_metaregistry())
    collections = sanitize_mapping(read_collections())

    with REGISTRY_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=registry)
    with METAREGISTRY_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=metaregistry)
    with COLLECTIONS_YAML_PATH.open("w") as file:
        yaml.safe_dump(stream=file, data=collections)


if __name__ == "__main__":
    export_yaml()
