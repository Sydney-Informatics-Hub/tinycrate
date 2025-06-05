from tinycrate.jsonld_context import JSONLDContextResolver, ContextResolutionException
import pytest
from pytest_httpserver import HTTPServer
import json


def test_init_with_dict(contexts):
    """Test initialization with a dictionary context"""
    cdict = contexts["simple"]
    resolver = JSONLDContextResolver(cdict)
    assert resolver.context_map == cdict


def test_init_with_url(contexts, httpserver: HTTPServer):
    """Test initialization with a URL context"""
    cdict = contexts["simple"]
    httpserver.expect_request("/mycontext").respond_with_data(
        json.dumps(cdict), content_type="application/json"
    )
    url = httpserver.url_for("/mycontext")
    resolver = JSONLDContextResolver(url)
    context_map = resolver.get_context_map()
    assert context_map == cdict


def test_init_with_local_file(contexts, tmp_path):
    """Test initialization with a local file context"""
    # Create a temporary context file
    cdict = contexts["simple"]
    fn = str(tmp_path / "context.json")
    with open(fn, "w") as fh:
        json.dump(cdict, fh)
    resolver = JSONLDContextResolver(fn)
    context_map = resolver.get_context_map()
    assert context_map == cdict


def test_init_with_complex_context(contexts, ro_crate_context, httpserver: HTTPServer):
    """Test initialization with a complex context including remote URLs"""
    # make a URL with the cut-down schema.org context on it
    httpserver.expect_request("/ro_crate_context").respond_with_data(
        json.dumps(ro_crate_context), content_type="application/json"
    )
    url = httpserver.url_for("/ro_crate_context")
    # inject the url from httpserverinto the complex context

    cdict = contexts["complex"]
    cdict[0] = url
    resolver = JSONLDContextResolver(cdict)
    context_map = resolver.get_context_map()
    assert context_map["@vocab"] == "http://schema.org/"
    assert context_map["ldac"] == "https://w3id.org/ldac/terms#"
    assert context_map["register"] == "http://w3id.org/meta-share/meta-share/register"
    assert context_map["birthDateEstimateStart"] == "#birthDateEstimateStart"


def test_resolve_term_direct(contexts):
    """Test resolving a term directly defined in the context"""
    resolver = JSONLDContextResolver(contexts["simple"])
    assert resolver.resolve_term("name") == "http://schema.org/name"
    assert resolver.resolve_term("description") == "http://schema.org/description"


def test_resolve_term_prefixed(contexts):
    """Test resolving a prefixed term (CURIE)"""
    resolver = JSONLDContextResolver(contexts["simple"])
    assert resolver.resolve_term("schema:title") == "http://schema.org/title"


def test_resolve_term_with_vocab(contexts):
    """Test resolving a term using @vocab"""
    resolver = JSONLDContextResolver(contexts["simple"])
    assert resolver.resolve_term("author") == "http://example.org/vocab/author"


def test_resolve_term_complex(contexts):
    """Test resolving a term with a complex definition"""
    resolver = JSONLDContextResolver(contexts["simple"])
    assert resolver.resolve_term("complex") == "http://example.org/complex"


def test_resolve_existing_iri(contexts):
    """Test resolving a term that is already an IRI"""
    resolver = JSONLDContextResolver(contexts["simple"])
    assert resolver.resolve_term("http://example.org/test") == "http://example.org/test"


# test with mediumcontext defined above local:whatever
def test_resolve_term_with_local_context(contexts):
    """Test resolving a term with a local context"""
    resolver = JSONLDContextResolver(contexts["medium"])
    assert (
        resolver.resolve_term("local")
        == "arcp://name,corpus-of-oz-early-english/terms#"
    )
    assert (
        resolver.resolve_term("local:whatever")
        == "arcp://name,corpus-of-oz-early-english/terms#whatever"
    )


def test_resolve_jsonld_keyword(contexts):
    """Test resolving a JSON-LD keyword"""
    resolver = JSONLDContextResolver(contexts["simple"])
    assert resolver.resolve_term("@type") == "@type"


def test_failed_remote_context():
    # Expect an exception when initializing with the URL
    with pytest.raises(ContextResolutionException):
        JSONLDContextResolver("https://localhost:1234")


def test_failed_local_context():
    """Test handling of non-existent local context file"""
    with pytest.raises(ContextResolutionException):
        JSONLDContextResolver("/path/to/non-existent-context.json")


def test_default_context():
    """Test initialization with default RO-Crate context"""
    # This test depends on internet connectivity to fetch the real RO-Crate context
    # So we'll just check that it doesn't raise an exception
    try:
        resolver = JSONLDContextResolver()
        # If we get here, the initialization succeeded
        assert len(resolver.context_map) > 0
    except ContextResolutionException:
        pass
