"""Tests for the local SPARQL endpoint."""

import csv
import unittest
from typing import Set, Tuple
from xml import etree

import requests

PING_SPARQL = 'SELECT ?s ?o WHERE { BIND("hello" as ?s) . BIND("there" as ?o) . }'
# NOTE: federated queries need to use docker internal URL
DOCKER_BIOREGISTRY = "http://bioregistry:8766/sparql"
LOCAL_BIOREGISTRY = "http://localhost:8888/sparql"
LOCAL_BLAZEGRAPH = "http://localhost:8889/blazegraph/namespace/kb/sparql"
LOCAL_VIRTUOSO = "http://localhost:8890/sparql"


def _handle_res_xml(res: requests.Response) -> Set[Tuple[str, str]]:
    root = etree.ElementTree.fromstring(res.text)  # noqa:S314
    results = root.find("{http://www.w3.org/2005/sparql-results#}results")
    rv = set()
    for result in results:
        parsed_result = {
            binding.attrib["name"]: binding.find("{http://www.w3.org/2005/sparql-results#}uri").text
            for binding in result
        }
        rv.add((parsed_result["s"], parsed_result["o"]))
    return rv


def _handle_res_json(res: requests.Response) -> Set[Tuple[str, str]]:
    res_json = res.json()
    return {
        (record["s"]["value"], record["o"]["value"]) for record in res_json["results"]["bindings"]
    }


def _handle_res_csv(res: requests.Response) -> Set[Tuple[str, str]]:
    reader = csv.DictReader(res.text.splitlines())
    return {(record["s"], record["o"]) for record in reader}


HANDLERS = {
    "application/json": _handle_res_json,
    "application/sparql-results+xml": _handle_res_xml,
    "text/csv": _handle_res_csv,
}


def get(endpoint: str, sparql: str, accept) -> Set[Tuple[str, str]]:
    """Get a response from a given SPARQL query."""
    res = requests.get(
        endpoint,
        params={"query": sparql},
        headers={"accept": accept},
    )
    func = HANDLERS[accept]
    return func(res)


def sparql_service_available(endpoint: str) -> bool:
    """Test if a SPARQL service is running."""
    try:
        records = get(endpoint, PING_SPARQL, "application/json")
    except requests.exceptions.ConnectionError:
        return False
    return list(records) == [("hello", "there")]


SPARQL_VALUES = f"""\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?s ?o WHERE {{
    SERVICE <{DOCKER_BIOREGISTRY}> {{
        VALUES ?s {{ <http://purl.obolibrary.org/obo/CHEBI_24867> }} .
        ?s owl:sameAs ?o .
    }}
}}
""".rstrip()

SPARQL_SIMPLE = f"""\
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT DISTINCT ?s ?o WHERE {{
    SERVICE <{DOCKER_BIOREGISTRY}> {{
        <http://purl.obolibrary.org/obo/CHEBI_24867> owl:sameAs ?o .
        ?s owl:sameAs ?o .
    }}
}}
""".rstrip()


@unittest.skipUnless(
    sparql_service_available(LOCAL_BIOREGISTRY), reason="No local Bioregistry is running"
)
class TestSPARQL(unittest.TestCase):
    """Tests for federated SPARQL queries to the Bioregistry mapping service."""

    def assert_endpoint(self, endpoint: str, query: str, *, accept: str):
        """Assert the endpoint returns favorable results."""
        records = get(endpoint, query, accept=accept)
        self.assertIn(
            ("http://purl.obolibrary.org/obo/CHEBI_24867", "https://bioregistry.io/chebi:24867"),
            records,
        )

    @unittest.skipUnless(
        sparql_service_available(LOCAL_BLAZEGRAPH), reason="No local BlazeGraph is running"
    )
    def test_federate_blazegraph(self):
        """Test federating on a Blazegraph triplestore.

        To run blazegraph locally: docker compose up
        """
        for mimetype in HANDLERS:
            with self.subTest(mimetype=mimetype):
                self.assert_endpoint(LOCAL_BLAZEGRAPH, SPARQL_SIMPLE, accept=mimetype)
                self.assert_endpoint(LOCAL_BLAZEGRAPH, SPARQL_VALUES, accept=mimetype)

    @unittest.skipUnless(
        sparql_service_available(LOCAL_VIRTUOSO), reason="No local Virtuoso is running"
    )
    def test_federate_virtuoso(self):
        """Test federating on a OpenLink Virtuoso triplestore.

        To run Virtuoso locally:
        1. docker compose up
        2. docker compose exec virtuoso isql -U dba -P dba exec='GRANT "SPARQL_SELECT_FED" TO "SPARQL";'
        """
        for mimetype in HANDLERS:
            with self.subTest(mimetype=mimetype):
                self.assert_endpoint(LOCAL_VIRTUOSO, SPARQL_SIMPLE, accept=mimetype)
                # TODO: Virtuoso fails to resolves VALUES in federated query
                # self.assert_endpoint(LOCAL_VIRTUOSO, SPARQL_VALUES, accept=mimetype)
