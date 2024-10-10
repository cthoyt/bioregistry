"""App builder interface."""

import json
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, Mapping, Optional, Union

import pystow
from curies.mapping_service import MappingServiceGraph, MappingServiceSPARQLProcessor
from fastapi import APIRouter, FastAPI
from flask import Flask
from flask_bootstrap import Bootstrap4
from markdown import markdown
from rdflib_endpoint import SparqlRouter
from starlette.middleware.wsgi import WSGIMiddleware

from bioregistry import curie_to_str, resource_manager, version

from .api import api_router
from .constants import BIOSCHEMAS
from .ui import ui_blueprint
from ..constants import PYDANTIC_1

if TYPE_CHECKING:
    import bioregistry

__all__ = [
    "get_app",
]

TITLE_DEFAULT = "Bioregistry"
DESCRIPTION_DEFAULT = dedent(
    """\
    An open source, community curated registry, meta-registry,
    and compact identifier (CURIE) resolver.
"""
)
FOOTER_DEFAULT = dedent(
    """\
    Developed with ❤️ by the <a href="https://gyorilab.github.io">Gyori Lab for Computational Biomedicine</a>
    at Northeastern University.<br/>
    Funded by Chan Zuckerberg Initiative (CZI) Award
    <a href="https://gyorilab.github.io/#czi-bioregistry">2023-329850</a>.<br/>
    Point of contact: <a href="https://github.com/cthoyt">@cthoyt</a>.
    (<a href="https://github.com/biopragmatics/bioregistry">Source code</a>)
"""
)
HEADER_DEFAULT = dedent(
    """\
    <p class="lead">
        The Bioregistry is an open source, community curated registry, meta-registry, and compact
        identifier resolver. Here's what that means:
    </p>
    <dl class="row">
        <dt class="col-lg-2 text-right text-nowrap">Registry</dt>
        <dd class="col-lg-10">
            A collection of prefixes and metadata for ontologies, controlled vocabularies, and other semantic
            spaces. Some other well-known registries are the <a href="http://www.obofoundry.org/">OBO Foundry</a>,
            <a href="https://identifiers.org">Identifiers.org</a>, and
            the <a href="https://www.ebi.ac.uk/ols/index">OLS</a>.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Metaregistry</dt>
        <dd class="col-lg-10">
            A collection of metadata about registries and mappings between their constituent prefixes. For
            example, <a href="https://www.ebi.ac.uk/chebi">ChEBI</a> appears in all of the example registries
            from above. So far, the Bioregistry is the <i>only</i> metaregistry.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Resolver</dt>
        <dd class="col-lg-10">
            A tool for mapping compact URIs (CURIEs) of the form <code>prefix:identifier</code> to HTML and
            structured content providers. Some other well-known resolvers are
            <a href="https://identifiers.org">Identifiers.org</a> and <a href="https://n2t.net/">Name-To-Thing</a>.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Open Source</dt>
        <dd class="col-lg-10">
            Anyone can <a href="https://github.com/biopragmatics/bioregistry/issues/new/choose">suggest
            improvements</a> or make pull requests to update the underlying database, which is stored in
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json">
                JSON</a> on GitHub where the community can engage in an open review process.
        </dd>
        <dt class="col-lg-2 text-right text-nowrap">Community</dt>
        <dd class="col-lg-10">
            Governed by public, well-defined
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/docs/CONTRIBUTING.md">contribution
                guidelines</a>,
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/docs/CODE_OF_CONDUCT.md">code of
            conduct</a>, and
            <a href="https://github.com/biopragmatics/bioregistry/blob/main/docs/GOVERNANCE.md">project
                governance</a> to promote the project's inclusivity and longevity.
        </dd>
    </dl>
"""
)
RESOURCES_SUBHEADER_DEFAULT = dedent(
    """\
    <p style="margin-bottom: 0">
        Anyone can <a href="https://github.com/biopragmatics/bioregistry/issues/new/choose">suggest
        improvements</a>, <a href="https://github.com/biopragmatics/bioregistry/issues/new?labels=\
            New%2CPrefix&template=new-prefix.yml&title=Add+prefix+%5BX%5D">request a new prefix</a>,
             or make pull requests to update the underlying database, which is stored in
        <a href="https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json">
            JSON</a> on GitHub where the community can engage in an open review process.
    </p>
    """
)


def get_app(
    manager: Optional["bioregistry.Manager"] = None,
    config: Union[None, str, Path, Mapping[str, Any]] = None,
    first_party: bool = True,
    return_flask: bool = False,
):
    """Prepare the WSGI application.

    :param manager: A pre-configured manager. If none given, uses the default manager.
    :param config: Additional configuration to be passed to the flask application. See below.
    :param first_party: Set to true if deploying the "canonical" bioregistry instance
    :param return_flask: Set to true to get internal flask app
    :returns: An instantiated WSGI application
    :raises ValueError: if there's an issue with the configuration's integrity
    """
    app = Flask(__name__)

    if manager is None:
        manager = resource_manager.manager

    if isinstance(config, (str, Path)):
        with open(config) as file:
            conf = json.load(file)
    elif config is None:
        conf = {}
    else:
        conf = config
    conf.setdefault("METAREGISTRY_TITLE", TITLE_DEFAULT)
    conf.setdefault("METAREGISTRY_DESCRIPTION", DESCRIPTION_DEFAULT)
    conf.setdefault("METAREGISTRY_FOOTER", FOOTER_DEFAULT)
    conf.setdefault("METAREGISTRY_HEADER", HEADER_DEFAULT)
    conf.setdefault("METAREGISTRY_RESOURCES_SUBHEADER", RESOURCES_SUBHEADER_DEFAULT)
    conf.setdefault("METAREGISTRY_VERSION", version.get_version())
    example_prefix = conf.setdefault("METAREGISTRY_EXAMPLE_PREFIX", "chebi")
    conf.setdefault("METAREGISTRY_EXAMPLE_IDENTIFIER", "138488")
    conf.setdefault("METAREGISTRY_FIRST_PARTY", first_party)
    conf.setdefault("METAREGISTRY_CONTACT_NAME", "Charles Tapley Hoyt")
    conf.setdefault("METAREGISTRY_CONTACT_EMAIL", "cthoyt@gmail.com")
    conf.setdefault("METAREGISTRY_LICENSE_NAME", "MIT License")
    conf.setdefault(
        "METAREGISTRY_LICENSE_URL", "https://github.com/biopragmatics/bioregistry/blob/main/LICENSE"
    )

    resource = manager.registry.get(example_prefix)
    if resource is None:
        raise ValueError(
            f"{example_prefix} is not available as a prefix. Set a different METAREGISTRY_EXAMPLE_PREFIX"
        )
    if resource.get_example() is None:
        raise ValueError("Must use an example prefix with an example identifier")
    if resource.get_uri_format() is None:
        raise ValueError("Must use an example prefix with a URI format")

    # note from klas:
    # "host": removeprefix(removeprefix(manager.base_url, "https://"), "http://"),

    Bootstrap4(app)

    app.register_blueprint(ui_blueprint)

    app.config.update(conf)
    app.manager = manager

    if app.config.get("METAREGISTRY_FIRST_PARTY"):
        app.config.setdefault("METAREGISTRY_BIOSCHEMAS", BIOSCHEMAS)

    fast_api = FastAPI(
        openapi_tags=_get_tags_metadata(conf, manager),
        title=conf["METAREGISTRY_TITLE"],
        description=conf["METAREGISTRY_DESCRIPTION"],
        contact={
            "name": conf["METAREGISTRY_CONTACT_NAME"],
            "email": conf["METAREGISTRY_CONTACT_EMAIL"],
        },
        license_info={
            "name": conf["METAREGISTRY_LICENSE_NAME"],
            "url": conf["METAREGISTRY_LICENSE_URL"],
        },
    )
    fast_api.manager = manager
    fast_api.include_router(api_router)
    fast_api.include_router(_get_sparql_router(app))
    fast_api.mount("/", WSGIMiddleware(app))

    analytics_api_key = conf.get("ANALYTICS_API_KEY") or pystow.get_config(
        "bioregistry", "analytics_api_key"
    )
    if analytics_api_key:
        from api_analytics.fastapi import Analytics

        fast_api.add_middleware(Analytics, api_key=analytics_api_key)  # Add middleware

    # Make manager available in all jinja templates
    app.jinja_env.globals.update(
        manager=manager,
        curie_to_str=curie_to_str,
        fastapi_url_for=fast_api.url_path_for,
        markdown=markdown,
        is_pydantic_1=PYDANTIC_1,
    )

    if return_flask:
        return fast_api, app
    return fast_api


example_query = """\
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?s ?o WHERE {
    VALUES ?s { <http://purl.obolibrary.org/obo/CHEBI_1> }
    ?s owl:sameAs ?o
}
""".rstrip()


def _get_sparql_router(app) -> APIRouter:
    sparql_graph = MappingServiceGraph(converter=app.manager.converter)
    sparql_processor = MappingServiceSPARQLProcessor(graph=sparql_graph)
    sparql_router = SparqlRouter(
        path="/sparql",
        title=f"{app.config['METAREGISTRY_TITLE']} SPARQL Service",
        description="An identifier mapping service",
        version=version.get_version(),
        example_query=example_query,
        graph=sparql_graph,
        processor=sparql_processor,
        public_url=f"{app.manager.base_url}/sparql",
    )
    return sparql_router


def _get_tags_metadata(conf, manager):
    tags_metadata = [
        {
            "name": "resource",
            "description": "Identifier resources in the registry",
            "externalDocs": {
                "description": f"{conf['METAREGISTRY_TITLE']} Resource Catalog",
                "url": f"{manager.base_url}/registry/",
            },
        },
        {
            "name": "metaresource",
            "description": "Resources representing registries",
            "externalDocs": {
                "description": f"{conf['METAREGISTRY_TITLE']} Registry Catalog",
                "url": f"{manager.base_url}/metaregistry/",
            },
        },
        {
            "name": "collection",
            "description": "Fit-for-purpose lists of prefixes",
            "externalDocs": {
                "description": f"{conf['METAREGISTRY_TITLE']} Collection Catalog",
                "url": f"{manager.base_url}/collection/",
            },
        },
    ]
    return tags_metadata
