# tinycrate

A minimal RO-Crate library in Python with an emphasis on working transparently
with crates on disk and crates over the network.

## Usage

    from tinycrate.tinycrate import TinyCrate

    tc_from_json = TinyCrate(jsonld)
    tc_from_url = TinyCrate(url)
    tc_from_disk = TinyCrate(crate_path)

    r = tc_from_url.root()

    for entity in tc_from_url.all():
        for prop.value in entity.items():
            print(f"{prop}: {value}"")
        if entity.type == "File":
            contents = entity.fetch()
            print(contents)
    
