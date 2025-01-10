"""Intest manually curated BioPortal PURLs from :mod:`prefixmaps`, curated by Harry Caufield."""

import requests
import yaml
import bioregistry
from bioregistry.external.bioportal import get_bioportal

URL = "https://raw.githubusercontent.com/linkml/prefixmaps/main/src/prefixmaps/data/bioportal.curated.yaml"
#: A mapping from BioPortal prefixes to lists of URI prefixes to skip
BLACKLIST = {"BFO": ["http://www.ifomis.org/bfo/1.1/snap#"]}


def main():
    count = 0
    max_count = 10
    bioportal = get_bioportal(force_download=False)

    bioportal_to_bioregistry = bioregistry.get_registry_invmap("bioportal")

    res = requests.get(URL)
    data = yaml.safe_load(res.text)["prefixes"]
    for bioportal_prefix, uri_prefixes in data.items():
        if bioportal_prefix not in bioportal:
            # these are nonsense
            continue

        bioregistry_prefix = bioportal_to_bioregistry.get(bioportal_prefix)
        if bioregistry_prefix is None:
            # these might be relevant, but are not currently in the Bioregistry.
            # note that there's no quality filter on BioPortal content, and it's not
            # clear if there's a quality filter on the curation here, so we skip them
            continue

        resource = bioregistry.get_resource(bioregistry_prefix)
        bioregistry_uri_prefixes = resource.get_uri_prefixes()
        if isinstance(uri_prefixes, str):
            uri_prefixes = [uri_prefixes]
        for uri_prefix in uri_prefixes:
            if uri_prefix in BLACKLIST.get(bioportal_prefix, []):
                continue
            if uri_prefix.startswith("OBO:"):
                uri_prefix = "http://purl.obolibrary.org/obo/" + uri_prefix[len("OBO:") :]
            if uri_prefix in bioregistry_uri_prefixes:
                continue
            print(bioregistry_prefix, uri_prefix)

            if count > max_count:
                continue
            p = bioregistry.Provider(
                code="",
                name="",
                homepage="",
                description="",
                uri_format=uri_prefix + "$1",
            )
            if resource.providers is None:
                resource.providers = []
            resource.providers.append(p)
            count += 1

    bioregistry.manager.write_registry()


if __name__ == "__main__":
    main()
