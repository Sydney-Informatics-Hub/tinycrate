from pathlib import Path
from fuzz import random_text, random_property
import json

from pytest_httpserver import HTTPServer

from tinycrate.tinycrate import TinyCrate, minimal_crate


def test_crate(tmp_path):
    """Build and save and reload a crate"""
    jcrate = minimal_crate()
    for i in range(1000):
        props = {"name": random_text(4), "description": random_text(11)}
        for j in range(30):
            prop, val = random_property()
            props[prop] = val
        jcrate.add("Dataset", f"#ds{i:05d}", props)
    jcrate.write_json(Path(tmp_path))
    jcrate2 = TinyCrate(source=tmp_path)
    for i in range(1000):
        eid = f"#ds{i:05d}"
        ea = jcrate.get(eid)
        eb = jcrate2.get(eid)
        assert ea.props == eb.props


def load_json(json_file):
    with open(json_file, "r") as fh:
        contents = fh.read()
    return json.loads(contents)


def test_load_file(crates):
    "Load from a JSON-LD file"
    cratedir = crates["textfiles"]
    jsonld_file = Path(cratedir) / "ro-crate-metadata.json"
    crate = TinyCrate(jsonld_file)
    tfile = crate.get("doc001/textfile.txt")
    contents = tfile.fetch()
    with open(Path(cratedir) / "doc001" / "textfile.txt", "r") as tfh:
        contents2 = tfh.read()
        assert contents == contents2
    assert crate.directory.samefile(cratedir)
    jsonld = load_json(jsonld_file)
    for json_ent in jsonld["@graph"]:
        entity = crate.get(json_ent["@id"])
        assert entity is not None
        for prop, val in entity.items():
            assert json_ent[prop] == val


def test_load_dir(crates):
    "Load from a directory containing a JSON-LD file"
    cratedir = crates["textfiles"]
    crate = TinyCrate(Path(cratedir))
    tfile = crate.get("doc001/textfile.txt")
    contents = tfile.fetch()
    with open(Path(cratedir) / "doc001" / "textfile.txt", "r") as tfh:
        contents2 = tfh.read()
        assert contents == contents2
    assert crate.directory.samefile(cratedir)
    jsonld_file = Path(cratedir) / "ro-crate-metadata.json"
    jsonld = load_json(jsonld_file)
    for json_ent in jsonld["@graph"]:
        entity = crate.get(json_ent["@id"])
        assert entity is not None
        for prop, val in entity.items():
            assert json_ent[prop] == val


def test_load_url(crates, httpserver: HTTPServer):
    "Load from a JSON-LD file on a URL"
    cratedir = crates["textfiles"]
    with open(Path(cratedir) / "ro-crate-metadata.json", "r") as fh:
        contents = fh.read()
    httpserver.expect_request("/ro-crate-metadata.json").respond_with_data(
        contents, content_type="application/json"
    )
    url = httpserver.url_for("/ro-crate-metadata.json")
    crate = TinyCrate(url)
    jsonld = json.loads(contents)
    for json_ent in jsonld["@graph"]:
        entity = crate.get(json_ent["@id"])
        assert entity is not None
        for prop, val in entity.items():
            assert json_ent[prop] == val


def test_load_utf8(crates):
    """Reads a textfile known to have utf-8 characters which cause
    encoding bugs on a Jupyter notebook on Windows"""
    cratedir = crates["utf8"]
    crate = TinyCrate(source=cratedir)
    tfile = crate.get("data/2-035-plain.txt")
    contents = tfile.fetch()
    # note: have to also explicitly set the encoding on this read so that
    # it doesn't also break the tests
    with open(
        Path(cratedir) / "data" / "2-035-plain.txt", "r", encoding="utf-8"
    ) as tfh:
        contents2 = tfh.read()
        assert contents == contents2
