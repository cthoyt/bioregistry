"""Add titles and missing xrefs for publications.

Run this script with python -m bioregistry.curation.clean_publications.
"""

from functools import lru_cache
from typing import Set

from manubot.cite.pubmed import get_pubmed_csl_item
from tqdm import tqdm

from bioregistry import manager
from bioregistry.schema.struct import Publication, deduplicate_publications


@lru_cache(None)
def _get_pubmed_csl_item(pmid):
    return get_pubmed_csl_item(pmid)


def _main():
    c = 0

    resources = []
    for resource in manager.registry.values():
        pubmed_ids: Set[str] = set()
        resource_publications = resource.get_publications()
        pubmed_ids.update(p.pubmed for p in resource_publications if p.pubmed)
        if pubmed_ids:
            resources.append((resource, pubmed_ids))
        elif resource.publications:
            resource.publications = deduplicate_publications(resource.publications)

    for resource, pubmed_ids in tqdm(
        resources, desc="resources with pubmeds to update", unit="resource"
    ):
        new_publications = []
        for pubmed in pubmed_ids:
            csl_item = _get_pubmed_csl_item(pubmed)
            title = csl_item.get("title", "").strip() or None
            doi = csl_item.get("DOI") or None
            pmc = csl_item.get("PMCID") or None
            if not title:
                tqdm.write(f"No title available for pubmed:{pubmed} / doi:{doi} / pmc:{pmc}")
                continue
            new_publications.append(
                Publication(
                    pubmed=pubmed,
                    title=title,
                    doi=doi and doi.lower(),
                    pmc=pmc,
                )
            )

        if not resource.publications and not new_publications:
            tqdm.write(f"error on {resource.prefix}")
        else:
            _pubs = [
                *(new_publications or []),
                *(resource.publications or []),
            ]
            if len(_pubs) == 1:
                resource.publications = _pubs
            else:
                from rich import print
                print(resource.prefix)
                print("pre")
                print(_pubs)
                resource.publications = deduplicate_publications(_pubs)
                print("post")
                print(resource.publications)
                print()

    # output every so often in case of failure
    manager.write_registry()
    tqdm.write("wrote registry")
    c = 0


if __name__ == "__main__":
    _main()
