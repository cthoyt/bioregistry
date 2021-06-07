# -*- coding: utf-8 -*-

"""Extract registry information."""

from .resolve import (  # noqa
    get, get_banana, get_bioportal_prefix, get_collection, get_description, get_email, get_example,
    get_fairsharing_prefix, get_format, get_format_url, get_format_urls, get_homepage, get_identifiers_org_prefix,
    get_json_download, get_mappings, get_miriam_format, get_miriam_url_prefix, get_n2t_prefix, get_name,
    get_obo_download, get_obofoundry_format, get_obofoundry_formatter, get_obofoundry_prefix, get_ols_format,
    get_ols_prefix, get_ols_url_prefix, get_owl_download, get_pattern, get_pattern_re, get_prefixcommons_format,
    get_provides_for, get_registry, get_registry_description, get_registry_example, get_registry_homepage,
    get_registry_map, get_registry_name, get_registry_url, get_synonyms, get_version, get_versions, get_wikidata_prefix,
    has_terms, is_deprecated, is_provider, namespace_in_lui, normalize_prefix, parse_curie,
)
from .resolve_identifier import (  # noqa
    get_bioportal_url, get_default_url, get_identifiers_org_curie, get_identifiers_org_url, get_link, get_n2t_url,
    get_obofoundry_link, get_ols_link, get_providers, get_providers_list, get_registry_resolve_url, validate,
)
from .utils import read_bioregistry, read_collections, read_metaregistry, read_mismatches, read_registry  # noqa
