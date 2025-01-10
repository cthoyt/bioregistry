# -*- coding: utf-8 -*-

"""Command line interface for the bioregistry."""

import sys

import click

from .app.cli import web
from .compare import compare
from .export.cli import export
from .lint import lint
from .utils import OLSBroken, get_hexdigests, secho
from .validate.cli import validate
from .version import VERSION

__all__ = [
    "main",
]


@click.group()
@click.version_option(version=VERSION)
def main() -> None:
    """Run the Bioregistry CLI."""


@click.command()
def download() -> None:
    """Download/update the external entries in the Bioregistry."""
    try:
        from .external import GETTERS
    except ImportError as exc:
        click.secho(
            "Could not import alignment dependencies."
            " Install bioregistry again with `pip install bioregistry[align]`.",
            fg="red",
        )
        raise sys.exit(1) from exc

    for _, name, getter in GETTERS:
        secho(f"Downloading {name}")
        getter(force_download=True)


@main.command()
@click.option("--skip-fairsharing", is_flag=True)
@click.option("--skip-re3data", is_flag=True)
@click.option("--skip-bioportal", is_flag=True)
@click.option("--skip-agroportal", is_flag=True)
@click.option("--skip-slow", is_flag=True)
@click.option("--no-force", is_flag=True)
def align(
    skip_fairsharing: bool,
    skip_re3data: bool,
    skip_bioportal: bool,
    skip_agroportal: bool,
    skip_slow: bool,
    no_force: bool,
) -> None:
    """Align all external registries."""
    try:
        from .external.align import aligner_resolver
    except ImportError as exc:
        click.secho(
            "Could not import alignment dependencies."
            " Install bioregistry again with `pip install bioregistry[align]`.",
            fg="red",
        )
        raise sys.exit(1) from exc

    pre_digests = get_hexdigests()

    skip = set()
    if skip_fairsharing or skip_slow:
        skip.add("fairsharing")
    if skip_re3data or skip_slow:
        skip.add("re3data")
    if skip_bioportal or skip_slow:
        skip.add("bioportal")
    if skip_agroportal or skip_slow:
        skip.add("agroportal")
    # Temporary fix to avoid issue with duplicate URI prefix
    skip.add("wikidata")
    for aligner_cls in aligner_resolver:
        if aligner_cls.key in skip:
            continue
        secho(f"Aligning {aligner_cls.key}")
        try:
            aligner_cls.align(force_download=not no_force)
        except (IOError, OLSBroken) as e:
            secho(f"Failed to align {aligner_cls.key}: {e}", fg="red")

    if pre_digests != get_hexdigests():
        secho("Alignment created updates", fg="green")
        click.echo("::set-output name=BR_UPDATED::true")


main.add_command(lint)
main.add_command(compare)
main.add_command(export)
main.add_command(validate)
main.add_command(web)


@main.command()
@click.pass_context
def update(ctx: click.Context) -> None:
    """Update the Bioregistry."""
    ctx.invoke(align)
    ctx.invoke(lint)
    ctx.invoke(export)
    ctx.invoke(compare)

    try:
        from . import upload_ndex

        ctx.invoke(upload_ndex.main)
    except ImportError:
        click.secho("Could not import ndex", fg="red")
    except Exception as e:
        click.secho("Error uploading to ndex", fg="red")
        click.secho(str(e), fg="red")


if __name__ == "__main__":
    main()
