# -*- coding: utf-8 -*-

"""Resolvers for CURIE (e.g., pairs of prefix and identifier)."""

import warnings
from typing import Mapping, Optional, Sequence, Tuple

from .resolve import get_resource
from .resource_manager import manager

__all__ = [
    "is_valid_curie",
    "is_standardizable_curie",
    "is_valid_identifier",
    "is_standardizable_identifier",
    "get_providers",
    "get_providers_list",
    "get_identifiers_org_iri",
    "get_identifiers_org_curie",
    "get_obofoundry_iri",
    "get_ols_iri",
    "get_bioportal_iri",
    "get_n2t_iri",
    "get_iri",
    "get_link",
    "get_bioregistry_iri",
    "get_default_iri",
    "standardize_identifier",
    "miriam_standardize_identifier",
]


def is_valid_curie(curie: str) -> bool:
    """Check if a CURIE is standardized and valid.

    :param curie: A compact URI of the form ``<prefix>:<local unique identifier>``.
    :return:
        If the CURIE is standardized in both syntax and semantics. This means that it uses the Bioregistry
        canonical prefix, does not have a redundant prefix, and if available, matches the Bioregistry's
        regular expression pattern for identifiers.

    Standard CURIE
    >>> is_valid_curie("go:0000001")
    True

    Not a standard CURIE (i.e., no colon)
    >>> is_valid_curie("0000001")
    False
    >>> is_valid_curie("GO_0000001")
    False
    >>> is_valid_curie("PTM-0001")
    False

    Non-standardized prefix
    >>> is_valid_curie("GO:0000001")
    False

    Incorrect identifier
    >>> is_valid_curie("go:0001")
    False

    Banana scenario
    >>> is_valid_curie("go:GO:0000001")
    False

    Unknown prefix
    >>> is_valid_curie("xxx:yyy")
    False
    """
    return manager.is_valid_curie(curie)


def is_standardizable_curie(curie: str) -> bool:
    """Check if a CURIE is validatable, but not necessarily standardized.

    :param curie: A compact URI
    :return: If the CURIE can be standardized (e.g., prefix normalize and identifier normalized)
        then validated.

    Standard CURIE
    >>> is_standardizable_curie("go:0000001")
    True

    Not a standard CURIE (i.e., no colon)
    >>> is_standardizable_curie("0000001")
    False
    >>> is_standardizable_curie("GO_0000001")
    False
    >>> is_standardizable_curie("PTM-0001")
    False

    Non-standardized prefix
    >>> is_standardizable_curie("GO:0000001")
    True

    Incorrect identifier
    >>> is_standardizable_curie("go:0001")
    False

    Banana scenario
    >>> is_standardizable_curie("go:GO:0000001")
    True

    Unknown prefix
    >>> is_standardizable_curie("xxx:yyy")
    False
    """
    return manager.is_standardizable_curie(curie)


def is_valid_identifier(prefix: str, identifier: str) -> bool:
    """Check if the pre-parsed CURIE is standardized valid.

    :param prefix: The prefix from a compact URI
    :param identifier: The local unique identifer from a compact URI
    :return:
        If the CURIE is standardized in both syntax and semantics. This means that it uses the Bioregistry
        canonical prefix, does not have a redundant prefix, and if available, matches the Bioregistry's
        regular expression pattern for identifiers.

    .. seealso:: The :func:`is_standardizable_identifier` performs normalization before checking validity

    Standard CURIE
    >>> is_valid_identifier("go", "0000001")
    True

    Non-standardized prefix
    >>> is_valid_identifier("GO", "0000001")
    False

    Incorrect identifier
    >>> is_valid_identifier("go", "0001")
    False

    Banana scenario
    >>> is_valid_identifier("go", "GO:0000001")
    False

    Unknown prefix
    >>> is_valid_identifier("xxx", "yyy")
    False
    """
    return manager.is_valid_identifier(prefix, identifier)


def is_standardizable_identifier(prefix: str, identifier: str) -> bool:
    """Check if the identifier is standardizable.

    :param prefix: The prefix from a compact URI
    :param identifier: The local unique identifer from a compact URI
    :return:
        If the CURIE can be standardized (e.g., prefix normalize and identifier normalized)
        then validated.

    .. seealso:: The :func:`is_valid_identifier` does not perform normalization before checking validity

    Standard CURIE
    >>> is_standardizable_identifier("go", "0000001")
    True

    Non-standardized prefix
    >>> is_standardizable_identifier("GO", "0000001")
    True

    Incorrect identifier
    >>> is_standardizable_identifier("go", "0001")
    False

    Banana scenario
    >>> is_standardizable_identifier("go", "GO:0000001")
    True

    Unknown prefix
    >>> is_standardizable_identifier("xxx", "yyy")
    False
    """
    return manager.is_standardizable_identifier(prefix, identifier)


def standardize_identifier(prefix: str, identifier: str) -> str:
    """Normalize an identifier."""
    resource = get_resource(prefix)
    if resource is None:
        return identifier  # nothing we can do
    return resource.standardize_identifier(identifier)


def miriam_standardize_identifier(prefix: str, identifier: str) -> Optional[str]:
    """Normalize the identifier with the appropriate banana.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A normalize identifier, possibly with banana/redundant prefix added.
        Returns none if the prefix doesn't map to MIRIAM.

    Examples with explicitly annotated bananas:

    >>> import bioregistry as br
    >>> assert "VariO" == br.get_banana('vario')
    >>> miriam_standardize_identifier('vario', '0376')
    'VariO:0376'
    >>> miriam_standardize_identifier('vario', 'VariO:0376')
    'VariO:0376'

    Examples with bananas from OBO:
    >>> import bioregistry as br
    >>> assert "GO" == br.get_banana('go')
    >>> miriam_standardize_identifier('go', '0000001')
    'GO:0000001'
    >>> miriam_standardize_identifier('go', 'GO:0000001')
    'GO:0000001'
    >>> assert "VariO" == br.get_banana('vario')
    >>> miriam_standardize_identifier('vario', '0000001')
    'VariO:0000001'
    >>> miriam_standardize_identifier('vario', 'VariO:0000001')
    'VariO:0000001'

    Examples from OBO Foundry:
    >>> miriam_standardize_identifier('chebi', '1234')
    'CHEBI:1234'
    >>> miriam_standardize_identifier('chebi', 'CHEBI:1234')
    'CHEBI:1234'

    Examples outside of OBO:
    >>> miriam_standardize_identifier('mgi', '6017782')
    'MGI:6017782'
    >>> miriam_standardize_identifier('mgi', 'MGI:6017782')
    'MGI:6017782'

    >>> miriam_standardize_identifier('swisslipid', '000000341')
    'SLM:000000341'
    >>> miriam_standardize_identifier('swisslipid', 'SLM:000000341')
    'SLM:000000341'

    Special cases with underscore-delimited bananas
    >>> miriam_standardize_identifier('cellosaurus', '0001')
    'CVCL_0001'
    >>> miriam_standardize_identifier('cellosaurus', 'CVCL_0001')
    'CVCL_0001'
    >>> miriam_standardize_identifier('ro', '0000001')
    'RO_0000001'
    >>> miriam_standardize_identifier('ro', 'RO_0000001')
    'RO_0000001'
    >>> miriam_standardize_identifier('geogeo', '000000001')
    'GEO_000000001'
    >>> miriam_standardize_identifier('geogeo', 'GEO_000000001')
    'GEO_000000001'
    >>> miriam_standardize_identifier('biomodels.kisao', '0000057')
    'KISAO_0000057'
    >>> miriam_standardize_identifier('biomodels.kisao', 'KISAO_0000057')
    'KISAO_0000057'

    Standard:

    >>> import bioregistry as br
    >>> assert br.get_banana('pdb') is None
    >>> assert not br.get_namespace_in_lui('pdb')
    >>> miriam_standardize_identifier('pdb', '00000020')
    '00000020'
    """
    resource = get_resource(prefix)
    if resource is None:
        return identifier  # nothing we can do
    return resource.miriam_standardize_identifier(identifier)


def get_default_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the default URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A IRI string corresponding to the default provider, if available.

    >>> get_default_iri('chebi', '24867')
    'http://purl.obolibrary.org/obo/CHEBI_24867'
    """
    return manager.get_default_iri(prefix, identifier)


def get_providers(prefix: str, identifier: str) -> Mapping[str, str]:
    """Get all providers for the CURIE."""
    return manager.get_providers(prefix, identifier)


def get_providers_list(prefix: str, identifier: str) -> Sequence[Tuple[str, str]]:
    """Get all providers for the CURIE."""
    return manager.get_providers_list(prefix, identifier)


def get_identifiers_org_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A IRI string corresponding to the Identifiers.org, if the prefix exists and is
        mapped to MIRIAM.

    >>> get_identifiers_org_iri('chebi', '24867')
    'https://identifiers.org/CHEBI:24867'
    >>> get_identifiers_org_iri("interpro", "IPR016380")
    'https://identifiers.org/interpro:IPR016380'
    >>> get_identifiers_org_iri("cellosaurus", "0001")
    'https://identifiers.org/cellosaurus:CVCL_0001'
    >>> get_identifiers_org_iri("biomodels.kisao", "0000057")
    'https://identifiers.org/biomodels.kisao:KISAO_0000057'
    """
    return manager.get_miriam_iri(prefix, identifier)


def get_n2t_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the name-to-thing URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A IRI string corresponding to the N2T resolve, if the prefix exists and is
        mapped to N2T.

    >>> get_n2t_iri('chebi', '24867')
    'https://n2t.net/chebi:24867'
    """
    return manager.get_n2t_iri(prefix, identifier)


def get_bioportal_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the Bioportal URL for the given CURIE.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the Bioportal page

    >>> get_bioportal_iri('chebi', '24431')
    'https://bioportal.bioontology.org/ontologies/CHEBI/?p=classes&conceptid=http://purl.obolibrary.org/obo/CHEBI_24431'
    """
    return manager.get_bioportal_iri(prefix, identifier)


def get_identifiers_org_curie(prefix: str, identifier: str) -> Optional[str]:
    """Get the identifiers.org CURIE for the given CURIE."""
    return manager.get_miriam_curie(prefix, identifier)


def get_obofoundry_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the OBO Foundry URL if possible.

    :param prefix: The prefix
    :param identifier: The identifier
    :return: The OBO Foundry URL if the prefix can be mapped to an OBO Foundry entry

    >>> get_obofoundry_iri('chebi', '24431')
    'http://purl.obolibrary.org/obo/CHEBI_24431'

    For entries where there's a preferred prefix, it is respected.

    >>> get_obofoundry_iri('fbbt', '00007294')
    'http://purl.obolibrary.org/obo/FBbt_00007294'
    """
    return manager.get_obofoundry_iri(prefix, identifier)


def get_ols_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the OLS URL if possible."""
    return manager.get_ols_iri(prefix, identifier)


def get_scholia_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get a Scholia IRI, if possible.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the Scholia page

    >>> get_scholia_iri("pubmed", "1234")
    'https://scholia.toolforge.org/pubmed/1234'

    >>> get_scholia_iri("pdb", "1234")
    None
    """
    return manager.get_scholia_iri(prefix, identifier)


def get_bioregistry_iri(prefix: str, identifier: str) -> Optional[str]:
    """Get the bioregistry link.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE
    :return: A link to the bioregistry resolver

    >>> get_bioregistry_iri('pdb', '1234')
    'https://bioregistry.io/pdb:1234'

    Redundant prefix (OBO)

    >>> get_bioregistry_iri('go', 'GO:0120212')
    'https://bioregistry.io/go:0120212'
    >>> get_bioregistry_iri('go', 'go:0120212')
    'https://bioregistry.io/go:0120212'
    >>> get_bioregistry_iri('go', '0120212')
    'https://bioregistry.io/go:0120212'

    Redundant prefix (banana; OBO)

    >>> get_bioregistry_iri('fbbt', 'fbbt:00007294')
    'https://bioregistry.io/fbbt:00007294'
    >>> get_bioregistry_iri('fbbt', 'fbbt:00007294')
    'https://bioregistry.io/fbbt:00007294'
    >>> get_bioregistry_iri('fbbt', '00007294')
    'https://bioregistry.io/fbbt:00007294'

    Redundant prefix (banana; explicit)
    >>> get_bioregistry_iri('go.ref', 'GO_REF:1234')
    'https://bioregistry.io/go.ref:1234'
    >>> get_bioregistry_iri('go.ref', '1234')
    'https://bioregistry.io/go.ref:1234'
    """
    return manager.get_bioregistry_iri(prefix=prefix, identifier=identifier)


def get_iri(
    prefix: str,
    identifier: Optional[str] = None,
    *,
    priority: Optional[Sequence[str]] = None,
    prefix_map: Optional[Mapping[str, str]] = None,
    use_bioregistry_io: bool = True,
    provider: Optional[str] = None,
) -> Optional[str]:
    """Get the best link for the CURIE, if possible.

    :param prefix: The prefix in the CURIE
    :param identifier: The identifier in the CURIE. If identifier is given as None, then this function will
        assume that the first argument (``prefix``) is actually a full CURIE.
    :param priority: A user-defined priority list. In addition to the metaprefixes in the Bioregistry
        corresponding to resources that are resolvers/lookup services, you can also use ``default``
        to correspond to the first-party IRI and ``custom`` to refer to the custom prefix map.
        The default priority list is:

        1. Custom prefix map (``custom``)
        1. First-party IRI (``default``)
        2. Identifiers.org / MIRIAM (``miriam``)
        3. Ontology Lookup Service (``ols``)
        4. OBO PURL (``obofoundry``)
        5. Name-to-Thing (``n2t``)
        6. BioPortal (``bioportal``)
    :param prefix_map: A custom prefix map to go with the ``custom`` key in the priority list
    :param use_bioregistry_io: Should the bioregistry resolution IRI be used? Defaults to true.
    :param provider: The provider code to use for a custom provider
    :return: The best possible IRI that can be generated based on the priority list.

    A pre-parse CURIE can be given as the first two arguments
    >>> get_iri("chebi", "24867")
    'http://purl.obolibrary.org/obo/CHEBI_24867'

    A CURIE can be given directly as a single argument
    >>> get_iri("chebi:24867")
    'http://purl.obolibrary.org/obo/CHEBI_24867'

    A priority list can be given
    >>> priority = ["miriam", "default", "bioregistry"]
    >>> get_iri("chebi:24867", priority=priority)
    'https://identifiers.org/CHEBI:24867'

    A custom prefix map can be supplied.
    >>> prefix_map = {"chebi": "https://example.org/chebi/"}
    >>> get_iri("chebi:24867", prefix_map=prefix_map)
    'https://example.org/chebi/24867'

    A custom prefix map can be supplied in combination with a priority list
    >>> prefix_map = {"lipidmaps": "https://example.org/lipidmaps/"}
    >>> priority = ["obofoundry", "custom", "default", "bioregistry"]
    >>> get_iri("chebi:24867", prefix_map=prefix_map, priority=priority)
    'http://purl.obolibrary.org/obo/CHEBI_24867'
    >>> get_iri("lipidmaps:1234", prefix_map=prefix_map, priority=priority)
    'https://example.org/lipidmaps/1234'

    A custom provider is given, which makes the Bioregistry very extensible
    >>> get_iri("chebi:24867", provider="chebi-img")
    'https://www.ebi.ac.uk/chebi/displayImage.do?defaultImage=true&imageIndex=0&chebiId=24867'

    An override for a metaregistry is built-in to the record
    >>> get_iri("kisao:0000057", provider="ols")
    'https://www.ebi.ac.uk/ols/ontologies/kisao/terms?iri=http://www.biomodels.net/kisao/KISAO#KISAO_0000057'
    >>> get_iri("kisao:0000057", provider="bioportal")
    'https://bioportal.bioontology.org/ontologies/KISAO?p=classes&conceptid=kisao:KISAO_0000057'
    """
    return manager.get_iri(
        prefix=prefix,
        identifier=identifier,
        priority=priority,
        prefix_map=prefix_map,
        use_bioregistry_io=use_bioregistry_io,
        provider=provider,
    )


def get_link(
    prefix: str,
    identifier: str,
    priority: Optional[Sequence[str]] = None,
    use_bioregistry_io: bool = True,
) -> Optional[str]:
    """Get the best link for the CURIE, if possible."""
    warnings.warn("get_link() is deprecated. use bioregistry.get_iri() instead", DeprecationWarning)
    return get_iri(prefix=prefix, identifier=identifier, use_bioregistry_io=use_bioregistry_io)


def get_formatted_iri(metaprefix: str, prefix: str, identifier: str) -> Optional[str]:
    """Get an IRI using the format in the metaregistry.

    :param metaprefix: The metaprefix of the registry in the metaregistry
    :param prefix: A bioregistry prefix (will be mapped to the external one automatically)
    :param identifier: The identifier for the entity
    :returns: An IRI generated from the ``resolver_url`` format string of the registry, if it
        exists.

    >>> get_formatted_iri("miriam", "hgnc", "16793")
    'https://identifiers.org/hgnc:16793'
    >>> get_formatted_iri("n2t", "hgnc", "16793")
    'https://n2t.net/hgnc:16793'
    >>> get_formatted_iri("obofoundry", "fbbt", "00007294")
    'http://purl.obolibrary.org/obo/FBbt_00007294'
    """
    return manager.get_formatted_iri(metaprefix=metaprefix, prefix=prefix, identifier=identifier)
