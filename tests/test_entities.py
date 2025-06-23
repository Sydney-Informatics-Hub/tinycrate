from pathlib import Path
import json
from tinycrate.tinycrate import TinyCrate, minimal_crate


def test_basic_entity():
    """Create a single entity"""
    crate = minimal_crate()
    props = {"name": "A dataset", "description": "The description of the dataset"}
    crate.add("Dataset", "#mydata", props)
    props["@type"] = "Dataset"
    entity = crate.get("#mydata")
    for prop, val in props.items():
        assert entity[prop] == [val]
        assert entity.data[prop] == [val]
        assert entity.props[prop] == [val]


def test_modify_entity(tmp_path):
    """Modify an entity and see if the change is written out to the crate"""
    crate = minimal_crate()
    props = {"name": "A dataset", "description": "The description of the dataset"}
    crate.add("Dataset", "#mydata", props)
    entity = crate.get("#mydata")
    new_name = "A dataset with a new name"
    entity["name"] = new_name
    jsonf = Path(tmp_path) / "ro-crate-metadata.json"
    crate.write_json(tmp_path)
    with open(jsonf, "r") as jfh:
        jsonld = json.load(jfh)
        crate2 = TinyCrate(jsonld)
        e2 = crate2.get("#mydata")
        assert e2 is not None
        assert e2["name"] == [new_name]
    entity3 = crate.get("#mydata")
    assert entity3["name"] == [new_name]


def test_entity_iteration():
    crate = minimal_crate()
    props = {"name": "A dataset", "description": "The description of the dataset"}
    crate.add("Dataset", "#mydata", props)
    entity = crate.get("#mydata")
    for prop, val in props.items():
        assert entity[prop] == [val]
    nitems = len(crate.graph)
    count = 0
    for prop in entity:
        val = entity.get(prop, None)
        assert entity[prop] == val
        count += 1
        assert count <= nitems
