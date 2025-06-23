from __future__ import annotations
from pathlib import Path, PurePath
import json
import requests
import datetime
from typing import Any, Optional, Union, List
from collections import UserDict
from tinycrate.jsonld_context import JSONLDContextResolver

LICENSE_ID = ("https://creativecommons.org/licenses/by-nc-sa/3.0/au/",)
LICENSE_DESCRIPTION = """
This work is licensed under the Creative Commons 
Attribution-NonCommercial-ShareAlike 3.0 Australia License.
To view a copy of this license, visit
http://creativecommons.org/licenses/by-nc-sa/3.0/au/ or send a letter to
Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
"""
LICENSE_IDENTIFIER = "https://creativecommons.org/licenses/by-nc-sa/3.0/au/"
LICENSE_NAME = """
Attribution-NonCommercial-ShareAlike 3.0 Australia (CC BY-NC-SA 3.0 AU)"
"""


class TinyCrateException(Exception):
    pass


def ensure_list(val):
    if type(val) is not list:
        return [val]
    else:
        return val


class TinyEntity(UserDict):
    def __init__(self, crate: TinyCrate, ejsonld: dict[str, Any]) -> None:
        self.crate = crate
        self.type = ensure_list(ejsonld["@type"])
        self.id = ejsonld["@id"]
        self.data = {}
        # Store index in parent crate's graph for later updates
        self._graph_index = None
        for key, val in ejsonld.items():
            if key == "@id":
                self.data["@id"] = val
            else:
                self[key] = val  # __setitem__ ensures list
        for i, entity in enumerate(self.crate.graph):
            if entity["@id"] == self.id:
                self._graph_index = i
                break

    @property
    def props(self):
        return self.data

    def __getitem__(self, prop: str) -> List[Union[str, Any]]:
        if prop in self.data:
            return self.data[prop]
        return []

    def __setitem__(self, prop: str, val: Union[str, Any]) -> None:
        """Values are convered to lists on setting if they are not"""
        if type(val) is not list:
            lval = [val]
        else:
            lval = val
        self.data[prop] = lval
        # Update the corresponding entity in the parent crate's graph
        if self._graph_index is not None:
            self.crate.graph[self._graph_index][prop] = lval
        else:
            # If index not found, search for the entity and update it
            for i, entity in enumerate(self.crate.graph):
                if entity["@id"] == self.id:
                    self.crate.graph[i][prop] = lval
                    self._graph_index = i
                    break

    def fetch(self) -> str:
        """Get this entity's content"""
        if self.id[:4] == "http":
            return self._fetch_http()
        else:
            return self._fetch_file()

    def _fetch_http(self) -> str:
        response = requests.get(self.id)
        if response.ok:
            return response.text
        raise TinyCrateException(
            f"http request to {self.id} failed with status {response.status_code}"
        )

    def _fetch_file(self) -> str:
        if self.crate.directory is None:
            # maybe use pwd for this?
            raise TinyCrateException("Can't load file: no crate directory")
        fn = Path(self.crate.directory) / self.id
        try:
            with open(fn, "r", encoding="utf-8") as fh:
                content = fh.read()
                return content
        except Exception as e:
            raise TinyCrateException(f"File read failed: {e}")


class TinyCrate:
    """Object representing an RO-Crate"""

    def __init__(self, source: Union[str, Path, None] = None) -> None:
        self.directory: Optional[Path] = None
        self._context_resolver: Optional[JSONLDContextResolver] = None
        if source is not None:
            if isinstance(source, PurePath):
                self._open_path(source)
            else:
                if type(source) is str:
                    if source.startswith(("https://", "http://")):
                        self._open_url(source)
                    else:
                        self._open_path(Path(source))
                else:
                    if type(source) is dict:
                        self._open_jsonld(source)
                    else:
                        t = type(source)
                        raise TinyCrateException(
                            "can only init from a str, Path or "
                            f"JSON-LD dict (got a {t})"
                        )
        else:
            self.context = "https://w3id.org/ro/crate/1.1/context"
            self.graph: list[dict] = []

    def _open_jsonld(self, jsonld: dict[str, Any]) -> None:
        """Load a dict representing a JSON-LD"""
        if "@context" not in jsonld:
            raise TinyCrateException("No @context in json-ld")
        if "@graph" not in jsonld:
            raise TinyCrateException("No @graph in json-ld")
        self.context = jsonld["@context"]
        self.graph = jsonld["@graph"]

    def _open_path(self, path: Path) -> None:
        """Load a file or Path, which can be the jsonld file or its
        containing directory. Sets the directory property accordingly."""
        if path.is_dir():
            self.directory = path
            path = path / "ro-crate-metadata.json"
        else:
            self.directory = path.parent
        with open(path, "r") as fh:
            jsonld = json.load(fh)
            self._open_jsonld(jsonld)

    def _open_url(self, url: str) -> None:
        """Load a crate from the url of the metadata.json"""
        response = requests.get(url)
        if response.ok:
            jsonld = json.loads(response.text)
            self._open_jsonld(jsonld)
        else:
            raise TinyCrateException(
                f"http request to {url} failed with status {response.status_code}"
            )

    @property
    def context_resolver(self) -> JSONLDContextResolver:
        """Lazily initialize the context resolver to avoid unnecessary processing on initialization"""
        if self._context_resolver is None:
            self._context_resolver = JSONLDContextResolver(self.context)
        return self._context_resolver

    def set_directory(self, directory: Path) -> None:
        """Set the directory for this crate"""
        self.directory = directory

    def add(self, t: str, i: str, props: dict[str, Any]) -> None:
        json_props = dict(props)
        json_props["@id"] = i
        json_props["@type"] = t
        self.graph.append(json_props)

    def all(self) -> list[TinyEntity]:
        return [TinyEntity(self, e) for e in self.graph]

    def get(self, i: str) -> Optional[TinyEntity]:
        es = [e for e in self.graph if e["@id"] == i]
        if es:
            return TinyEntity(self, es[0])
        else:
            return None

    def deref(self, entity: TinyEntity, prop: str) -> Optional[TinyEntity]:
        """Given an entity and a property, try to follow the @id"""
        id_val: List[Union[str, Any]] = entity[prop]
        if len(id_val) == 0:
            return None
        if len(id_val) == 1:
            if type(id_val[0]) is dict:
                ref: Optional[str] = id_val[0].get("@id", None)
                if ref is not None:
                    return self.get(ref)
        return None

    def root(self) -> TinyEntity:
        metadata = self.get("ro-crate-metadata.json")
        if metadata is None:
            raise TinyCrateException("no ro-crate-metadata.json entity")
        root = self.deref(metadata, "about")
        if root is None:
            raise TinyCrateException("Missing or malformed root entity")
        return root

    def json(self) -> str:
        return json.dumps({"@context": self.context, "@graph": self.graph}, indent=2)

    def write_json(self, crate_dir: Optional[Path] = None) -> None:
        """Write the json-ld to a file"""
        if crate_dir is None:
            crate_dir = self.directory or Path(".")
        crate_dir.mkdir(parents=True, exist_ok=True)
        with open(crate_dir / "ro-crate-metadata.json", "w") as jfh:
            json.dump({"@context": self.context, "@graph": self.graph}, jfh, indent=2)

    def resolve_term(self, term: str) -> str:
        """Resolve a JSON-LD term like 'name' or 'schema:name' to its full IRI

        Args:
            term (str): The term to resolve, e.g., 'name' or 'schema:name'

        Returns:
            str: The full IRI for the term, or the original term if not found
        """
        return self.context_resolver.resolve_term(term)


def minimal_crate(
    name: str = "Minimal crate",
    description: str = "Minimal crate",
    date_published: Optional[str] = None,
) -> TinyCrate:
    """Create ROCrate json with the minimal structure. Allowing the caller
    to pass in the datePublished to ensure that this can be run
    deterministically in tests"""
    crate = TinyCrate()
    license_id = "https://creativecommons.org/licenses/by-nc-sa/3.0/au/"
    dp: str = ""
    if date_published is None:
        dp = datetime.datetime.now().isoformat()[:10]
    else:
        dp = date_published
    crate.add(
        "Dataset",
        "./",
        {
            "name": name,
            "description": description,
            "license": {"@id": license_id},
            "datePublished": dp,
        },
    )
    crate.add(
        "CreativeWork",
        license_id,
        {
            "name": LICENSE_NAME,
            "description": "LICENSE_DESCRIPTION",
            "identifier": "LICENSE_IDENTIFIER",
        },
    )
    crate.add(
        "CreativeWork",
        "ro-crate-metadata.json",
        {
            "about": {"@id": "./"},
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
        },
    )
    return crate
