"""Generating records for :mod:`curies`."""

import itertools as itt
import logging
from collections import defaultdict
from typing import (
    Collection,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    cast,
)

import curies
from curies import Converter

from .schema.struct import Resource

__all__ = [
    "get_converter",
]

logger = logging.getLogger(__name__)
prefix_blacklist = {"bgee.gene"}
uri_prefix_blacklist = {
    "http://www.ebi.ac.uk/ontology-lookup/?termId=",
    "https://www.ebi.ac.uk/ontology-lookup/?termId=",
    "https://purl.obolibrary.org/obo/",
    "http://purl.obolibrary.org/obo/",
    # see https://github.com/biopragmatics/bioregistry/issues/548
    "https://www.ncbi.nlm.nih.gov/nuccore/",
    "http://www.ncbi.nlm.nih.gov/nuccore/",
    "https://www.ebi.ac.uk/ena/data/view/",
    "http://www.ebi.ac.uk/ena/data/view/",
    "http://arabidopsis.org/servlets/TairObject?accession=",
}
prefix_resource_blacklist = {
    ("orphanet", "http://www.orpha.net/ORDO/Orphanet_"),  # biocontext is wrong
    ("orphanet", "https://www.orpha.net/ORDO/Orphanet_"),  # biocontext is wrong
    ("wikidata.property", "http://scholia.toolforge.org/"),  # duplicated with wikidata
    ("wikidata.property", "https://scholia.toolforge.org/"),  # duplicated with wikidata
    ("uniprot", "https://www.ncbi.nlm.nih.gov/protein/"),  # FIXME not sure how to resolve this
    ("uniprot", "http://www.ncbi.nlm.nih.gov/protein/"),  # FIXME not sure how to resolve this
    ("cl", "https://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/"),
    ("cl", "http://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/"),
    ("uberon", "http://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/"),
    ("uberon", "https://www.ebi.ac.uk/ols/ontologies/cl/terms?iri=http://purl.obolibrary.org/obo/"),
    ("ncbigene", "https://en.wikipedia.org/wiki/"),  # probably from wikigene?
    ("ncbigene", "http://en.wikipedia.org/wiki/"),
    ("wbphenotype", "http://www.wormbase.org/get?name="),  # wrong in GO
    ("wbphenotype", "https://www.wormbase.org/get?name="),  # wrong in GO
    ("wbls", "http://www.wormbase.org/get?name="),  # wrong in GO
    ("wbls", "https://www.wormbase.org/get?name="),  # wrong in GO
    ("uniprot.isoform", "http://www.uniprot.org/uniprot/"),  # wrong in miriam
    ("uniprot.isoform", "https://www.uniprot.org/uniprot/"),  # wrong in miriam
    ("uniprot.isoform", "http://purl.uniprot.org/uniprot/"),  # wrong in miriam
    ("uniprot.isoform", "https://purl.uniprot.org/uniprot/"),  # wrong in miriam
}
assert all(not x.endswith("$1") for _, x in prefix_resource_blacklist)


def _debug_or_raise(msg: str, strict: bool = False) -> None:
    if strict:
        raise ValueError(msg)
    logger.debug(msg)


def _stratify_resources(resources: Iterable[Resource]) -> Tuple[List[Resource], List[Resource]]:
    primary_resources, secondary_resources = [], []
    for resource in resources:
        if resource.prefix in prefix_blacklist:
            continue
        if resource.part_of or resource.provides or resource.has_canonical:
            secondary_resources.append(resource)
        else:
            primary_resources.append(resource)
    return primary_resources, secondary_resources


def _iterate_prefix_prefix(resource: Resource, *extras: str) -> Iterable[str]:
    prefixes_ = [
        resource.prefix,
        *resource.get_synonyms(),
        resource.get_preferred_prefix(),
        *extras,
    ]
    for prefix_ in prefixes_:
        if not prefix_:
            continue
        for prefix_prefix in [
            f"{prefix_}:",
            f"{prefix_.upper()}:",
            f"{prefix_.lower()}:",
        ]:
            yield prefix_prefix


# TODO handle situations where a URI format string is available but
#  it is not directly convertable to URI prefix -> use Bioregistry
#  URL for these (e.g., chemspider, lrg)

# TODO handle when one URI is a subspace of another
#  (e.g., uniprot.isoform and uniprot)


def get_converter(
    resources: List[Resource],
    prefix_priority: Optional[Sequence[str]] = None,
    uri_prefix_priority: Optional[Sequence[str]] = None,
    include_prefixes: bool = False,
    strict: bool = False,
    blacklist: Optional[Collection[str]] = None,
    remapping: Optional[Mapping[str, str]] = None,
    rewiring: Optional[Mapping[str, str]] = None,
) -> Converter:
    """Generate a converter from resources."""
    records = _get_records(
        resources,
        prefix_priority=prefix_priority,
        uri_prefix_priority=uri_prefix_priority,
        include_prefixes=include_prefixes,
        strict=strict,
        blacklist=blacklist,
    )
    converter = curies.Converter(records)
    if remapping:
        converter = curies.remap_curie_prefixes(converter, remapping)
    if rewiring:
        converter = curies.rewire(converter, rewiring)
    converter = _enrich_converter_synonyms(converter)
    return converter


def _get_records(  # noqa: C901
    resources: List[Resource],
    prefix_priority: Optional[Sequence[str]] = None,
    uri_prefix_priority: Optional[Sequence[str]] = None,
    include_prefixes: bool = False,
    strict: bool = False,
    blacklist: Optional[Collection[str]] = None,
) -> List[curies.Record]:
    """Generate records from resources."""
    blacklist = set(blacklist or []).union(prefix_blacklist)
    resource_dict: Mapping[str, Resource] = {
        resource.prefix: resource
        for resource in resources
        if resource.get_uri_prefix() and resource.prefix not in blacklist
    }
    primary_uri_prefixes: Dict[str, str] = {
        resource.prefix: cast(str, resource.get_uri_prefix(priority=uri_prefix_priority))
        for resource in resource_dict.values()
    }
    primary_prefixes: Dict[str, str] = {
        resource.prefix: resource.get_priority_prefix(priority=prefix_priority)
        for resource in resource_dict.values()
    }
    pattern_map = {
        prefix: pattern
        for prefix in primary_prefixes
        if (pattern := resource_dict[prefix].get_pattern()) is not None
    }
    secondary_prefixes: DefaultDict[str, Set[str]] = defaultdict(set)
    secondary_uri_prefixes: DefaultDict[str, Set[str]] = defaultdict(set)

    #: A mapping from URI prefixes (both primary and secondary) appearing
    #: in all records to bioregistry prefixes
    reverse_uri_prefix_lookup: Dict[str, str] = {
        "http://purl.obolibrary.org/obo/": "obo",
        "https://purl.obolibrary.org/obo/": "obo",
    }
    #: A mapping from prefixes (both primary and secondary) appearing
    #: in all records to bioregistry prefixes
    reverse_prefix_lookup: Dict[str, str] = {}

    def _add_primary_uri_prefix(prefix: str) -> Optional[str]:
        primary_uri_prefix = primary_uri_prefixes[prefix]
        if primary_uri_prefix in reverse_uri_prefix_lookup:
            logger.debug(
                "duplicate primary URI prefix: %s for %s that already appeared in %s",
                primary_uri_prefix,
                prefix,
                reverse_uri_prefix_lookup[primary_uri_prefix],
            )
            # primary_uri_prefix = f"https://bioregistry.io/{resource.prefix}:"
            return None
        reverse_uri_prefix_lookup[primary_uri_prefix] = prefix
        return primary_uri_prefix

    def _add_primary_prefix(prefix: str) -> Optional[str]:
        primary_prefix = primary_prefixes[prefix]
        if primary_prefix in reverse_prefix_lookup:
            logger.debug(
                "duplicate primary prefix: %s for %s that already appeared in %s",
                primary_prefix,
                prefix,
                reverse_prefix_lookup[primary_prefix],
            )
            return None
        reverse_prefix_lookup[primary_prefix] = prefix
        return primary_prefix

    def _add_synonym(*, synonym: str, prefix: str) -> None:
        if synonym in reverse_prefix_lookup:
            if reverse_prefix_lookup[synonym] == prefix:
                return
            msg = f"duplicate prefix in {reverse_prefix_lookup[synonym]} and {prefix}: {synonym}"
            _debug_or_raise(msg, strict=strict)
            return
        reverse_prefix_lookup[synonym] = prefix
        secondary_prefixes[prefix].add(synonym)

    def _add_uri_synonym(*, uri_prefix: str, prefix: str) -> None:
        if (prefix, uri_prefix) in prefix_resource_blacklist:
            return
        elif uri_prefix in uri_prefix_blacklist:
            return
        elif uri_prefix in reverse_uri_prefix_lookup:
            if prefix == reverse_uri_prefix_lookup[uri_prefix]:
                return  # this is already in
            msg = f"duplicate URI prefix in {reverse_uri_prefix_lookup[uri_prefix]} and {prefix}: {uri_prefix}"
            _debug_or_raise(msg, strict=strict)
            return
        else:
            reverse_uri_prefix_lookup[uri_prefix] = prefix
            secondary_uri_prefixes[prefix].add(uri_prefix)

    def _add_prefix_prefixes(
        primary_prefix: str, resource: Resource, target_prefix: Optional[str] = None
    ) -> None:
        if target_prefix is None:
            target_prefix = resource.prefix
        for prefix_prefix in _iterate_prefix_prefix(resource, primary_prefix):
            if prefix_prefix in reverse_uri_prefix_lookup:
                if reverse_uri_prefix_lookup[prefix_prefix] == resource.prefix:
                    continue
                msg = (
                    f"duplicate prefix prefix in {reverse_uri_prefix_lookup[prefix_prefix]} "
                    f"and {resource.prefix}: {prefix_prefix}"
                )
                _debug_or_raise(msg, strict=strict)
                continue
            reverse_uri_prefix_lookup[prefix_prefix] = target_prefix
            secondary_uri_prefixes[target_prefix].add(prefix_prefix)

    primary_resources, secondary_resources = _stratify_resources(resource_dict.values())
    for resource in itt.chain(primary_resources):
        primary_uri_prefix = _add_primary_uri_prefix(resource.prefix)
        if primary_uri_prefix is None:
            continue
        primary_prefix = _add_primary_prefix(resource.prefix)
        if primary_prefix is None:
            continue
        for synonym in resource.get_synonyms():
            _add_synonym(synonym=synonym, prefix=resource.prefix)
        for uri_prefix in resource.get_uri_prefixes():
            _add_uri_synonym(uri_prefix=uri_prefix, prefix=resource.prefix)
        if include_prefixes:
            _add_prefix_prefixes(primary_prefix=primary_prefix, resource=resource)

    for resource in secondary_resources:
        provides = resource.provides
        canonical = resource.has_canonical
        has_part = resource.part_of
        if provides is not None or canonical is not None:
            prefix = cast(str, provides or canonical)
            # remove from cache so it doesn't get its own entry
            primary_prefix = primary_prefixes.pop(resource.prefix)
            if primary_prefix not in reverse_prefix_lookup:
                reverse_prefix_lookup[primary_prefix] = prefix
                secondary_prefixes[prefix].add(primary_prefix)
            primary_uri_prefix = primary_uri_prefixes.pop(resource.prefix)
            if primary_uri_prefix not in reverse_uri_prefix_lookup:
                reverse_uri_prefix_lookup[primary_uri_prefix] = prefix
                secondary_uri_prefixes[prefix].add(primary_uri_prefix)
            _add_synonym(synonym=resource.prefix, prefix=prefix)
            for synonym in resource.get_synonyms():
                _add_synonym(synonym=synonym, prefix=prefix)
            for uri_prefix in resource.get_uri_prefixes():
                _add_uri_synonym(uri_prefix=uri_prefix, prefix=prefix)
            if include_prefixes:
                _add_prefix_prefixes(
                    primary_prefix=primary_prefix, resource=resource, target_prefix=prefix
                )
        elif has_part:
            uri_prefixes = {
                p
                for p in resource.get_uri_prefixes()
                if (resource.prefix, p) not in prefix_resource_blacklist
            }
            _duplicats = [
                uri_prefix for uri_prefix in uri_prefixes if uri_prefix in reverse_uri_prefix_lookup
            ]
            if _duplicats and has_part in primary_uri_prefixes:
                del primary_prefixes[resource.prefix]
                del primary_uri_prefixes[resource.prefix]
                _add_synonym(synonym=resource.prefix, prefix=has_part)
                for synonym in resource.get_synonyms():
                    _add_synonym(synonym=synonym, prefix=has_part)
                for uri_prefix in uri_prefixes:
                    _add_uri_synonym(uri_prefix=uri_prefix, prefix=has_part)
                if include_prefixes:
                    _add_prefix_prefixes(
                        primary_prefix=primary_prefixes[has_part],
                        resource=resource,
                        target_prefix=has_part,
                    )
            else:
                primary_uri_prefix = _add_primary_uri_prefix(resource.prefix)
                if primary_uri_prefix is None:
                    continue
                primary_prefix = _add_primary_prefix(resource.prefix)
                if primary_prefix is None:
                    continue
                for synonym in resource.get_synonyms():
                    _add_synonym(synonym=synonym, prefix=resource.prefix)
                for uri_prefix in resource.get_uri_prefixes():
                    _add_uri_synonym(uri_prefix=uri_prefix, prefix=resource.prefix)
                if include_prefixes:
                    _add_prefix_prefixes(primary_prefix=primary_prefix, resource=resource)

        else:
            raise RuntimeError

    records: Dict[str, curies.Record] = {}
    for prefix, primary_prefix in primary_prefixes.items():
        primary_uri_prefix = primary_uri_prefixes[prefix]
        if not primary_prefix or not primary_uri_prefix:
            continue
        records[prefix] = curies.Record(
            prefix=primary_prefix,
            prefix_synonyms=sorted(secondary_prefixes[prefix].union({prefix}) - {primary_prefix}),
            uri_prefix=primary_uri_prefix,
            uri_prefix_synonyms=sorted(secondary_uri_prefixes[prefix] - {primary_uri_prefix}),
            pattern=pattern_map.get(prefix),
        )

    return [record for _, record in sorted(records.items())]


def _enrich_converter_synonyms(converter: Converter) -> Converter:
    return Converter([_enrich_record_synonyms(r) for r in converter.records])


def _enrich_record_synonyms(record: curies.Record) -> curies.Record:
    sss = set()
    for s in [record.prefix, *record.prefix_synonyms]:
        sss.update(_generate_variants(s))
    record.prefix_synonyms = sorted(sss - {record.prefix})
    return record


def _generate_variants(s: str):
    yield s
    yield s.lower()
    yield s.upper()
    yield s.replace("_", "")
    yield s.replace("_", "").upper()
    yield s.replace("_", "").lower()
