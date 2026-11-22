"""Export the independent JKK balcony assembly as two editable glTF files."""
import argparse
import sys
from pathlib import Path

import numpy as np
from jkk_balconies import PALETTE, add_balconies

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "hongkou-general-post-office/source/common"))
from photo_architecture import Builder


def build(directory):
    directory.mkdir(exist_ok=True, parents=True)
    for lod, name in ((False,"full"), (True,"lod")):
        builder = Builder(PALETTE)
        add_balconies(builder, lod)
        for part in builder.parts:
            triangles = np.asarray(part["triangles"])
            v = np.asarray(part["vertices"])[triangles]
            volume = np.einsum("ij,ij->i", v[:,0], np.cross(v[:,1],v[:,2])).sum()/6
            edges = np.sort(np.concatenate([triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]]),axis=1)
            if volume <= 0 or np.any(np.unique(edges,axis=0,return_counts=True)[1] != 2):
                raise ValueError(f"Open or reversed solid: {part['label']}")
        builder.save(directory / f"jkk-balconies-{name}.glb",
                     {"scope":"Twelve street balconies on the photographed JKK block","level":name})
        print(name, len(builder.parts), sum(len(part["triangles"]) for part in builder.parts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    build(parser.parse_args().directory)
