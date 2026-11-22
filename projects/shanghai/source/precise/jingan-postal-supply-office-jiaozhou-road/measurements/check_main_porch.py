"""Test the stone surround, its opening, and unfiltered rays from the winter photographs."""
from pathlib import Path
import argparse
from collections import Counter
import json
import sys

import numpy as np

D=Path(__file__).resolve().parent
sys.path[:0]=[str(D.parent/'source'),str(D.parents[1]/'hongkou-general-post-office/source/common'),
             str(D.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from main_porch import PALETTE,OBS,STONE,EDGE,BED,add_main_porch
from glb_triangles import SerialScene
from photo_architecture import Builder

PHOTO_MARKS={
 'mid-2020':{'north wing upright':[(246,234),(250,273)],'exposed left cap':[(101,149),(112,147)],'opening':[(308,236),(319,252)]},
 'north-2015':{'north wing upright':[(175,166),(183,214)],'opening':[(228,164),(225,194)]},
 'north-2020':{'south wing upright':[(512,218),(507,262)],'flat header':[(352,155),(410,151)],'opening':[(376,200),(412,217)]},
}
ALLOWED=[STONE,EDGE,BED]

def export(mesh,low):
    b=Builder(PALETTE);add_main_porch(b,low)
    for p in b.parts:
        v=np.array(p['vertices']);faces=np.array(p['triangles'])
        edges=Counter((i,j) for tri in faces for i,j in zip(tri,np.roll(tri,-1)))
        assert all(n==1 and edges[j,i]==1 for (i,j),n in edges.items()),p['label']
        vert=(v-v.mean(axis=0))[faces]
        assert np.sum(vert[:,0]*np.cross(vert[:,1],vert[:,2]))>0,p['label']
    b.save(mesh,{'name':'Street-side stone porch and canopy'})
    return dict(objects=len(b.parts),triangles=sum(len(p['triangles'])for p in b.parts),positive_closed_parts=True)

def check(mesh):
    s=SerialScene(mesh);rows=[]
    def sample(k,o,v,length,allowed,**fields):
        hit=s.ray(o,v,length)
        material=hit['material'] if hit else None
        rows.append(dict(group=k,accepted=allowed,first_material=material,
                         distance_m=round(hit['distance_m'],4) if hit else None,
                         passed=material in allowed,**fields))
    for a,xs in [('north shaft',[-14.78,-14.56,-14.33]),('south shaft',[-12.32,-12.1,-11.9])]:
        for x in xs:
            for z in [.85,1.65,2.46,3.19,3.62]:
                sample(a,[x,-2,z],[0,1,0],2.24,ALLOWED,x=x,z=z)
    for x in [-14.05,-13.74,-13.45,-13.08,-12.76,-12.56]:
        for z in [.80,1.44,2.15,2.75,3.42]:
            sample('Clear finished aperture',[x,-2,z],[0,1,0],2.02,[None],x=x,z=z)
    for z,xs in [(3.80,[-14.11,-13.58,-12.64]),(3.98,[-14.5,-13.88,-13.0,-12.6]),
                 (4.109,[-15.25,-14.8,-13.5,-12.6,-11.3]),(4.22,[-15.45,-14.1,-12.8,-11.2]),
                 (4.28,[-15.65,-13.2,-11]),(4.36,[-15.7,-14.9,-13,-11.0])]:
        for x in xs:sample('Header or cap',[x,-2,z],[0,1,0],2.20,ALLOWED,x=x,z=z)
    for tag,features in PHOTO_MARKS.items():
        P=np.array(OBS['photos'][tag]['matrix']);eye=np.linalg.solve(-P[:,:3],P[:,3])
        for name,uvs in features.items():
            allowed=[None] if name=='opening' else ALLOWED
            for uv in uvs:
                vec=np.linalg.solve(P[:,:3],[*uv,1]);vec/=np.linalg.norm(vec)
                # Test only the porch and near edge of the façade. The physical
                # door leaf behind it belongs to the separate opening model.
                length=(.02-eye[1])/vec[1]
                sample(name,eye,vec,length,allowed,station=tag,native_px=uv)
    return dict(asset=s.asset,orthographic=len(rows)-sum(len(v)for d in PHOTO_MARKS.values()for v in d.values()),
                count=len(rows),source_pixel_rays=sum(len(v)for d in PHOTO_MARKS.values()for v in d.values()),
                passed=all(r['passed'] for r in rows),results=rows)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('mesh',type=Path);ap.add_argument('out',type=Path)
    ap.add_argument('--export',choices=('full','lod'));a=ap.parse_args()
    stats=export(a.mesh,a.export=='lod') if a.export else {}
    v={**stats,**check(a.mesh)};a.out.write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n')
    print(v['count'],[(r['group'],r.get('native_px'),r.get('x'))for r in v['results']if not r['passed']])
    raise SystemExit(int(not v['passed']))
