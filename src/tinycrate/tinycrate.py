# a new, tiny python RO-Crate library with emphasis on manipulating
# the json-ld metadata

from pathlib import Path
import json
import requests
import datetime  # Added import for datetime
from .jsonld_context import JSONLDContextResolver

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


class TinyCrate:
    def __init__(self, jsonld=None, directory=None):
        if jsonld is not None:
            self.context = jsonld["@context"]
            self.graph = jsonld["@graph"]
        else:
            self.context = "https://w3id.org/ro/crate/1.1/context"
            self.graph = []
        self.directory = directory
        self._context_resolver = None  # Lazy initialization
   

    @property
    def context_resolver(self):
        """Lazily initialize the context resolver to avoid unnecessary processing on initialization"""
        if self._context_resolver is None:
            from .jsonld_context import JSONLDContextResolver
            self._context_resolver = JSONLDContextResolver(self.context)
        return self._context_resolver

    def set_directory(self, directory):
        """Set the directory for this crate"""
        self.directory = directory

    def add(self, t, i, props):
        json_props = dict(props)
        json_props["@id"] = i
        json_props["@type"] = t
        self.graph.append(json_props)

    def all(self):
        """dunno about this"""
        return [TinyEntity(self, e) for e in self.graph]

    def get(self, i):
        es = [e for e in self.graph if e["@id"] == i]
        if es:
            return TinyEntity(self, es[0])
        else:
            return None

    def root(self):
        metadata = self.get("ro-crate-metadata.json")
        if metadata is None:
            raise TinyCrateException("no ro-crate-metadata.json entity")
        root = self.get(metadata["about"]["@id"])
        if root is None:
            raise TinyCrateException("malformed or missing root entity")
        return root

    def json(self):
        return json.dumps({"@context": self.context, "@graph": self.graph}, indent=2)

    def write_json(self, crate_dir=None):
        """Write the json-ld to a file"""
        if crate_dir is None:  # if no directory is set, use the current working directory
            crate_dir = self.directory or "."
        Path(crate_dir).mkdir(parents=True, exist_ok=True)
        with open(Path(crate_dir) / "ro-crate-metadata.json", "w") as jfh:
            json.dump({"@context": self.context, "@graph": self.graph}, jfh, indent=2)

    def resolve_term(self, term):
        """Resolve a JSON-LD term like 'name' or 'schema:name' to its full IRI
        
        Args:
            term (str): The term to resolve, e.g., 'name' or 'schema:name'
            
        Returns:
            str: The full IRI for the term, or the original term if not found
        """
        return self.context_resolver.resolve_term(term)

  
class TinyEntity:
    def __init__(self, crate, ejsonld):
        self.crate = crate
        self.type = ejsonld["@type"]
        self.id = ejsonld["@id"]
        self.props = dict(ejsonld)
        # Store index in parent crate's graph for later updates
        self._graph_index = None
        for i, entity in enumerate(self.crate.graph):
            if entity["@id"] == self.id:
                self._graph_index = i
                break

    def __getitem__(self, prop):
        return self.props.get(prop, None)

    def __setitem__(self, prop, val):
        self.props[prop] = val
        # Update the corresponding entity in the parent crate's graph
        if self._graph_index is not None:
            self.crate.graph[self._graph_index][prop] = val
        else:
            # If index not found, search for the entity and update it
            for i, entity in enumerate(self.crate.graph):
                if entity["@id"] == self.id:
                    self.crate.graph[i][prop] = val
                    self._graph_index = i
                    break

    def fetch(self):
        """Get this entity's content"""
        if self.id[:4] == "http":
            return self._fetch_http()
        else:
            return self._fetch_file()

    def _fetch_http(self):
        response = requests.get(self.id)
        if response.ok:
            return response.text
        raise TinyCrateException(
            f"http request to {self.id} failed with status {response.status_code}"
        )

    def _fetch_file(self):
        if self.crate.directory is None:
            # maybe use pwd for this?
            raise TinyCrateException("Can't load file: no crate directory")
        fn = Path(self.crate.directory) / self.id
        try:
            with open(fn, "r") as fh:
                content = fh.read()
                return content
        except Exception as e:
            raise TinyCrateException(f"File read failed: {e}")


def minimal_crate(name="Minimal crate", description="Minimal crate"):
    """Create ROCrate json with the minimal structure"""
    crate = TinyCrate()
    license_id = "https://creativecommons.org/licenses/by-nc-sa/3.0/au/"
    crate.add(
        "Dataset",
        "./",
        {
            "name": name,
            "description": description,
            "license": {"@id": license_id},
            "datePublished": datetime.datetime.now().year,  # Using datetime to get current year
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
