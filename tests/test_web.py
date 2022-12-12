# -*- coding: utf-8 -*-

"""Test for web."""
import json
import unittest
from typing import List

import rdflib
from starlette.testclient import TestClient

from bioregistry.app.impl import get_app


class TestWeb(unittest.TestCase):
    """Tests for the web application."""

    def setUp(self) -> None:
        """Set up the test case with an app."""
        self.fast_api, self.app = get_app(return_flask=True)
        self.client = TestClient(self.fast_api)

    def test_ui(self):
        """Test user-facing pages don't error."""
        for endpoint in [
            "",
            "registry",
            "registry/chebi",
            "metaregistry",
            "metaregistry/miriam",
            "metaregistry/miriam/chebi",
            # "metaregistry/miriam/chebi:24867",  # FIXME this resolves, test elsewhere
            "reference/chebi:24867",
            "collection",
            "collection/0000001",
            "context",
            "context/obo",
            "contributor",
            "contributor/0000-0003-4423-4370",
            # Meta pages
            "download",
            "summary",
            "usage",
            "schema",
            "sustainability",
            "related",
            "acknowledgements",
            # API
            "apidocs",
        ]:
            with self.subTest(endpoint=endpoint), self.app.test_client() as client:
                res = client.get(endpoint, follow_redirects=True)
                self.assertEqual(200, res.status_code, msg=f"Failed on {endpoint}\n\n{res.text}")

    def test_api_registry(self):
        """Test the registry endpoint."""
        self.assert_endpoint(
            "/api/registry",
            ["yaml", "json"],
        )

    def test_api_resource(self):
        """Test the resource endpoint."""
        self.assert_endpoint(
            "/api/registry/3dmet",
            ["yaml", "json"],
        )

        # test something that's wrong gives a proper error
        with self.subTest(fmt=None):
            res = self.client.get("/api/registry/nope")
            self.assertEqual(404, res.status_code)

    def test_ui_resource_json(self):
        """Test the UI resource with content negotiation."""
        with self.app.test_client() as client:
            res = client.get("/registry/chebi", headers={"Accept": "application/json"})
            self.assertEqual(200, res.status_code)
            self.assertEqual({"application/json"}, {t for t, _ in res.request.accept_mimetypes})
            j = res.get_json()
            self.assertIn("prefix", j)
            self.assertEqual("chebi", j["prefix"])

    def test_ui_resource_rdf(self):
        """Test the UI resource with content negotiation."""
        with self.app.test_client() as client:
            res = client.get("/registry/chebi", headers={"Accept": "text/turtle"})
            self.assertEqual(200, res.status_code)
            self.assertEqual({"text/turtle"}, {t for t, _ in res.request.accept_mimetypes})
            with self.assertRaises(ValueError, msg="result was return as JSON"):
                json.loads(res.text)
            g = rdflib.Graph()
            g.parse(res.text.encode("utf-8"), format="turtle")

    def test_api_metaregistry(self):
        """Test the metaregistry endpoint."""
        self.assert_endpoint(
            "/api/metaregistry",
            ["json", "yaml"],
        )

    def test_api_metaresource(self):
        """Test the metaresource endpoint."""
        self.assert_endpoint(
            "/api/metaregistry/miriam",
            ["json", "yaml", "turtle", "jsonld"],
        )

    def test_api_reference(self):
        """Test the reference endpoint."""
        self.assert_endpoint(
            "/api/reference/chebi:24867",
            ["json", "yaml"],
        )

    def test_api_collections(self):
        """Test the collections endpoint."""
        self.assert_endpoint(
            "/api/collection",
            ["json", "yaml"],
        )

    def test_api_collection(self):
        """Test the collection endpoint."""
        self.assert_endpoint(
            "/api/collection/0000001",
            ["json", "yaml", "turtle", "jsonld", "context"],
        )

    def test_api_contexts(self):
        """Test the contexts endpoint."""
        self.assert_endpoint(
            "/api/context",
            ["json", "yaml"],
        )

    def test_api_context(self):
        """Test the context endpoint."""
        self.assert_endpoint(
            "/api/context/obo",
            ["json", "yaml"],
        )

    def test_api_contributors(self):
        """Test the contributors endpoint."""
        self.assert_endpoint(
            "/api/contributors",
            ["json", "yaml"],
        )

    def test_api_contributor(self):
        """Test the contributor endpoint."""
        self.assert_endpoint(
            "/api/contributor/0000-0003-4423-4370",
            ["json", "yaml"],
        )

    def assert_endpoint(self, endpoint: str, formats: List[str]) -> None:
        """Test downloading the full registry as JSON."""
        self.assertTrue(endpoint.startswith("/"))
        with self.subTest(fmt=None):
            res = self.client.get(endpoint)
            self.assertEqual(200, res.status_code, msg=res.text)
        for fmt in formats:
            url = f"{endpoint}?format={fmt}"
            with self.subTest(fmt=fmt, endpoint=url):
                res = self.client.get(url)
                self.assertEqual(200, res.status_code, msg=f"Failed on format={fmt}\n\n:{res.text}")

    def test_missing_prefix(self):
        """Test missing prefix responses."""
        with self.app.test_client() as client:
            for query in ["xxxx", "xxxx:yyyy"]:
                with self.subTest(query=query):
                    res = client.get(f"/{query}")
                    self.assertEqual(404, res.status_code)

    def test_search(self):
        """Test search."""
        res = self.client.get("/api/search?q=che")
        self.assertEqual(200, res.status_code)

    def test_autocomplete(self):
        """Test search."""
        for q in ["che", "chebi", "xxxxx", "chebi:123", "chebi:dd"]:
            with self.subTest(query=q):
                res = self.client.get(f"/api/autocomplete?q={q}")
                self.assertEqual(200, res.status_code)

    def test_resolve_failures(self):
        """Test resolve failures."""
        with self.app.test_client() as client:
            for endpoint in ["chebi:ddd", "xxx:yyy", "gmelin:1"]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint)
                    self.assertEqual(404, res.status_code)

    def test_redirects(self):
        """Test healthy redirects."""
        with self.app.test_client() as client:
            for endpoint in [
                "metaregistry/miriam/chebi:24867",
                "chebi:24867",
                "health/go",
            ]:
                with self.subTest(endpoint=endpoint):
                    res = client.get(endpoint)
                    self.assertEqual(302, res.status_code)

    def test_banana_redirects(self):
        """Test banana redirects."""
        with self.app.test_client() as client:
            for prefix, identifier, location in [
                ("agrovoc", "c_2842", "http://aims.fao.org/aos/agrovoc/c_2842"),
                ("agrovoc", "2842", "http://aims.fao.org/aos/agrovoc/c_2842"),
                # Related to https://github.com/biopragmatics/bioregistry/issues/93, the app route is not greedy,
                # so it parses on the rightmost colon.
                # ("go", "0032571", "http://amigo.geneontology.org/amigo/term/GO:0032571"),
                # ("go", "GO:0032571", "http://amigo.geneontology.org/amigo/term/GO:0032571"),
            ]:
                with self.subTest(prefix=prefix, identifier=identifier):
                    res = client.get(f"/{prefix}:{identifier}", follow_redirects=False)
                    self.assertEqual(
                        302,
                        res.status_code,
                        msg=f"{prefix}\nHeaders: {res.headers}\nRequest: {res.request}",
                    )
                    self.assertEqual(location, res.headers["Location"])
