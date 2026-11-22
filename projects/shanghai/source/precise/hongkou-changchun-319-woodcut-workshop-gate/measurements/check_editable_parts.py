"""Verify that every authoring part encloses positive volume with paired edge directions."""
from pathlib import Path
import argparse,json,sys
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'source'))
from build_model import Builder,PALETTE,add_building
from package_architectural_model import group_parts
def review(lod):
    b=Builder(PALETTE);add_building(b,lod);rows=[]
    for part in b.parts:
        p=np.array(part['vertices']);f=np.array(part['triangles'])
        positions,indices=np.unique(p.round(8),axis=0,return_inverse=True);t=indices[f]
        edges=Counter((int(x),int(y))for i in t for x,y in zip(i,np.roll(i,-1)))
        bad=sum(n!=edges.get((y,x),0)for (x,y),n in edges.items())
        v=p[f];vol=np.einsum('ij,ij->i',v[:,0],np.cross(v[:,1],v[:,2])).sum()/6
        areas=np.linalg.norm(np.cross(v[:,1]-v[:,0],v[:,2]-v[:,0]),axis=1)/2
        rows.append(dict(name=part['label'],material=part['material'],faces=len(f),unpaired_directed_edges=bad,volume_m3=round(float(vol),12),zero_area_faces=int((areas<1.e-14).sum())))
    return dict(groups=len(group_parts(b)),parts=len(rows),triangles=sum(p['faces']for p in rows),items=rows)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('output',type=Path);a=ap.parse_args()
    data={k:review(k=='lod')for k in ('full','lod')};a.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
    print([(k,v['groups'],v['parts'],v['triangles'],[p['name']for p in v['items'] if p['unpaired_directed_edges'] or p['zero_area_faces'] or p['volume_m3']<=0])for k,v in data.items()])
