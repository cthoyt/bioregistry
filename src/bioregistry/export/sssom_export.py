# -*- coding: utf-8 -*-

"""Export the Bioregistry to SSSOM."""

import csv
from collections import namedtuple

import click
import yaml

import bioregistry
from bioregistry.constants import SSSOM_METADATA_PATH, SSSOM_PATH

__all__ = [
    "export_sssom",
]

Row = namedtuple("Row", "subject_id predicate_id object_id match_type")


def _get_curie_map():
    rv = {}
    for metaprefix, metaresource in bioregistry.read_metaregistry().items():
        if not metaresource.provider_uri_format:
            continue
        if metaprefix in bioregistry.read_registry() and not metaresource.bioregistry_prefix:
            print("issue with overlap", metaprefix)
            continue
        rv[metaprefix] = metaresource.provider_uri_format.rstrip("$1")
    return rv


METADATA = {
    "license": "https://creativecommons.org/publicdomain/zero/1.0/",
    "mapping_provider": "https://github.com/biopragmatics/bioregistry",
    "mapping_set_group": "bioregistry",
    "mapping_set_id": "bioregistry",
    "mapping_set_title": "Biomappings",
    "curie_map": _get_curie_map(),
}


@click.command()
def export_sssom():
    """Export the meta-registry as SSSOM."""
    rows = []
    for prefix, resource in bioregistry.read_registry().items():
        mappings = resource.get_mappings()
        for metaprefix, metaidentifier in mappings.items():
            rows.append(_make_row("bioregistry", prefix, metaprefix, metaidentifier))
    with SSSOM_PATH.open("w") as file:
        writer = csv.writer(file, delimiter="\t")
        writer.writerow(Row._fields)
        writer.writerows(rows)
    with SSSOM_METADATA_PATH.open("w") as file:
        yaml.safe_dump(METADATA, file)


def _make_row(mp1: str, mi1: str, mp2: str, mi2: str) -> Row:
    return Row(
        subject_id=f"{mp1}:{mi1}",
        predicate_id="skos:exactMatch",
        object_id=f"{mp2}:{mi2}",
        match_type="sssom:HumanCurated",
    )


if __name__ == "__main__":
    export_sssom()
