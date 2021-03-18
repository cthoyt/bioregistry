# -*- coding: utf-8 -*-

"""Align OntoBee with the Bioregistry."""

import textwrap
from typing import List

from bioregistry.align.utils import NewAligner
from bioregistry.external.ontobee import get_ontobee

__all__ = ['OntobeeAligner']


class OntobeeAligner(NewAligner):
    """Aligner for OntoBee xref registry."""

    key = 'ontobee'
    getter = get_ontobee
    curation_header = ('name', 'url')

    def get_curation_row(self, external_id, external_entry) -> List[str]:
        """Return the relevant fields from an OntoBee entry for pretty-printing."""
        return [
            textwrap.shorten(external_entry['name'], 50),
            external_entry.get('url'),
        ]


if __name__ == '__main__':
    OntobeeAligner.align(dry=False)
