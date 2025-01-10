"""Validation command line interface.

JSON-LD Validation

1. Passes ``bioregistry validate jsonld "https://bioregistry.io/api/collection/0000002?format=context"``
1. Fails ``bioregistry validate jsonld "https://raw.githubusercontent.com/prefixcommons/prefixcommons-py/master/prefixcommons/registry/go_context.jsonld"``
2.
"""

import json
import sys
from pathlib import Path

import click
import requests

from .utils import validate_jsonld

__all__ = [
    "validate",
]


@click.group()
def validate():
    """Validate data with the Bioregistry."""


@validate.command()
@click.argument("location")
@click.option("--relax", is_flag=True)
def jsonld(location: str, relax: bool):
    """Validate a JSON-LD file."""
    if location.startswith("http://") or location.startswith("https://"):
        res = requests.get(location)
        res.raise_for_status()
        obj = res.json()
    else:
        path = Path(location).resolve()
        if not path.is_file():
            raise ValueError
        obj = json.loads(path.read_text())

    messages = validate_jsonld(obj, strict=not relax)
    for message in messages:
        error, prefix, solution, level = (
            message["error"],
            message["prefix"],
            message["solution"],
            message["level"],
        )
        click.secho(f"{prefix} - {error}", fg=LEVEL_TO_COLOR[level], nl=False)
        if solution:
            click.echo(" > " + solution)
        else:
            click.echo("")

    if any(message["level"] == "error" for message in messages):
        click.secho("failed", fg="red")
        sys.exit(1)


LEVEL_TO_COLOR = {
    "warning": "yellow",
    "error": "red",
}
