"""Check each editable closed roof solid, plus per-triangle UV area on all tiles."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
SRC=HERE.parent/'source'
PREC=HERE.parents[1]
sys.path[:0]=[str(SRC),str(PREC/'hongkou-tanggu-road-apartment-dated-crown/source'),str(PREC/'hongkou-general-post-office/source/common')]
from crown_builder import CrownBuilder
from house_fabric import PALETTE
from huang_roof import add_roof,TILE

def review(lod):
    b=CrownBuilder(dict(PALETTE))
    faces=add_roof(b,lod,json.loads((SRC/'garden-layout.json').read_bytes()))
    smallest_uv=None
    volume_sum=0.
    textured=0
    triangles=0
    minimum_volume=None
    for part in b.parts:
        verts=np.asarray(part['vertices'],dtype=float)
        idx=np.asarray(part['triangles'],dtype=int)
        xyz=verts[idx]; triangles+=len(idx)
        weld,inverse=np.unique(np.round(verts,7),axis=0,return_inverse=True)
        t=inverse[idx]
        edges=Counter((min(a,c),max(a,c)) for poly in t for a,c in zip(poly,np.roll(poly,-1)))
        oriented=Counter((a,c) for poly in t for a,c in zip(poly,np.roll(poly,-1)))
        assert all(n==2 for n in edges.values())
        assert all(n==oriented[(c,a)] for (a,c),n in oriented.items())
        signed=float(np.einsum('ij,ij->i',xyz[:,0],np.cross(xyz[:,1],xyz[:,2])).sum()/6.)
        assert signed>0
        volume_sum+=signed
        minimum_volume=signed if minimum_volume is None else min(signed,minimum_volume)
        if part['material']!=TILE: continue
        uv=np.asarray(part['texcoords'])[idx]
        d=uv[:,1]-uv[:,0]; e=uv[:,2]-uv[:,0]
        area=np.abs(d[:,0]*e[:,1]-d[:,1]*e[:,0])
        assert np.isfinite(uv).all() and (area>1e-11).all()
        textured+=len(area)
        smallest_uv=area.min() if smallest_uv is None else min(smallest_uv,area.min())
    return dict(passed=True,editable_solids=len(b.parts),triangles=triangles,closed_solids=len(b.parts),positive_volume_solids=len(b.parts),roof_faces=len(faces),minimum_volume_m3=minimum_volume,sum_independent_solid_volumes_m3=volume_sum,tile_triangles=textured,minimum_tile_twice_uv_area=smallest_uv)

if __name__=='__main__':
    result={'near':review(False),'far':review(True),'source_sha256':hashlib.sha256((SRC/'huang_roof.py').read_bytes()).hexdigest(),'tile_texture_sha256':hashlib.sha256((SRC/'huang-roof-tiles.png').read_bytes()).hexdigest()}
    Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n')
    print(result)
