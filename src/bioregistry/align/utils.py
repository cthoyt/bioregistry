# -*- coding: utf-8 -*-

"""Utilities for registry alignment."""

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar, Dict, Iterable, Mapping, Optional, Sequence

from tabulate import tabulate

from bioregistry import normalize_prefix, read_bioregistry
from bioregistry.utils import write_bioregistry

__all__ = [
    'Aligner',
]


class Aligner(ABC):
    """A class for aligning new registries."""

    #: The key for the external registry
    key: ClassVar[str]

    #: The function that gets the external registry as a dictionary from the string identifier to
    #: the entries (could be anything, but a dictionary is probably best)
    getter: ClassVar[Callable[..., Mapping[str, Any]]]

    #: Keyword arguments to pass to the getter function on call
    getter_kwargs: ClassVar[Optional[Mapping[str, Any]]] = None

    #: Optional header to put on the curation table
    curation_header: ClassVar[Optional[Sequence[str]]] = None

    def __init__(self):
        """Instantiate the aligner."""
        self.internal_registry = read_bioregistry()
        self.external_registry = self.__class__.getter(**(self.getter_kwargs or {}))
        self.skip_external = self.get_skip()

        # Get all of the pre-curated mappings from the Bioregistry
        self.external_id_to_bioregistry_id = {
            bioregistry_entry[self.key]['prefix']: bioregistry_id
            for bioregistry_id, bioregistry_entry in self.internal_registry.items()
            if self.key in bioregistry_entry
        }

        # Run lexical alignment
        self._align()

    def get_skip(self) -> Mapping[str, str]:
        """Get the mapping prefixes that should be skipped to their reasons (strings)."""
        return {}

    def _align(self):
        """Align the external registry."""
        for external_id, external_entry in self.external_registry.items():
            if external_id in self.skip_external:
                continue

            bioregistry_id = self.external_id_to_bioregistry_id.get(external_id)

            # try to lookup with lexical match
            if bioregistry_id is None:
                bioregistry_id = normalize_prefix(external_id)

            if bioregistry_id is not None:  # a match was found
                _entry = self.prepare_external(external_id, external_entry)
                _entry['prefix'] = external_id
                self.external_id_to_bioregistry_id[external_id] = bioregistry_id
                self._update_internal_registry(bioregistry_id, _entry)

    def _update_internal_registry(self, bioregistry_id, entry):
        self.internal_registry[bioregistry_id][self.key] = entry

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
        """Prepare a dictionary to be added to the bioregistry for each external registry entry.

        The default implementation returns `external_entry` unchanged.
        If you need more than that, override this method.

        :param external_id: The external registry identifier
        :param external_entry: The external registry data
        :return: The dictionary to be added to the bioregistry for the aligned entry
        """
        return external_entry

    @classmethod
    def align(cls, dry: bool = False):
        """Align and output the curation sheet."""
        instance = cls()
        if not dry:
            write_bioregistry(instance.internal_registry)
        instance.print_uncurated()

    @abstractmethod
    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Get a sequence of items that will be ech row in the curation table.

        :param external_id: The external registry identifier
        :param external_entry: The external registry data
        :return: A sequence of cells to add to the curation table.

        .. note:: You don't need to pass the external ID. this will automatically be the first element.

        .. note:: set the ``curation_header`` on the class to get a nice header automatically.
        """  # noqa:DAR202

    def _iter_curation_rows(self) -> Iterable[Sequence[str]]:
        for external_id, external_entry in sorted(self.external_registry.items(), key=lambda s: s[0].casefold()):
            if external_id in self.skip_external:
                continue

            bioregistry_id = self.external_id_to_bioregistry_id.get(external_id)
            if bioregistry_id is None:
                yield (
                    external_id,
                    *self.get_curation_row(external_id, external_entry),
                )

    def get_curation_table(self, **kwargs) -> str:
        """Get the curation table as a string, built by :mod:`tabulate`."""
        kwargs.setdefault('tablefmt', 'rst')
        if self.curation_header:
            headers = ('prefix', *self.curation_header)
        else:
            headers = ()

        return tabulate(
            list(self._iter_curation_rows()),
            headers=headers,
            **kwargs,
        )

    def print_uncurated(self, **kwargs) -> None:
        """Print the curation table."""
        print(self.get_curation_table(**kwargs))


class NewAligner(Aligner):
    def _update_internal_registry(self, bioregistry_id, entry):
        self.internal_registry[bioregistry_id].setdefault('mappings', {})
        self.internal_registry[bioregistry_id]['mappings'][self.key] = entry['prefix']

        # Remove old-style data
        if self.key in self.internal_registry[bioregistry_id]:
            del self.internal_registry[bioregistry_id][self.key]
