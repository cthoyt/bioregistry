<p align="center">
  <img src="https://github.com/biopragmatics/bioregistry/raw/main/docs/source/logo.png" height="150">
</p>

<h1 align="center">
    Bioregistry
</h1>

<p align="center">
    <a href="https://github.com/biopragmatics/bioregistry/actions?query=workflow%3ATests">
        <img alt="Tests" src="https://github.com/biopragmatics/bioregistry/workflows/Tests/badge.svg" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI" src="https://img.shields.io/pypi/v/bioregistry" />
    </a>
    <a href="https://pypi.org/project/bioregistry">
        <img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/bioregistry" />
    </a>
    <a href="https://github.com/biopragmatics/bioregistry/blob/main/LICENSE">
        <img alt="PyPI - License" src="https://img.shields.io/pypi/l/bioregistry" />
    </a>
    <a href='https://bioregistry.readthedocs.io/en/latest/?badge=latest'>
        <img src='https://readthedocs.org/projects/bioregistry/badge/?version=latest' alt='Documentation Status' />
    </a>
    <a href="https://zenodo.org/badge/latestdoi/319481281">
        <img src="https://zenodo.org/badge/319481281.svg" alt="DOI">
    </a>
    <a href="https://github.com/psf/black">
        <img src="https://img.shields.io/badge/code%20style-black-000000.svg" alt="Code style: black">
    </a>
    <a href="https://github.com/biopragmatics/bioregistry/blob/main/.github/CODE_OF_CONDUCT.md">
        <img alt="Contributor Covenant" src="https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg" />
    </a>
</p>

<p align="center">
   A community-driven integrative meta-registry of life science databases, ontologies, and other resources.
   <br />More information <a href="https://bioregistry.io/summary">here</a>.
</p>

The Bioregistry can be accessed, searched, and queried through its associated website at
https://bioregistry.io.

### 📥 Download

The underlying data of the Bioregistry can be downloaded (or edited) directly
from [here](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/).
Several exports to YAML, TSV, and RDF, including consensus views over the
registry, are built on a nightly basis and can be downloaded via the
[`exports/`](https://github.com/biopragmatics/bioregistry/tree/main/exports) directory.

The manually curated portions of these data are available under the
[CC0 1.0 Universal License](https://creativecommons.org/publicdomain/zero/1.0/).
Aggregated data are redistributed under their original licenses.

## 🙏 Contributing

Contributions are both welcomed and encouraged. Contribution guidelines for new
prefix requests, record edits, record removals, and code updates are available
in [CONTRIBUTING.md](docs/CONTRIBUTING.md).

The most simple contribution is to submit an issue:

- Submit a new prefix using the [issue template](https://github.com/biopragmatics/bioregistry/issues/new?assignees=cthoyt&labels=New%2CPrefix&template=new-prefix.yml&title=Add+prefix+%5BX%5D). A new pull request will be generated automatically for you.
- Update an existing record using one of the [existing issue templates](https://github.com/biopragmatics/bioregistry/issues/new/choose) (e.g., for updating a record's regular expression, merging two prefixes).
- For any updates that don't have a corresponding template, feel free to start with a [blank issue](https://github.com/biopragmatics/bioregistry/issues/new).

If you want to make a direct contribution, feel free to make edits directly to
the [bioregistry.json](https://github.com/biopragmatics/bioregistry/blob/main/src/bioregistry/data/bioregistry.json)
file either through the GitHub interface or locally by [forking the repository](https://github.com/biopragmatics/bioregistry/blob/main/docs/CONTRIBUTING.md#code-contribution).

If you want to make a contribution but don't know where to start, you can check
[this list](https://biopragmatics.github.io/bioregistry/curation/) of curation
To-Do's that's automatically generated daily, including more detailed
information on how to contribute.

## ⚖️ Governance

The Bioregistry is maintained by a Review Team and Core Development team
whose memberships and duties are described in the
[Project Governance](docs/GOVERNANCE.md).

## 🧹 Maintenance

### 🫀 Health Report

The Bioregistry runs some automated tests weekly to check that various metadata haven't gone stale. For example,
it checks that the homepages are still available and that each provider URL is still able to resolve.

It has a dedicated [dashboard](https://biopragmatics.github.io/bioregistry/health) that is not part of the main
Bioregistry site.

### ♻️ Update

The database is automatically updated daily thanks to scheduled workflows in GitHub Actions. The workflow's
configuration can be found [here](https://github.com/biopragmatics/bioregistry/blob/main/.github/workflows/update.yml)
and the last run can be seen [here](https://github.com/biopragmatics/bioregistry/actions?query=workflow%3A%22Update+Data%22).
Further, a [changelog](https://github.com/biopragmatics/bioregistry/commits?author=actions-user) can be recapitulated from the
commits of the GitHub Actions bot.

If you want to manually update the database, run the following:

```shell
$ tox -e update
```

Make sure that you have valid environment variables or `pystow` configurations
for `BIOPORTAL_API_KEY`, `ECOPORTAL_API_KEY`, `AGROPORTAL_API_KEY`,
`FAIRSHARING_LOGIN`, and `FAIRSHARING_PASSWORD`.

## 🚀 Installation

The Bioregistry can be installed from [PyPI](https://pypi.org/project/bioregistry/) with:

```shell
$ pip install bioregistry
```

It can be installed in development mode for local curation with:

```shell
$ git clone https://github.com/biopragmatics/bioregistry.git
$ cd bioregistry
$ pip install --editable .
```

Build the docs locally with `tox -e ldocs` then view by opening
`docs/build/html/index.html`.

<details>
  <summary>See the instructions to run the tests</summary>

Having [`tox`](https://tox.wiki/en/latest/installation.html) installed is required to run the tests. Optionally to run all tests you will need to start the Bioregistry, a Virtuoso endpoint, and a Blazegraph endpoint using `docker compose`:

```shell
$ docker compose up
```

The first time you deploy the docker compose stack, you will need to run an additional command from another terminal, in this repository root folder, to enable federated query in Virtuoso:

```shell
$ docker compose exec virtuoso isql -U dba -P dba exec='GRANT "SPARQL_SELECT_FED" TO "SPARQL";'
```

After cloning the repository and installing the dependencies, the unit tests in the `tests/` folder can be run reproducibly with:

```shell
$ tox
```

Additionally, these tests are automatically re-run with each commit in a [GitHub Action](https://github.com/biopragmatics/bioregistry/actions/workflows/tests.yml).

</details>

## 💪 Usage

### Normalizing Prefixes

The Bioregistry can be used to normalize prefixes across MIRIAM and all the (very plentiful) variants that pop up in
ontologies in OBO Foundry and the OLS with the `normalize_prefix()` function.

```python
from bioregistry import normalize_prefix

# Doesn't affect canonical prefixes
assert 'ncbitaxon' == normalize_prefix('ncbitaxon')

# This works for uppercased prefixes, like:
assert 'chebi' == normalize_prefix("CHEBI")

# This works for mixed case prefixes like
assert 'fbbt' == normalize_prefix("FBbt")

# This works for synonym prefixes, like:
assert 'ncbitaxon' == normalize_prefix('taxonomy')

# This works for common mistaken prefixes, like:
assert 'pubchem.compound' == normalize_prefix('pubchem')

# This works for prefixes that are often written many ways, like:
assert 'eccode' == normalize_prefix('ec-code')
assert 'eccode' == normalize_prefix('EC_CODE')

# If a prefix is not registered, it gives back `None`
assert normalize_prefix('not a real key') is None
```

### Parsing CURIEs

The Bioregistry supports parsing a CURIE into a pair of normalized prefix
and identifier using the `parse_curie()` function:

```python
from bioregistry import parse_curie

# Obvious for canonical CURIEs
assert ('chebi', '1234') == parse_curie('chebi:1234')

# Normalize mixed case prefixes
assert ('fbbt', '00007294') == parse_curie('FBbt:00007294')

# Normalize common mistaken prefixes
assert ('pubchem.compound', '1234') == parse_curie('pubchem:1234')

# Remove the redundant prefix and normalize
assert ('go', '1234') == parse_curie('GO:GO:1234')
```

This will also apply the same normalization rules for prefixes from the previous
section on normalizing prefixes for the remaining examples.

### Normalizing CURIEs

The Bioregistry supports converting a CURIE to a canonical CURIE by normalizing
the prefix and removing redundant namespaces embedded in LUIs with the
`normalize_curie()` function.

```python
from bioregistry import normalize_curie

# Idempotent to canonical CURIEs
assert 'chebi:1234' == normalize_curie('chebi:1234')

# Normalize common mistaken prefixes
assert 'pubchem.compound:1234' == normalize_curie('pubchem:1234')

# Normalize mixed case prefixes
assert 'fbbt:1234' == normalize_curie('FBbt:1234')

# Remove the redundant prefix and normalize
assert 'go:1234' == normalize_curie('GO:GO:1234')
```

### Parsing IRIs

The Bioregistry can be used to parse CURIEs from IRIs due to its vast registry of provider URL
strings and additional programmatic logic implemented with Python. It can parse OBO Library PURLs,
IRIs from the OLS and identifiers.org, IRIs from the Bioregistry website, and any other IRIs
from well-formed providers registered in the Bioregistry. The `parse_iri()` function
gets a pre-parsed CURIE, while the `curie_from_iri()` function makes a canonical CURIE
from the pre-parsed CURIE.

```python
from bioregistry import curie_from_iri, parse_iri

# First-party IRI
assert ('chebi', '24867') == parse_iri('https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867')
assert 'chebi:24867' == curie_from_iri('https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867')

# OBO Library PURL
assert ('chebi', '24867') == parse_iri('http://purl.obolibrary.org/obo/CHEBI_24867')
assert 'chebi:24867' == curie_from_iri('http://purl.obolibrary.org/obo/CHEBI_24867')

# OLS IRI
assert ('chebi', '24867') == parse_iri('https://www.ebi.ac.uk/ols/ontologies/chebi/terms?iri=http://purl.obolibrary.org/obo/CHEBI_24867')
assert 'chebi:24867' == curie_from_iri('https://www.ebi.ac.uk/ols/ontologies/chebi/terms?iri=http://purl.obolibrary.org/obo/CHEBI_24867')

# Identifiers.org IRIs (with varying usage of HTTP(s) and colon/slash separator
assert ('chebi', '24867') == parse_iri('https://identifiers.org/CHEBI:24867')
assert ('chebi', '24867') == parse_iri('http://identifiers.org/CHEBI:24867')
assert ('chebi', '24867') == parse_iri('https://identifiers.org/CHEBI/24867')
assert ('chebi', '24867') == parse_iri('http://identifiers.org/CHEBI/24867')

# Bioregistry IRI
assert ('chebi', '24867') == parse_iri('https://bioregistry.io/chebi:24867')
```

In general, the Bioregistry knows how to parse both the http and https variants
of any given URI:

```python
from bioregistry import parse_iri

assert ('neuronames', '268') == parse_iri("http://braininfo.rprc.washington.edu/centraldirectory.aspx?ID=268")
assert ('neuronames', '268') == parse_iri("https://braininfo.rprc.washington.edu/centraldirectory.aspx?ID=268")
```

### Generating IRIs

You can generate an IRI from either a CURIE or a pre-parsed CURIE
(i.e., a 2-tuple of a prefix and identifier) with the `get_iri()` function.
By default, it uses the following priorities:

1. Custom prefix map (`custom`)
2. First-party IRI (`default`)
3. Identifiers.org / MIRIAM (`miriam`)
4. Ontology Lookup Service (`ols`)
5. OBO PURL (`obofoundry`)
6. Name-to-Thing (`n2t`)
7. BioPortal (`bioportal`)

```python
from bioregistry import get_iri

assert get_iri("chebi", "24867") == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'
assert get_iri("chebi:24867") == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'
```

It's possible to change the default priority list by passing an alternate
sequence of metaprefixes to the `priority` keyword (see above). For example, if
you're working with OBO ontologies, you might want to make OBO PURLs the highest
priority and when OBO PURLs can't be generated, default to something else:

```python
from bioregistry import get_iri

priority = ["obofoundry", "default", "miriam", "ols", "n2t", "bioportal"]
assert get_iri("chebi:24867", priority=priority) == 'http://purl.obolibrary.org/obo/CHEBI_24867'
assert get_iri("hgnc:1234", priority=priority) == 'https://bioregistry.io/hgnc:1234' 
```

Even deeper, you can add (or override) any of the Bioregistry's default prefix
map with the `prefix_map` keyword:

```python
from bioregistry import get_iri

prefix_map = {
   "myprefix": "https://example.org/myprefix/",
   "chebi": "https://example.org/chebi/",
}
assert get_iri("chebi:24867", prefix_map=prefix_map) == 'https://example.org/chebi/24867'
assert get_iri("myprefix:1234", prefix_map=prefix_map) == 'https://example.org/myprefix/1234'
```

A custom prefix map can be supplied in combination with a priority list, using
the `"custom"` key for changing the priority of the custom prefix map.

```python
from bioregistry import get_iri

prefix_map = {"lipidmaps": "https://example.org/lipidmaps/"}
priority = ["obofoundry", "custom", "default", "bioregistry"]
assert get_iri("chebi:24867", prefix_map=prefix_map, priority=priority) == \
    'http://purl.obolibrary.org/obo/CHEBI_24867'
assert get_iri("lipidmaps:1234", prefix_map=prefix_map, priority=priority) == \
    'https://example.org/lipidmaps/1234'
```

Alternatively, there are direct functions for generating IRIs for different
registries:

```python
import bioregistry as br

# Bioregistry IRI
assert br.get_bioregistry_iri('chebi', '24867') == 'https://bioregistry.io/chebi:24867'

# Default Provider
assert br.get_default_iri('chebi', '24867') == 'https://www.ebi.ac.uk/chebi/searchId.do?chebiId=CHEBI:24867'

# OBO Library
assert br.get_obofoundry_iri('chebi', '24867') == 'http://purl.obolibrary.org/obo/CHEBI_24867'

# OLS IRI
assert br.get_ols_iri('chebi', '24867') ==
       'https://www.ebi.ac.uk/ols/ontologies/chebi/terms?iri=http://purl.obolibrary.org/obo/CHEBI_24867'

# Bioportal IRI
assert br.get_bioportal_iri('chebi', '24867') == \
    'https://bioportal.bioontology.org/ontologies/CHEBI/?p=classes&conceptid=http://purl.obolibrary.org/obo/CHEBI_24867'

# Identifiers.org IRI
assert br.get_identifiers_org_iri('chebi', '24867') == 'https://identifiers.org/CHEBI:24867'

# Name-to-Thing IRI
assert br.get_n2t_iri('chebi', '24867') == 'https://n2t.net/chebi:24867'
```

Each of these functions could also return `None` if there isn't a provider available or if the prefix
can't be mapped to the various resources.

### Prefix Map

The Bioregistry can be used to generate prefix maps with various flavors
depending on your context. Prioritization works the same way as when generating
IRIs.

```python
from bioregistry import get_prefix_map

# Standard
prefix_map = get_prefix_map()

# Prioritize OBO prefixes over bioregistry
priority = ["obofoundry", "default", "miriam", "ols", "n2t", "bioportal"]
prefix_map = get_prefix_map(uri_prefix_priority=priority)

# Provide custom remapping that doesn't have prioritization logic
remapping = {"chebi": "CHEBI"}
prefix_map = get_prefix_map(remapping=remapping)
```

### Getting Metadata

The pattern for an entry in the Bioregistry can be looked up quickly with `get_pattern()` if
it exists. It prefers the custom curated, then MIRIAM, then Wikidata pattern.

```python
import bioregistry

assert '^GO:\\d{7}$' == bioregistry.get_pattern('go')
```

Entries in the Bioregistry can be checked for deprecation with the `is_deprecated()` function. MIRIAM and OBO Foundry
don't often agree - OBO Foundry takes precedence since it seems to be updated more often.

```python
import bioregistry

assert bioregistry.is_deprecated('nmr')
assert not bioregistry.is_deprecated('efo')
```

Entries in the Bioregistry can be looked up with the `get_resource()` function.

```python
import bioregistry

entry = bioregistry.get_resource('taxonomy')
# there are lots of mysteries to discover in this dictionary!
```

The full Bioregistry can be read in a Python project using:

```python
import bioregistry

registry = bioregistry.read_registry()
```

### 🕸️ Resolver App

After installation with the `[web]` extras, the Bioregistry web application
can be run with the following code:

```shell
$ python -m pip install bioregistry[web]
$ bioregistry web
```

to run a web app that functions like Identifiers.org, but backed by the Bioregistry.
A public instance of this app is hosted by the [INDRA Lab](https://indralab.github.io) at
https://bioregistry.io.

## 👋 Attribution

### ⚖️ License

The code in this repository is licensed under the
[MIT License](https://github.com/biopragmatics/bioregistry/blob/main/LICENSE).

### 📛 Badge

If you use the Bioregistry in your code, support us by including our
badge in your project's README.md:

```markdown
[![Powered by the Bioregistry](https://img.shields.io/static/v1?label=Powered%20by&message=Bioregistry&color=BA274A&style=flat&logo=image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACgAAAAoCAYAAACM/rhtAAAACXBIWXMAAAEnAAABJwGNvPDMAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAACi9JREFUWIWtmXl41MUZxz/z291sstmQO9mQG0ISwHBtOOSwgpUQhApWgUfEowKigKI81actypaqFbWPVkGFFKU0Vgs+YgvhEAoqEUESrnDlEEhCbkLYJtlkk9399Y/N/rKbzQXt96+Zed+Z9/t7Z+adeecnuA1s5yFVSGrLOAf2qTiEEYlUZKIAfYdKE7KoBLkQSc4XgkPfXxz/owmT41ZtiVtR3j94eqxQq5aDeASIvkVb12RBtt0mb5xZsvfa/5XgnqTMcI3Eq7IQjwM+7jJJo8YvNhK/qDBUOl8A7JZWWqqu01Jeg6Pd1nW4NuBjjax6eWrRruv/M8EDqTMflmXeB0Jcbb6RIRhmTCJ0ymgC0wYjadTd9nW0tWMu+In63NNU7c3FWtvgJpXrZVlakVGU8/ltEcwzGjU3miI/ABa72vwTB5K45AEi7x2PUEl9fZsHZLuDmgPHuLJpJ82lle6iTSH6mpXp+fnt/Sa4yzhbp22yfwFkgnMaBy17kPhFmQh1997qLxztNkq35XB505fINtf0iz1WvfTQ7Pxdlj4Jdnjuny5yvpEhjHh7FQOGD/YyZi4owS86HJ+QQMDpJaBf3jUXlHD21+8q0y4LDppV/vfNO7+jzV3Pa6SOac0E8I8fSPonpm7JAVR+eRhzwU/Ofj+e49tpT/HdtGXcyLvQJ8HAtCTGfmJCF2dwfpTMz4NszX/uqqdyr+xPyVwoEK+C03PGrDX4GkJ7NBJ+txH/hCgAit7cRlNxOY62dmzmZgwzJvZJUh2gI/xnRmoOHsfe3AqQ/kho0qXs+pLzLh3FgwdT54YKxLsAQq0mbf1zHuTsltZejemHJSrlgGGDPGTXc09zdM5qTi59jZbKOg+Zb1QYI95+XokEQogPDifPDnPJFQ8uCkl8FyGmACQtn4dhxp3KINX7jnHi0ZeJnT8dla8Plbu+48zzfyJ08kh8ggIACB4zlIAhsURm3EnML6eB6Fzep1a+SUt5DS2VddTs+4GQccPRhgV1kowIQRaChhMXAPxkIev/Vl+8R/HgnqTMmI4gjH/iQOIXZSqdzQUlXDB9RPyi+1DrdVx67WMursvCkDERXYxB0ROSIOKecURMG+tBzkXAhbYbZk6teNPLkwmPzUIX71wuMiw+MHx2nEJQrWIFHSdE4pIHlFDisLZxYe1HhIwfTtLK+RSu30rVnlxGvrOapOcW9DsW3vH6CgKS4zxIXlz3Fw8dSaMmcfEcV9XHYbc/DSCZMEkgFoJzY0TeO17pVL7jANbaBoauWUJlTi4VOw+T9sazBKYl0ZB/qV/kALThQRi3vOJB0lpzw0vPMONOtOHOqRcyi7bzkEqanJo3HogBMGROUrziaGundGsOsQsyUPn6UPx2NvELZxIybhinn3uLyx9uVwaW7XbqjxdQmr2X0uy93Dh+Dtlu9zCu9vdj1PsvEWwcii7OwJAXFnoRFCoVhoxJrmr0gOQWo9qBfaorXodOHq0o1x8roN3cSMyC6ZT942uQBIlL53Jl804sV6oY9/fXAGg4WcjFdZuxlFV7GNPFRzFs7VKCRiV7ejJrTa/eDr1rFKXZOQCocEyTgHQAyUdD4B2d4cF8pohg4zC0YUFU7z5C9Jy7sVvbKPtsH6GT0tCGBtFwspBTz/zRixyApbSKk8te5+aZ4l4JdUVQWpIScmQhjGocUjJCRhcTieSjURQTF89FtttpuVaLpaya8Knp1B3OQ5Zlag/nU//9cmScS6EnONrauWjazIQv3kCoVD3quUPS+uAXHU7z1SpATpEQchSA78AwD0WVnxa1XkdjURlCJRGQHMfN/EuEjk9jyr4NRN47Hltjc58Gm0sraTjZ/w3l5BLuKkZJdFzT1f5+3Sq3NZjRDNAjaX1orb2BX2wEmkA9fvGGbvW7Q+OlUu+2wlIqdx+h3dzkJVPrda5iQJ93p+DRqcQ/PhsAw8xJ6AfHdkhuIVvoEribLl/jxKOv4Gi34T8omgnb1yOk7sdTA01AiK3J6yoGgP+gaPwHOdOP6LlTlXb3mNYXAlI8da9/e0pJBZovV2BrakYzQK/I3bg0SsiiCqClqs/0wAPB6UOVo6k3+CdEETwm1aPtP+dLlLJPSKAHOYDWCoVLlYTkKAKcCU4vO7IrhErFsLVLPXZ+V0haDcN+v8xjB9strdQfPavUA0ckefRxWNuwVNS6rBRKQB44r+Lmc5f7TRAgaFQyYzb9Dv/4gd18ASQ8/gsC0zwJNJVcw97aeWmOcDtaAW6eLXZLBchTC8EhWXbW6o+cInhMipetuu9OUvTWNnwNodzx+krlvAQIGjmECV+spyH/Ak3F5QDok+OoPXicip2HiJiWTuH6rQx6eh7BxlT0STH4xUbSUl6Df/xAIqaO9bBVn3taKUuy/ZAwYZImpvx4FYjVRgQzOec9r1vK0TmrldMiIDkO45ZXegxLLrRW13P0/heQHQ4CUhIYvfElNIHOtWaztNJ4qZQBqfFKLg3OMz135rNY624ClB0tHJcomTA5ZMGnANbaBmoOHPMy5hvZebNuLCoj71frXIN0i9pDJzj24IsIlUTCo7NI3/KyQg5ArfMleEyKBzmA6r1HO8eV+dSEySEB2G3yRpwZP1c2f+n1GjB07RIlcwNoKi7j3G839EhQF2cg6fmHmbznPRKevJ/GorIedV1wtLVzJesrV9WqQtoIHRfWjreSjwGar1ZRui3Ho7PfwHBGb3jRg6S1roGeoIuNJGBIPKV/zSF31irOrn4HXAu9B1zduhtLecelQxZZ9xTtrgC342Df8IwQyaYqBMKEWo0xaw1BI4d4DNJSWcfF32fRWnuD5NWPEDZ5lIe8NDuHq1v+ha2xGdkho4szYJg1hbj501EH6OgJ5oIS8hf/oWPm5HqNrE51vdt4nC/7k+9bIIT8GYA2Ipixn5jwjQrrZsju0XT5GubTRfiEBqFPisUvOrzPPi0VdeQ9YcJ63bWmxbzphTk7XHKvA/DrlJkfAU+Bcy2N+fA3vZK0WVoxny4idOKIfn+IO7lTz7zRObWCjdMv7VnhruOV9dws9F8u4CsAS1k1J54wYS4o6arWaaS8hvLP998yuZtnisl7wuROLkdjsKzqqtfL45FjB8gzwZnIJy6dS8Jjs3p8ausvHG3tXN26mytZO5W8Rcjsbg1Qze/X45ELHY9I7wHLXG26+CgSl8zFkDGh3zdkF2S7nep9PzhzmnK3FEGwUWOwrJr6zTdeL529EnRhf3LmfCHEBkBZiNrwIAwZkwi9a5Qzh9D6dNvXYW3jZkEJ9UdOOYPwdY/gXgdiufuGuC2C4Hy3kWXrOhmeBLQeA6jV6GLC8Y0KR613Hn+2phZaK69jqah1P/hdsCKLLIfGtnbG+f3eyfHtEHTh38mzom2SY4WQWQjE9tnBE+XIZKuQNrqCcH9wSwRdMGGSJiTnpatwTJOFMIKcgvPVX/kNIcM1gSgC8iTZfii3aEL+7fyG+C+6O8izl1GE5gAAAABJRU5ErkJggg==)](https://github.com/biopragmatics/bioregistry)
```

If your README uses reStructuredText (.rst), use this instead:

```
.. image:: https://img.shields.io/static/v1?label=Powered%20by&message=Bioregistry&color=BA274A&style=flat&logo=image/png;base64,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
    :target: https://github.com/biopragmatics/bioregistry
    :alt: Powered by the Bioregistry
```

It looks like this: [![Powered by the Bioregistry](https://img.shields.io/static/v1?label=Powered%20by&message=Bioregistry&color=BA274A&style=flat&logo=image/png;base64,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)](https://github.com/biopragmatics/bioregistry)

### 📖 Citation

> [Unifying the identification of biomedical entities with the Bioregistry](https://bioregistry.io/doi:10.1038/s41597-022-01807-3)
> <br />Hoyt, C. T., Balk, M., Callahan, T. J., Domingo-Fernandez, D., Haendel, M. A., Hegde, H. B., Himmelstein, D. S., Karis, K., Kunze, J., Lubiana, T., Matentzoglu, N., McMurry, J., Moxon, S., Mungall, C. J., Rutz, A., Unni, D. R., Willighagen, E., Winston, D., and Gyori, B. M. (2022)
> <br />*Nature Scientific Data*, s41597-022-01807-3

```bibtex
@article{Hoyt2022Bioregistry,
    author = {Hoyt, Charles Tapley and Balk, Meghan and Callahan, Tiffany J and Domingo-Fern{\'{a}}ndez, Daniel and Haendel, Melissa A and Hegde, Harshad B and Himmelstein, Daniel S and Karis, Klas and Kunze, John and Lubiana, Tiago and Matentzoglu, Nicolas and McMurry, Julie and Moxon, Sierra and Mungall, Christopher J and Rutz, Adriano and Unni, Deepak R and Willighagen, Egon and Winston, Donald and Gyori, Benjamin M},
    doi = {10.1038/s41597-022-01807-3},
    issn = {2052-4463},
    journal = {Sci. Data},
    number = {1},
    pages = {714},
    title = {{Unifying the identification of biomedical entities with the Bioregistry}},
    url = {https://doi.org/10.1038/s41597-022-01807-3},
    volume = {9},
    year = {2022}
}
```

Talks on the Bioregistry:

- [Future Curation in the Bioregistry](https://bit.ly/wpci2022-bioregistry-maintenance) (WPCI, December 2022)
- [The Bioregistry - Governance and Review Team](https://bit.ly/wpci2022-bioregistry-governance) (WPCI, December 2022)
- [Development, Maintenance, and Expansion of the Bioregistry](https://bit.ly/sorger-lab-bioregistry-2022)
  (Sorger Lab Meeting, October 2022)
- [The Bioregistry, CURIEs, and OBO Community Health](https://bit.ly/icbo2022-cth) (ICBO 2022 (September))
- [Introduction to the Bioregistry](https://bit.ly/bioregistry-short-talk) (Sorger Lab Meeting, July 2021)

### 🎁 Support

The Bioregistry was developed by the [INDRA Lab](https://indralab.github.io), a part of the
[Laboratory of Systems Pharmacology](https://hits.harvard.edu/the-program/laboratory-of-systems-pharmacology/about/)
and the [Harvard Program in Therapeutic Science (HiTS)](https://hits.harvard.edu)
at [Harvard Medical School](https://hms.harvard.edu/).

### 💰 Funding

The development of the Bioregistry is funded by the DARPA Young Faculty Award W911NF2010255 (PI: Benjamin M. Gyori).
