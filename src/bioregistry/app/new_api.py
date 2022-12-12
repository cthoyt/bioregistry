# -*- coding: utf-8 -*-

"""FastAPI blueprint and routes."""

from typing import List, Mapping, Optional, Set

import yaml
from fastapi import APIRouter, Header, HTTPException, Path, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from bioregistry import Collection, Context, Registry, Resource
from bioregistry.app.utils import _autocomplete, _search
from bioregistry.export.rdf_export import (
    collection_to_rdf_str,
    metaresource_to_rdf_str,
    resource_to_rdf_str,
)
from bioregistry.schema import Attributable, sanitize_model
from bioregistry.schema_utils import (
    read_collections_contributions,
    read_prefix_contacts,
    read_prefix_contributions,
    read_prefix_reviews,
    read_registry_contributions,
)

__all__ = [
    "api_router",
]

api_router = APIRouter(
    prefix="/api",
)


class YAMLResponse(Response):
    """A custom response encoded in YAML."""

    media_type = "application/yaml"

    def render(self, content: BaseModel) -> bytes:
        return yaml.safe_dump(
            content.dict(
                exclude_none=True,
                exclude_unset=True,
            ),
            allow_unicode=True,
            indent=2,
        ).encode("utf-8")


RDF_MEDIA_TYPES = {
    "text/turtle": "turtle",
    "application/ld+json": "json-ld",
    "application/rdf+xml": "xml",
    "text/n3": "n3",
}


@api_router.get("/registry", response_model=Mapping[str, Resource], tags=["resource"])
def get_resources(request: Request, accept: Optional[str] = Header(default="application/json")):
    """Get all resources."""
    if accept == "application/json":
        return request.app.manager.registry
    elif accept == "application/yaml":
        x = {k: sanitize_model(resource) for k, resource in request.app.manager.registry.items()}
        return yaml.safe_dump(x, allow_unicode=True)
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


@api_router.get(
    "/registry/{prefix}",
    response_model=Resource,
    tags=["resource"],
    responses={
        200: {
            "content": {
                "application/yaml": {},
                **{k: {} for k in RDF_MEDIA_TYPES},
            },
        },
    },
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def get_resource(
    request: Request,
    prefix: str = Path(
        title="Prefix", description="The Bioregistry prefix for the entry", example="doid"
    ),
    accept: Optional[str] = Header(default="application/json"),
):
    """Get a resource."""
    resource = request.app.manager.get_resource(prefix)
    if resource is None:
        raise HTTPException(status_code=404, detail=f"Prefix not found: {prefix}")
    resource = request.app.manager.rasterized_resource(resource)
    if accept == "application/json":
        return resource
    elif accept == "application/yaml":
        return YAMLResponse(resource)
    elif accept in RDF_MEDIA_TYPES:
        return Response(
            resource_to_rdf_str(
                resource, fmt=RDF_MEDIA_TYPES[accept], encoding="utf-8", manager=request.app.manager
            ),
            media_type=accept,
        )
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


@api_router.get(
    "/metaregistry",
    response_model=Mapping[str, Registry],
    tags=["metaresource"],
    description="Get all metaresource representing registries.",
)
def get_metaresources(request: Request):
    """Get all registries."""
    return request.app.manager.metaregistry


METAPREFIX_PATH = Path(
    title="Metaprefix",
    description="The Bioregistry metaprefix for the external registry",
    example="n2t",
)


@api_router.get(
    "/metaregistry/{metaprefix}",
    response_model=Registry,
    tags=["metaresource"],
    description="Get a metaresource representing a registry.",
    responses={
        200: {
            "content": {
                "application/yaml": {},
                **{k: {} for k in RDF_MEDIA_TYPES},
            },
        },
    },
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def get_metaresource(
    request: Request,
    metaprefix: str = METAPREFIX_PATH,
    accept: Optional[str] = Header(default="application/json"),
):
    """Get all registries."""
    metaresource = request.app.manager.get_registry(metaprefix)
    if metaresource is None:
        raise HTTPException(status_code=404, detail=f"Registry not found: {metaprefix}")
    if accept == "application/json":
        return metaresource
    elif accept == "application/yaml":
        return YAMLResponse(metaresource)
    elif accept in RDF_MEDIA_TYPES:
        return Response(
            metaresource_to_rdf_str(
                metaresource,
                fmt=RDF_MEDIA_TYPES[accept],
                encoding="utf-8",
                manager=request.app.manager,
            ),
            media_type=accept,
        )
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


@api_router.get(
    "/metaregistry/{metaprefix}/registry_subset.json",
    response_model=Mapping[str, Resource],
    tags=["metaresource"],
)
def get_external_registry_slim(
    request: Request,
    metaprefix: str = METAPREFIX_PATH,
):
    """Get a slim version of the registry with only resources mapped to the given external registry."""
    manager = request.app.manager
    return {
        resource_.prefix: manager.rasterized_resource(resource_)
        for resource_ in manager.registry.values()
        if metaprefix in resource_.get_mappings()
    }


class MappingResponseMeta(BaseModel):
    len_overlap: int
    source: str
    target: str
    len_source_only: int
    len_target_only: int
    source_only: List[str]
    target_only: List[str]


class MappingResponse(BaseModel):
    meta: MappingResponseMeta
    mappings: Mapping[str, str]


@api_router.get(
    "/metaregistry/{metaprefix}/mapping/{target}",
    response_model=MappingResponse,
    tags=["metaresource"],
    description="Get mappings from the given metaresource to another",
)
def get_metaresource_external_mappings(
    request: Request,
    metaprefix: str = METAPREFIX_PATH,
    target: str = Path(title="target metaprefix"),
):
    """Get mappings between two external prefixes."""
    manager = request.app.manager
    if metaprefix not in manager.metaregistry:
        return {"bad source prefix": metaprefix}, 400
    if target not in manager.metaregistry:
        return {"bad target prefix": target}, 400
    rv = {}
    source_only = set()
    target_only = set()
    for resource in manager.registry.values():
        mappings = resource.get_mappings()
        mp1_prefix = mappings.get(metaprefix)
        mp2_prefix = mappings.get(target)
        if mp1_prefix and mp2_prefix:
            rv[mp1_prefix] = mp2_prefix
        elif mp1_prefix and not mp2_prefix:
            source_only.add(mp1_prefix)
        elif not mp1_prefix and mp2_prefix:
            target_only.add(mp2_prefix)

    return MappingResponse(
        meta=MappingResponseMeta(
            len_overlap=len(rv),
            source=metaprefix,
            target=target,
            len_source_only=len(source_only),
            len_target_only=len(target_only),
            source_only=sorted(source_only),
            target_only=sorted(target_only),
        ),
        mappings=rv,
    )


@api_router.get("/metaregistry/{metaprefix}/mappings.json", response_model=Mapping[str, str])
def bioregistry_to_external_mapping(request: Request, metaprefix: str = METAPREFIX_PATH):
    """Get mappings from the Bioregistry to an external registry."""
    if metaprefix not in request.app.manager.metaregistry:
        raise HTTPException(404, detail=f"Invalid metaprefix: {metaprefix}")
    return request.app.manager.get_registry_map(metaprefix)


@api_router.get(
    "/metaregistry/{metaprefix}/redirect/{metaidentifier}",
    tags=["metaresource"],
)
def get_metaresource_redirect(
    request: Request,
    metaprefix: str = METAPREFIX_PATH,
    metaidentifier: str = Path(description="The prefix inside the external registry"),
):
    raise NotImplementedError
    # if metaprefix not in manager.metaregistry:
    #     return abort(404, f"invalid metaprefix: {metaprefix}")
    # prefix = manager.lookup_from(metaprefix, metaidentifier, normalize=True)
    # if not prefix:
    #     return abort(404, f"invalid metaidentifier: {metaidentifier}")
    # resource = manager.get_resource(prefix)
    # assert resource is not None
    # return serialize_resource(resource, rasterize=True)


@api_router.get("/collection", response_model=Mapping[str, Collection], tags=["collection"])
def get_collections(request: Request):
    """Get all collections."""
    return request.app.manager.collections


@api_router.get(
    "/collection/{identifier}",
    response_model=Collection,
    tags=["collection"],
    responses={
        200: {
            "content": {
                "application/yaml": {},
                **{k: {} for k in RDF_MEDIA_TYPES},
            },
        },
    },
    response_model_exclude_none=True,
    response_model_exclude_unset=True,
)
def get_collection(
    request: Request,
    identifier: str = Path(
        title="Collection Identifier",
        description="The 7-digit collection identifier",
        example="0000001",
    ),
    accept: Optional[str] = Header(default="application/json"),
):
    """Get a collection."""
    collection = request.app.manager.collections.get(identifier)
    if collection is None:
        raise HTTPException(status_code=404, detail=f"Collection not found: {identifier}")
    if accept == "application/json":
        return collection
    elif accept == "application/yaml":
        return YAMLResponse(collection)
    elif accept in RDF_MEDIA_TYPES:
        return Response(
            collection_to_rdf_str(
                collection,
                fmt=RDF_MEDIA_TYPES[accept],
                encoding="utf-8",
                manager=request.app.manager,
            ),
            media_type=accept,
        )
    else:
        raise HTTPException(400, f"Bad Accept header: {accept}")


@api_router.get("/context", response_model=Mapping[str, Context], tags=["context"])
def get_contexts(request: Request):
    """Get all context."""
    return request.app.manager.contexts


@api_router.get("/context/{identifier}", response_model=Context, tags=["context"])
def get_context(
    request: Request,
    identifier: str = Path(title="Context Key", description="The context key", example="obo"),
):
    """Get a context."""
    context = request.app.manager.contexts.get(identifier)
    if context is None:
        raise HTTPException(status_code=404, detail=f"Context not found: {identifier}")
    return context


@api_router.get("/contributors", response_model=Mapping[str, Attributable], tags=["contributor"])
def get_contributors(request: Request):
    """Get all context."""
    return request.app.manager.read_contributors()


class ContributorResponse(BaseModel):
    contributor: Attributable
    prefix_contributions: Set[str]
    prefix_reviews: Set[str]
    prefix_contacts: Set[str]
    registries: Set[str]
    collections: Set[str]


@api_router.get("/contributor/{orcid}", response_model=ContributorResponse, tags=["contributor"])
def get_contributor(
    request: Request, orcid: str = Path(title="Open Researcher and Contributor Identifier")
):
    """Get all context."""
    manager = request.app.manager
    author = manager.read_contributors().get(orcid)
    if author is None:
        raise HTTPException(404, f"No contributor with orcid: {orcid}")
    return ContributorResponse(
        contributor=author,
        prefix_contributions=sorted(read_prefix_contributions(manager.registry).get(orcid, [])),
        prefix_reviews=sorted(read_prefix_reviews(manager.registry).get(orcid, [])),
        prefix_contacts=sorted(read_prefix_contacts(manager.registry).get(orcid, [])),
        registries=sorted(read_registry_contributions(manager.metaregistry).get(orcid, [])),
        collections=sorted(read_collections_contributions(manager.collections).get(orcid, [])),
    )


class Reference(BaseModel):
    prefix: str
    identifier: str


class IdentifierResponse(BaseModel):
    query: Reference
    providers: Mapping[str, str]


@api_router.get("/reference/{prefix}:{identifier}", response_model=IdentifierResponse)
def reference(request: Request, prefix: str, identifier: str):
    """Look up information on the reference."""
    resource = request.app.manager.get_resource(prefix)
    if resource is None:
        raise HTTPException(404, f"invalid prefix: {prefix}")

    if not resource.is_standardizable_identifier(identifier):
        raise HTTPException(
            404,
            f"invalid identifier: {resource.get_curie(identifier)} for pattern {resource.get_pattern(prefix)}",
        )
    providers = resource.get_providers(identifier)
    if not providers:
        raise HTTPException(404, f"no providers available for {resource.get_curie(identifier)}")

    return IdentifierResponse(
        query=Reference(prefix=prefix, identifier=identifier),
        providers=providers,
    )


@api_router.get("/context.jsonld")
def generate_context_json_ld(
    request: Request,
    prefix: List[str] = Query(description="The prefix for the entry. Can be given multiple."),
):
    """Generate an *ad-hoc* context JSON-LD file from the given parameters.

    You can either give prefixes as a comma-separated list like:

    https://bioregistry.io/api/context.jsonld?prefix=go,doid,oa

    or you can use multiple entries for "prefix" like:

    https://bioregistry.io/api/context.jsonld?prefix=go&prefix=doid&prefix=oa
    """  # noqa:DAR101,DAR201
    manager = request.app.manager
    prefix_map = {}
    for arg in prefix:
        for prefix in arg.split(","):
            prefix = manager.normalize_prefix(prefix.strip())
            if prefix is None:
                continue
            uri_prefix = manager.get_uri_prefix(prefix)
            if uri_prefix is None:
                continue
            prefix_map[prefix] = uri_prefix

    return JSONResponse(
        {
            "@context": prefix_map,
        }
    )


@api_router.get("/autocomplete")
def autocomplete(
    request: Request,
    q: str = Query(description="A query for the prefix"),
):
    """Complete a resolution query.

    ---
    parameters:
    - name: q
      in: query
      description: The prefix for the entry
      required: true
      type: string
    """  # noqa:DAR101,DAR201
    return JSONResponse(_autocomplete(request.app.manager, q))


@api_router.get("/search")
def search(
    request: Request,
    q: str = Query(description="A query for the prefix"),
):
    """Search for a prefix."""
    return JSONResponse(_search(request.app.manager, q))
