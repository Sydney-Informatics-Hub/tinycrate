# tinycrate

A minimal RO-Crate library in Python with an emphasis on working transparently
with crates on disk and crates over the network.

## Usage

    from tinycrate.tinycrate import TinyCrate

    tc = TinyCrate(jsonld)
    tc = TinyCrate(url)
    tc = TinyCrate(crate_path)

    r = tc.root()

    for entity in tc.all():
        for prop.value in entity.items():
            print(f"{prop}: {value}"")
        if entity.type == "File":
            contents = entity.fetch()
    
