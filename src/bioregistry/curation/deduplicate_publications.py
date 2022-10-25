import bioregistry
from bioregistry.schema.struct import deduplicate_publications
from tqdm import tqdm


def main():
    for resource in tqdm(bioregistry.resources()):
        if resource.publications:
            resource.publications = [p for p in deduplicate_publications(resource.publications) if p.title]
    bioregistry.manager.write_registry()


if __name__ == '__main__':
    main()
