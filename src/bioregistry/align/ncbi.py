# -*- coding: utf-8 -*-

"""Align NCBI with the Bioregistry."""

from typing import Any, Dict, List, Mapping

from bioregistry.align.utils import Aligner
from bioregistry.external.ncbi import get_ncbi

__all__ = ['NcbiAligner']


class NcbiAligner(Aligner):
    """Aligner for NCBI xref registry."""

    key = 'ncbi'
    getter = get_ncbi
    curation_header = ('name', 'homepage', 'example')

    def get_curation_row(self, external_id, external_entry) -> List[str]:
        """Return the relevant fields from an NCBI entry for pretty-printing."""
        return [
            external_entry['name'],
            external_entry.get('homepage'),
            external_entry.get('example'),
        ]


if __name__ == '__main__':
    NcbiAligner.align()
