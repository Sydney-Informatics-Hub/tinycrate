import pytest


@pytest.fixture
def crates():
    return {
        "minimal": "./tests/crates/minimal",
        "wide": "./tests/crates/wide",
        "textfiles": "./tests/crates/textfiles",
        "utf8": "./tests/crates/utf8",
    }


@pytest.fixture
def contexts():
    return {
        "simple": {
            "name": "http://schema.org/name",
            "description": "http://schema.org/description",
            "schema": "http://schema.org/",
            "@vocab": "http://example.org/vocab/",
            "complex": {"@id": "http://example.org/complex"},
        },
        "medium": {
            "@context": [
                "https://w3id.org/ro/crate/1.1/context",
                {
                    "@vocab": "http://schema.org/",
                    "ldac": "https://w3id.org/ldac/terms#",
                },
                {
                    "register": "http://w3id.org/meta-share/meta-share/register",
                    "local": "arcp://name,corpus-of-oz-early-english/terms#",
                },
            ],
        },
        "complex": [
            "https://w3id.org/ro/crate/1.1/context",
            {"@vocab": "http://schema.org/", "ldac": "https://w3id.org/ldac/terms#"},
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
                "textType": "#textType",
            },
        ],
    }


@pytest.fixture
def ro_crate_context():
    return {
        "@context": {
            "schema": "http://schema.org/",
            "name": "schema:name",
            "description": "schema:description",
            "url": "schema:url",
            "ImageObject": "schema:ImageObject",
        }
    }
