# -*- coding: utf-8 -*-

"""Export the Bioregistry to RDF."""

import logging
from typing import Any, Callable, List, Optional, Tuple, Union, cast

import click
import rdflib
from rdflib import Literal, Namespace
from rdflib.namespace import DC, DCTERMS, FOAF, RDF, RDFS, SKOS, XSD
from rdflib.term import URIRef

import bioregistry
from bioregistry import Manager
from bioregistry.constants import (
    RDF_JSONLD_PATH,
    RDF_NT_PATH,
    RDF_TURTLE_PATH,
    SCHEMA_JSONLD_PATH,
    SCHEMA_NT_PATH,
    SCHEMA_TURTLE_PATH,
)
from bioregistry.schema.constants import (
    IDOT,
    OBOINOWL,
    _add_schema,
    bioregistry_collection,
    bioregistry_metaresource,
    bioregistry_resource,
    bioregistry_schema,
    get_schema_rdf,
    orcid,
)
from bioregistry.schema.struct import Collection, Registry, Resource

logger = logging.getLogger(__name__)

NAMESPACES = {
    _ns: Namespace(_uri) for _ns, _uri in bioregistry.manager.get_internal_prefix_map().items()
}
NAMESPACE_WARNINGS = set()


@click.command()
def export_rdf():
    """Export RDF."""
    from bioregistry import manager

    schema_rdf = get_schema_rdf()
    schema_rdf.serialize(SCHEMA_TURTLE_PATH.as_posix(), format="turtle")
    schema_rdf.serialize(SCHEMA_NT_PATH.as_posix(), format="nt", encoding="utf-8")
    schema_rdf.serialize(
        SCHEMA_JSONLD_PATH.as_posix(),
        format="json-ld",
        context={
            "@language": "en",
            **dict(schema_rdf.namespaces()),
        },
        sort_keys=True,
        ensure_ascii=False,
    )

    graph = get_full_rdf(manager=manager) + schema_rdf
    graph.serialize(RDF_TURTLE_PATH.as_posix(), format="turtle")
    graph.serialize(RDF_NT_PATH.as_posix(), format="nt", encoding="utf-8")
    # Currently getting an issue with not being able to shorten URIs
    # graph.serialize(os.path.join(DOCS_DATA, "bioregistry.xml"), format="xml")

    context = {
        "@language": "en",
        **dict(graph.namespaces()),
    }
    graph.serialize(
        RDF_JSONLD_PATH.as_posix(),
        format="json-ld",
        context=context,
        sort_keys=True,
        ensure_ascii=False,
    )


def _graph(manager: Manager) -> rdflib.Graph:
    graph = rdflib.Graph()
    graph.namespace_manager.bind("bioregistry", bioregistry_resource)
    graph.namespace_manager.bind("bioregistry.metaresource", bioregistry_metaresource)
    graph.namespace_manager.bind("bioregistry.collection", bioregistry_collection)
    graph.namespace_manager.bind("bioregistry.schema", bioregistry_schema)
    graph.namespace_manager.bind("orcid", orcid)
    graph.namespace_manager.bind("foaf", FOAF)
    graph.namespace_manager.bind("dc", DC)
    graph.namespace_manager.bind("dcterms", DCTERMS)
    graph.namespace_manager.bind("skos", SKOS)
    graph.namespace_manager.bind("obo", Namespace("http://purl.obolibrary.org/obo/"))
    graph.namespace_manager.bind("idot", IDOT)
    graph.namespace_manager.bind("oboinowl", OBOINOWL)
    for key, value in manager.get_internal_prefix_map().items():
        graph.namespace_manager.bind(key, value)
    return graph


def get_full_rdf(manager: Manager) -> rdflib.Graph:
    """Get a combine RDF graph representing the Bioregistry using :mod:`rdflib`."""
    graph = _graph(manager=manager)
    _add_schema(graph)
    for registry in manager.metaregistry.values():
        registry.add_triples(graph)
    for collection in manager.collections.values():
        collection.add_triples(graph)
    for resource in manager.registry.values():
        _add_resource(graph=graph, manager=manager, resource=resource)
    return graph


def collection_to_rdf_str(
    collection: Collection,
    manager: Manager,
    fmt: Optional[str] = None,
) -> str:
    """Get a collection as an RDF string."""
    graph = _graph(manager=manager)
    collection.add_triples(graph)
    return graph.serialize(format=fmt or "turtle")


def metaresource_to_rdf_str(
    registry: Registry,
    manager: Manager,
    fmt: Optional[str] = None,
) -> str:
    """Get a collection as an RDF string."""
    graph = _graph(manager=manager)
    registry.add_triples(graph)
    return graph.serialize(format=fmt or "turtle")


def resource_to_rdf_str(
    resource: Resource,
    manager: Manager,
    fmt: Optional[str] = None,
) -> str:
    """Get a collection as an RDF string."""
    graph = _graph(manager=manager)
    _add_resource(resource, manager=manager, graph=graph)
    return graph.serialize(format=fmt or "turtle")


def _get_resource_functions() -> List[Tuple[Union[str, URIRef], Callable[[Resource], Any], URIRef]]:
    return [
        ("0000008", Resource.get_pattern, XSD.string),
        ("0000006", Resource.get_uri_format, XSD.string),
        ("0000005", Resource.get_example, XSD.string),
        ("0000012", Resource.is_deprecated, XSD.boolean),
        (DC.description, Resource.get_description, XSD.string),
        (FOAF.homepage, Resource.get_homepage, XSD.string),
    ]


def _add_resource(resource: Resource, *, manager: Manager, graph: rdflib.Graph):
    node = cast(URIRef, bioregistry_resource[resource.prefix])
    graph.add((node, RDF.type, bioregistry_schema["0000001"]))
    graph.add((node, RDFS.label, Literal(resource.get_name())))
    graph.add((node, DCTERMS.isPartOf, bioregistry_metaresource["bioregistry"]))
    graph.add((bioregistry_metaresource["bioregistry"], DCTERMS.hasPart, node))
    for synonym in resource.get_synonyms():
        graph.add((node, bioregistry_schema["0000023"], Literal(synonym)))

    for predicate, func, datatype in _get_resource_functions():
        value = func(resource)
        if not isinstance(predicate, URIRef):
            predicate = bioregistry_schema[predicate]
        if value is not None:
            graph.add((node, predicate, Literal(value, datatype=datatype)))

    download = (
        resource.get_download_owl()
        or resource.get_download_obo()
        or resource.get_download_obograph()
    )
    if download:
        graph.add((node, bioregistry_schema["0000010"], URIRef(download)))

    # Ontological relationships

    for depends_on in manager.get_depends_on(resource.prefix) or []:
        graph.add((node, bioregistry_schema["0000017"], bioregistry_resource[depends_on]))

    for appears_in in manager.get_appears_in(resource.prefix) or []:
        graph.add((node, bioregistry_schema["0000018"], bioregistry_resource[appears_in]))

    part_of = manager.get_part_of(resource.prefix)
    if part_of:
        graph.add((node, DCTERMS.isPartOf, bioregistry_resource[part_of]))
        graph.add((bioregistry_resource[part_of], DCTERMS.hasPart, node))

    provides = manager.get_provides_for(resource.prefix)
    if provides:
        graph.add((node, bioregistry_schema["0000011"], bioregistry_resource[provides]))

    if resource.has_canonical:
        graph.add(
            (node, bioregistry_schema["0000016"], bioregistry_resource[resource.has_canonical])
        )

    contact = resource.get_contact()
    if contact is not None:
        contact_node = contact.add_triples(graph)
        graph.add((node, bioregistry_schema["0000019"], contact_node))
    if resource.reviewer is not None and resource.reviewer.orcid:
        reviewer_node = resource.reviewer.add_triples(graph)
        graph.add((node, bioregistry_schema["0000021"], reviewer_node))
    if resource.contributor is not None and resource.contributor.orcid:
        contributor_node = resource.contributor.add_triples(graph)
        graph.add((contributor_node, DCTERMS.contributor, node))

    mappings = resource.get_mappings()
    for metaprefix, metaidentifier in (mappings or {}).items():
        metaresource = manager.metaregistry[metaprefix]
        if metaprefix not in NAMESPACES and metaresource.bioregistry_prefix in NAMESPACES:
            metaprefix = metaresource.bioregistry_prefix
        if metaprefix not in NAMESPACES:
            if metaprefix not in NAMESPACE_WARNINGS:
                logger.warning(f"can not find prefix-uri pair for {metaprefix}")
                NAMESPACE_WARNINGS.add(metaprefix)
            continue
        graph.add((node, SKOS.exactMatch, NAMESPACES[metaprefix][metaidentifier]))
        graph.add(
            (
                NAMESPACES[metaprefix][metaidentifier],
                DCTERMS.isPartOf,
                bioregistry_metaresource[metaresource.prefix],
            )
        )
        graph.add(
            (
                bioregistry_metaresource[metaresource.prefix],
                DCTERMS.hasPart,
                NAMESPACES[metaprefix][metaidentifier],
            )
        )


if __name__ == "__main__":
    export_rdf()
