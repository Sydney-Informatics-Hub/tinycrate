from tinycrate.jsonld_context import JSONLDContextResolver, ContextResolutionException
import unittest
import json
import os
import sys
from pathlib import Path
import tempfile
from unittest.mock import patch, MagicMock

# Add the src directory to sys.path so we can import the module
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


class TestJSONLDContextResolver(unittest.TestCase):
    """Test cases for JSONLDContextResolver"""

    def setUp(self):
        # Set up a simple test context
        self.simple_context = {
            "name": "http://schema.org/name",
            "description": "http://schema.org/description",
            "schema": "http://schema.org/",
            "@vocab": "http://example.org/vocab/",
            "complex": {"@id": "http://example.org/complex"}

        }
        self.medium_context = {
            "@context": [
                "https://w3id.org/ro/crate/1.1/context",
                {
                    "@vocab": "http://schema.org/",
                    "ldac": "https://w3id.org/ldac/terms#"
                },
                {
                    "register": "http://w3id.org/meta-share/meta-share/register",
                    "local": "arcp://name,corpus-of-oz-early-english/terms#"
                }
            ],
        }
        # Set up a complex test context like the one provided
        self.complex_context = [
            "https://w3id.org/ro/crate/1.1/context",
            {
                "@vocab": "http://schema.org/",
                "ldac": "https://w3id.org/ldac/terms#"
            },
            {
                "register": "http://w3id.org/meta-share/meta-share/register",
                "birthDateEstimateStart": "#birthDateEstimateStart",
                "birthDateEstimateEnd": "#birthDateEstimateEnd",
                "arrivalDate": "#arrivalDate",
                "arrivalDateEstimateStart": "#arrivalDateEstimateStart",
                "arrivalDateEstimateEnd": "#arrivalDateEstimateEnd",
                "bornInAustralia": "#bornInAustralia",
                "yearsLivedInAustralia": "#yearsLivedInAustralia",
                "socialClass": "#socialClass",
                "textType": "#textType"
            }
        ]

        # Create a mock for the RO-Crate context
        self.mock_rocrate_context = {
            "@context": {
                "schema": "http://schema.org/",
                "name": "schema:name",
                "description": "schema:description",
                "url": "schema:url",
                "ImageObject": "schema:ImageObject",
            }
        }

    def _create_temp_context_file(self, context):
        """Helper to create a temporary context file"""
        fd, path = tempfile.mkstemp(suffix='.json')
        with os.fdopen(fd, 'w') as f:
            json.dump(context, f)
        return path

    def test_init_with_dict(self):
        """Test initialization with a dictionary context"""
        resolver = JSONLDContextResolver(self.simple_context)
        self.assertEqual(
            resolver.context_map["name"], "http://schema.org/name")
        self.assertEqual(resolver.context_map["schema"], "http://schema.org/")
        self.assertEqual(
            resolver.context_map["complex"]["@id"], "http://example.org/complex")

    @patch('tinycrate.jsonld_context.requests.get')
    def test_init_with_url(self, mock_get):
        """Test initialization with a URL context"""
        # Mock the response from the URL
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = self.mock_rocrate_context
        mock_get.return_value = mock_response

        # Initialize with a URL
        resolver = JSONLDContextResolver(
            "https://w3id.org/ro/crate/1.1/context")

        # Check that the request was made correctly
        mock_get.assert_called_once_with(
            "https://w3id.org/ro/crate/1.1/context")

        # Check that the context was processed correctly
        context_map = resolver.get_context_map()
        self.assertIn("schema", context_map)
        self.assertEqual(context_map["schema"], "http://schema.org/")

    def test_init_with_local_file(self):
        """Test initialization with a local file context"""
        # Create a temporary context file
        path = self._create_temp_context_file(self.mock_rocrate_context)
        try:
            # Initialize with the file path
            resolver = JSONLDContextResolver(path)

            # Check that the context was processed correctly
            context_map = resolver.get_context_map()
            self.assertIn("schema", context_map)
            self.assertEqual(context_map["schema"], "http://schema.org/")
        finally:
            # Clean up the temporary file
            os.unlink(path)

    @patch('tinycrate.jsonld_context.requests.get')
    def test_init_with_complex_context(self, mock_get):
        """Test initialization with a complex context including remote URLs"""
        # Mock the response from the URL
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = self.mock_rocrate_context
        mock_get.return_value = mock_response

        # Create a copy of the complex context to avoid modifying the original
        complex_context_copy = list(self.complex_context)

        # Initialize with the complex context
        resolver = JSONLDContextResolver(complex_context_copy)

        # Check that the URL was requested
        mock_get.assert_called_with("https://w3id.org/ro/crate/1.1/context")

        # Check that the context was processed correctly
        context_map = resolver.get_context_map()
        self.assertIn("@vocab", context_map)
        self.assertEqual(context_map["@vocab"], "http://schema.org/")
        self.assertIn("ldac", context_map)
        self.assertEqual(context_map["ldac"], "https://w3id.org/ldac/terms#")
        self.assertIn("register", context_map)
        self.assertEqual(
            context_map["register"], "http://w3id.org/meta-share/meta-share/register")
        self.assertIn("birthDateEstimateStart", context_map)
        self.assertEqual(
            context_map["birthDateEstimateStart"], "#birthDateEstimateStart")

    def test_resolve_term_direct(self):
        """Test resolving a term directly defined in the context"""
        resolver = JSONLDContextResolver(self.simple_context)
        self.assertEqual(resolver.resolve_term(
            "name"), "http://schema.org/name")
        self.assertEqual(resolver.resolve_term("description"),
                         "http://schema.org/description")

    def test_resolve_term_prefixed(self):
        """Test resolving a prefixed term (CURIE)"""
        resolver = JSONLDContextResolver(self.simple_context)
        self.assertEqual(resolver.resolve_term(
            "schema:title"), "http://schema.org/title")

    def test_resolve_term_with_vocab(self):
        """Test resolving a term using @vocab"""
        resolver = JSONLDContextResolver(self.simple_context)
        self.assertEqual(resolver.resolve_term("author"),
                         "http://example.org/vocab/author")

    def test_resolve_term_complex(self):
        """Test resolving a term with a complex definition"""
        resolver = JSONLDContextResolver(self.simple_context)
        self.assertEqual(resolver.resolve_term("complex"),
                         "http://example.org/complex")

    def test_resolve_existing_iri(self):
        """Test resolving a term that is already an IRI"""
        resolver = JSONLDContextResolver(self.simple_context)
        self.assertEqual(
            resolver.resolve_term("http://example.org/test"),
            "http://example.org/test"
        )
   # test with mediumcontext defined above local:whatever
    def test_resolve_term_with_local_context(self):
        """Test resolving a term with a local context"""
        resolver = JSONLDContextResolver(self.medium_context)
        self.assertEqual(resolver.resolve_term("local"),
                         "arcp://name,corpus-of-oz-early-english/terms#")
        self.assertEqual(resolver.resolve_term("local:whatever"),
                         "arcp://name,corpus-of-oz-early-english/terms#whatever")

    def test_resolve_jsonld_keyword(self):
        """Test resolving a JSON-LD keyword"""
        resolver = JSONLDContextResolver(self.simple_context)
        self.assertEqual(resolver.resolve_term("@type"), "@type")

    @patch('tinycrate.jsonld_context.requests.get')
    def test_failed_remote_context(self, mock_get):
        """Test handling of failed remote context fetch"""
        # Mock a failed response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Expect an exception when initializing with the URL
        with self.assertRaises(ContextResolutionException):
            JSONLDContextResolver("https://example.org/non-existent-context")

    def test_failed_local_context(self):
        """Test handling of non-existent local context file"""
        # Attempt to initialize with a non-existent file
        with self.assertRaises(ContextResolutionException):
            JSONLDContextResolver("/path/to/non-existent-context.json")

    def test_default_context(self):
        """Test initialization with default RO-Crate context"""
        # This test depends on internet connectivity to fetch the real RO-Crate context
        # So we'll just check that it doesn't raise an exception
        try:
            resolver = JSONLDContextResolver()
            # If we get here, the initialization succeeded
            self.assertTrue(len(resolver.context_map) > 0)
        except ContextResolutionException:
            self.skipTest(
                "Could not fetch default RO-Crate context - skipping test")


if __name__ == '__main__':
    unittest.main()
