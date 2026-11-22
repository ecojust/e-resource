"""Export the measured courtyard window assemblies at both delivery levels."""
import argparse
from pathlib import Path
import sys

import numpy as np

from upper_casements import PALETTE,add_windows

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE.parent/"hongkou-general-post-office/source/common"))
from photo_architecture import Builder


def export(output):
    output.mkdir(exist_ok=True,parents=True)
    for low,name in [(False,"full"),(True,"lod")]:
        b=Builder(PALETTE)
        add_windows(b,low)
        for part in b.parts:
            xyz=np.asarray(part["vertices"])
            tri=np.asarray(part["triangles"])
            polys=xyz[tri]
            volume=np.einsum("ij,ij->i",polys[:,0],np.cross(polys[:,1],polys[:,2])).sum()/6
            edges=np.sort(np.concatenate([tri[:,[0,1]],tri[:,[1,2]],tri[:,[2,0]]]),axis=1)
            count=np.unique(edges,axis=0,return_counts=True)[1]
            if volume<=0. or np.any(count!=2):
                raise ValueError("Open or inverted editable part: "+part["label"])
        b.save(output/f"212-casements-{name}.glb",{"subject":"Upper wooden casements of the numbered Nanchang Lane 212 entrance","level":name})
        print(name,len(b.parts),sum(len(part["triangles"]) for part in b.parts))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("output",type=Path)
    export(p.parse_args().output)
