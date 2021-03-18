# -*- coding: utf-8 -*-

"""Download registry information from OntoBee."""

import json

from bs4 import BeautifulSoup

from bioregistry.constants import BIOREGISTRY_MODULE
from bioregistry.data.external import ONTOBEE_PATH

URL = 'http://www.ontobee.org/'
LEGEND = {
    'F': 'Foundry',
    'L': 'Library',
    'N': 'Not Specified/No',
}


def get_ontobee(force: bool = False):
    if ONTOBEE_PATH.exists() and not force:
        with ONTOBEE_PATH.open() as file:
            return json.load(file)

    source_path = BIOREGISTRY_MODULE.ensure(url=URL, name='ontobee.html', force=force)
    with open(source_path) as f:
        soup = BeautifulSoup(f, 'html.parser')

    rv = {}
    for row in soup.find(id='ontologyList').find('tbody').find_all('tr'):
        cells = row.find_all('td')
        prefix = cells[1].text
        rv[prefix] = {
            'name': cells[2].text,
            'library': LEGEND[cells[3].text],
            'url': cells[1].find('a').attrs['href'],
        }

    with ONTOBEE_PATH.open('w') as file:
        json.dump(rv, file, indent=2, sort_keys=True)

    return rv


if __name__ == '__main__':
    get_ontobee()
