"""Test for validation utilities."""

import unittest

from bioregistry.validate.utils import validate_jsonld


class TestValidation(unittest.TestCase):
    """Test case for validation utilities."""

    def test_validate_jsonld(self):
        """Test validating JSON-LD."""
        with self.assertRaises(TypeError):
            validate_jsonld(None)
        with self.assertRaises(TypeError):
            validate_jsonld({})
        with self.assertRaises(TypeError):
            validate_jsonld({"@context": None})

        test_context = {
            "@context": {
                "GO": ...,
                "nope": ...,
            }
        }
        warnings, errors = validate_jsonld(test_context, strict=True)
        self.assertEqual([("GO", "nonstandard"), ("nope", "invalid")], errors)
        self.assertEqual([], warnings)

        warnings, errors = validate_jsonld(test_context, strict=False)
        self.assertEqual([("nope", "invalid")], errors)
        self.assertEqual([("GO", "nonstandard")], warnings)
