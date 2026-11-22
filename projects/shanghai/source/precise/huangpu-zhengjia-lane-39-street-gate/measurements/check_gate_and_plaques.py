"""Compare independent street-pixel samples to the actual exported iron, plaques, piers and openings."""
import argparse
import json
from pathlib import Path
import runpy
import sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
import zhengjia_gate as gate
from zheng_gate_camera import matrix

def check(path):
    h=runpy.run_path(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    tri,mi,names,asset=h['load_triangles'](path);normals=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
    want={'paint':set(gate.INK),'paper':{gate.PALE},'green':{gate.GREEN},'concrete':{gate.POST},
          'cap':{gate.CAP,gate.EDGE},'fixture':{gate.BOX,gate.SHADE},'iron':{gate.IRON,gate.WORN},
          'gap':set(names)-{gate.IRON,gate.WORN}|{None}}
    source=json.loads((HERE/'zhengjia-gate-native-witnesses.json').read_bytes())['points'];out=[]
    for key in dict.fromkeys(v['camera']for v in source):
        m=matrix(key);inv=np.linalg.inv(m[:,:3]);eye=-inv@m[:,3];q=tri@m[:,:3].T+m[:,3]
        uv=q[:,:,:2]/q[:,:,2:];lo=uv.min(1);hi=uv.max(1);cache={}
        def first(pixel):
            coord=tuple(pixel)
            if coord in cache:return cache[coord]
            ray=inv@np.r_[pixel,1.];ray/=np.linalg.norm(ray)
            idx=np.flatnonzero((lo<=pixel+.00001).all(1)&(hi>=pixel-.00001).all(1)&(normals@ray<0))
            mat=None
            if len(idx):
                j,dist,_=h['first_hit'](tri[idx],eye,ray)
                if np.isfinite(dist):mat=names[mi[idx[j]]]
            cache[coord]=mat
            return mat
        for p in (w for w in source if w['camera']==key):
            px=np.array(p['native_pixel']);surface=first(px);ok=surface in want[p['surface']]
            offset=[0,0] if ok else None
            if not ok:
                rad=p['tolerance_px']
                nearby=sorted(((dx,dy)for dx in range(-rad,rad+1)for dy in range(-rad,rad+1)if 0<dx*dx+dy*dy<=rad*rad),key=lambda o:o[0]**2+o[1]**2)
                for dx,dy in nearby:
                    if first(px+[dx,dy]) in want[p['surface']]:
                        offset=[dx,dy];break
            out.append({**p,'first_surface':surface,'nominal_matches':ok,'nearest_matching_offset':offset})
    return dict(asset=asset,count=len(out),nominal=sum(o['nominal_matches']for o in out),
                neighbourhood=sum(o['nearest_matching_offset'] is not None for o in out),tests=out)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();v=check(a.model);a.output.write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n')
    print(v['nominal'],v['neighbourhood'],v['count'])
