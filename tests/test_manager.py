# -*- coding: utf-8 -*-

"""Tests for managers."""

import unittest

import pytest

import bioregistry
from bioregistry import Manager, parse_curie
from bioregistry.export.rdf_export import get_full_rdf
from bioregistry.resource_manager import MappingsDiff


class TestResourceManager(unittest.TestCase):
    """Test the registry manager."""

    def setUp(self) -> None:
        """Set up the test case with a resource manager."""
        self.manager = Manager()

    def test_get_records(self):
        """Test getting records."""
        resource = self.manager.registry["uniprot.isoform"]
        self.assertEqual("uniprot.isoform", resource.get_priority_prefix())

        prefixes = {
            resource.prefix
            for resource in self.manager.registry.values()
            if resource.get_uri_prefix()
        }
        self.assertIn(
            "uniprot.isoform",
            prefixes,
            msg="uniprot.isoform isn't registered with a URI prefix properly",
        )

        converter = self.manager.get_converter()
        prefixes = {record.prefix for record in converter.records}
        self.assertIn("uniprot.isoform", prefixes)

    def test_prefix_map(self):
        """Test getting a prefix map."""
        prefix_map = self.manager.get_prefix_map()
        # Non-obo, but need to check it works right
        self.assertIn("uniprot.isoform", prefix_map)
        self.assertEqual("http://purl.uniprot.org/isoforms/", prefix_map["uniprot.isoform"])

    def test_prefix_map_preferred(self):
        """Test using preferred prefixes in the prefix map."""
        prefix_map = self.manager.get_prefix_map(
            prefix_priority=["preferred", "default"],
            uri_prefix_priority=["obofoundry", "default"],
        )
        self.assertNotIn("fbbt", prefix_map)
        self.assertIn("FBbt", prefix_map)

        prefix_map = bioregistry.get_prefix_map(
            uri_prefix_priority=["obofoundry", "default"],
            prefix_priority=["preferred", "default"],
        )
        self.assertNotIn("fbbt", prefix_map)
        self.assertIn("FBbt", prefix_map)

    def test_rasterized_manager(self):
        """Test that generating a rasterized manager works the same for all functions."""
        rasterized_registry = self.manager._rasterized_registry()
        self.assertEqual(set(self.manager.registry), set(rasterized_registry))
        rast_manager = Manager(rasterized_registry)
        self.assertEqual(set(self.manager.registry), set(rast_manager.registry))
        self.assertEqual(self.manager.synonyms, rast_manager.synonyms)
        for prefix in self.manager.registry:
            with self.subTest(prefix=prefix):
                self.assertEqual(
                    self.manager.is_deprecated(prefix),
                    rast_manager.is_deprecated(prefix),
                )
                self.assertEqual(
                    self.manager.get_example(prefix),
                    rast_manager.get_example(prefix),
                )
                self.assertEqual(
                    self.manager.get_uri_format(prefix),
                    rast_manager.get_uri_format(prefix),
                )
                self.assertEqual(
                    self.manager.get_name(prefix),
                    rast_manager.get_name(prefix),
                )
                self.assertEqual(
                    self.manager.get_pattern(prefix),
                    rast_manager.get_pattern(prefix),
                )
                self.assertEqual(
                    self.manager.get_preferred_prefix(prefix) or prefix,
                    rast_manager.get_preferred_prefix(prefix),
                )
                self.assertEqual(
                    self.manager.get_synonyms(prefix),
                    rast_manager.get_synonyms(prefix),
                )
                self.assertEqual(
                    self.manager.get_depends_on(prefix),
                    rast_manager.get_depends_on(prefix),
                )
                self.assertEqual(
                    self.manager.get_appears_in(prefix),
                    rast_manager.get_appears_in(prefix),
                )
                self.assertEqual(
                    self.manager.get_provides_for(prefix),
                    rast_manager.get_provides_for(prefix),
                )
                self.assertEqual(
                    self.manager.get_provided_by(prefix),
                    rast_manager.get_provided_by(prefix),
                )
                self.assertEqual(
                    self.manager.get_has_canonical(prefix),
                    rast_manager.get_has_canonical(prefix),
                )
                self.assertEqual(
                    self.manager.get_canonical_for(prefix),
                    rast_manager.get_canonical_for(prefix),
                )
                self.assertEqual(
                    self.manager.get_part_of(prefix),
                    rast_manager.get_part_of(prefix),
                )
                self.assertEqual(
                    self.manager.get_has_parts(prefix),
                    rast_manager.get_has_parts(prefix),
                )

    def test_formatted_iri(self):
        """Test formatted IRI."""
        for metaprefix, prefix, identifier, uri in [
            ("miriam", "hgnc", "16793", "https://identifiers.org/hgnc:16793"),
            ("n2t", "hgnc", "16793", "https://n2t.net/hgnc:16793"),
            ("obofoundry", "fbbt", "00007294", "http://purl.obolibrary.org/obo/FBbt_00007294"),
        ]:
            with self.subTest(metaprefix=metaprefix, prefix=prefix, identifier=identifier):
                self.assertEqual(
                    uri, self.manager.get_formatted_iri(metaprefix, prefix, identifier)
                )

    def test_lookup_from(self):
        """Test the lookup_from method."""
        for metaprefix, key, normalize, expected in [
            ("obofoundry", "GO", False, "go"),
            ("obofoundry", "go", False, None),
            ("obofoundry", "go", True, "go"),
        ]:
            with self.subTest(meteprefix=metaprefix, key=key, norm=normalize):
                self.assertEqual(
                    expected, self.manager.lookup_from(metaprefix, key, normalize=normalize)
                )

    def test_curie_validation(self):
        """Test validation functions."""
        valid = [
            "go:0000001",
        ]
        for curie in valid:
            with self.subTest(curie=curie):
                self.assertTrue(self.manager.is_valid_curie(curie))

        invalid = [
            "0000001",
            "go:000001",  # too short
            "GO:0000001",
            # Wrong syntax
            "GO-0000001",
            "GO_0000001",
            # banana variations
            "go:GO:0000001",
            "GO:GO:0000001",
            "go:go:0000001",
            "go:go:000001",
            # invalid prefix
            "xxx:yyy",
            # TODO add one with no pattern validation
        ]
        for curie in invalid:
            with self.subTest(curie=curie):
                self.assertFalse(self.manager.is_valid_curie(curie))

    def test_curie_standardizable(self):
        """Test CURIEs that can be standardized."""
        valid = [
            "go:0000001",
            "GO:0000001",
            # banana variations
            "go:GO:0000001",
            "GO:GO:0000001",
            "go:go:0000001",
        ]
        for curie in valid:
            with self.subTest(curie=curie):
                self.assertTrue(self.manager.is_standardizable_curie(curie))

        invalid = [
            "0000001",
            # Too short
            "go:000001",
            "go:GO:000001",
            "GO:GO:000001",
            # Wrong syntax
            "GO-0000001",
            "GO_0000001",
            # Invalid banana (needs to be capitalized)
            "go:go:000001",
            # invalid prefix
            "xxx:yyy",
            # TODO add one with no pattern validation
        ]
        for curie in invalid:
            with self.subTest(curie=curie):
                self.assertFalse(self.manager.is_standardizable_curie(curie))

    def test_full_rdf(self):
        """Test the full dump."""
        full = get_full_rdf(self.manager)
        prefixes = {
            prefix[len("https://bioregistry.io/registry/") :]
            for prefix, in full.query(
                "SELECT ?s WHERE { ?s a <https://bioregistry.io/schema/#0000001> }"
            )
        }
        self.assertEqual(set(self.manager.registry), prefixes)

    def test_parse_curie(self):
        """Test parsing CURIEs."""
        for curie, pref, sep, p, i in [
            ("pdb:1234", False, ":", "pdb", "1234"),
            ("go:GO:1234", False, ":", "go", "1234"),
            ("go:go:1234", False, ":", "go", "1234"),
            ("go:1234", False, ":", "go", "1234"),
            ("fbbt:FBbt:1234", False, ":", "fbbt", "1234"),
            ("fbbt:fbbt:1234", False, ":", "fbbt", "1234"),
            ("fbbt:1234", False, ":", "fbbt", "1234"),
            ("go.ref:GO_REF:1234", False, ":", "go.ref", "1234"),
            ("go.ref:1234", False, ":", "go.ref", "1234"),
            ("GO_1234", False, "_", "go", "1234"),
            ("omim.ps:PS12345", False, ":", "omim.ps", "12345"),
            ("GO_1234", True, "_", "GO", "1234"),
            ("pdb:1234", True, ":", "pdb", "1234"),
        ]:
            with self.subTest(curie=curie, use_preferred=pref, sep=sep):
                actual_prefix, actual_i = parse_curie(curie, sep=sep, use_preferred=pref)
                self.assertEqual(p, actual_prefix)
                self.assertEqual(i, actual_i)

    def test_external_registry_mappings(self):
        """Test external registry mappings."""
        res = self.manager.get_external_mappings("obofoundry", "bioportal")
        self.assertIsInstance(res, MappingsDiff)
        self.assertEqual("obofoundry", res.source_metaprefix)
        self.assertEqual("bioportal", res.target_metaprefix)
        self.assertIn("gaz", res.mappings)
        self.assertEqual("GAZ", res.mappings["gaz"])
        # This is an obsolete OBO Foundry ontology so it won't get uploaded to BioPortal
        self.assertIn("loggerhead", res.source_only)
        # This is a non-ontology so it won't get in OBO Foundry
        self.assertIn("DCTERMS", res.target_only)

    @pytest.mark.slow
    def test_converter(self):
        """Test standardizing prefixes with the converter."""
        converter = self.manager.get_converter()
        self.assertEqual("meddra", converter.standardize_prefix("MEDDRA"))
        self.assertEqual("meddra", converter.standardize_prefix("MedDRA"))

        self.assertEqual("pubmed", converter.standardize_prefix("PMID"))
        self.assertEqual("pubmed", converter.standardize_prefix("PUBMED"))
        self.assertEqual("pubmed", converter.standardize_prefix("pmid"))
        self.assertEqual("pubmed", converter.standardize_prefix("pubmed"))
        self.assertEqual("pubmed", converter.standardize_prefix("PubMed"))
