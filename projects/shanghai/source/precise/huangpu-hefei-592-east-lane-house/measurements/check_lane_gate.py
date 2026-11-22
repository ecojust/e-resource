"""Test photographed gate, sign and paving by intersecting rays with a delivered GLB."""
import argparse
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from lane_gate import ENAMEL,BRICKS,PLASTER,IRON,CAP,BAND
from lane_paving import CEMENT,PAVERS,JOINT,LID,DARK

def check(path):
    helper=runpy.run_path(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
    tri,mi,names,asset=helper['load_triangles'](path)
    survey=json.loads((HERE/'hefei-lane-gate-survey.json').read_bytes())
    points=json.loads((HERE/'gate-native-pixel-witnesses.json').read_bytes())['points']
    expected={'enamel':{ENAMEL},'red':set(BRICKS),'iron':{IRON},'gap':set(names)-{IRON}|{None},
              'plaster':{PLASTER},'cap':{CAP,BAND},'cement':{CEMENT},'walk':set(PAVERS)|{JOINT,LID,DARK}}
    normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);events=[]
    for camera in dict.fromkeys(w['camera'] for w in points):
        m=np.array(survey['cameras'][camera]['projection']);inverse=np.linalg.inv(m[:,:3]);eye=-inverse@m[:,3]
        q=tri@m[:,:3].T+m[:,3];uv=q[:,:,:2]/q[:,:,2:];lo=uv.min(1);hi=uv.max(1);tiles={}
        def first(uv):
            k=tuple(np.floor(uv/24).astype(int))
            if k not in tiles:
                lim=np.array(k)*24.;tiles[k]=np.flatnonzero((lo<=lim+24).all(1)&(hi>=lim).all(1))
            ray=inverse@np.r_[uv,1.];ray/=np.linalg.norm(ray)
            ii=tiles[k];ii=ii[(lo[ii]<=uv+.00001).all(1)&(hi[ii]>=uv-.00001).all(1)&(normal[ii]@ray<0)]
            if not len(ii):return None
            j,d,_=helper['first_hit'](tri[ii],eye,ray)
            return None if not np.isfinite(d) else names[mi[ii[j]]]
        for p in (w for w in points if w['camera']==camera):
            xy=np.array(p['native_px']);want=expected[p['expected']];surf=first(xy)
            off=None
            for dx,dy in sorted(((x,y)for x in np.arange(-3.,3.01,.5)for y in np.arange(-3.,3.01,.5)
                                 if x*x+y*y<=p['radius_px']**2),key=lambda t:t[0]**2+t[1]**2):
                if (surf if dx==dy==0 else first(xy+[dx,dy])) in want:
                    off=[dx,dy];break
            events.append({**p,'nominal_surface':surf,'nominal_ok':surf in want,'nearest_matching_offset_px':off})
    return {'asset':asset,'total':len(events),'nominal':sum(e['nominal_ok']for e in events),
            'within_native_pixel_neighbourhood':sum(e['nearest_matching_offset_px'] is not None for e in events),'tests':events}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    a=parser.parse_args();r=check(a.mesh);a.output.write_text(json.dumps(r,ensure_ascii=False,indent=1)+'\n')
    print(r['nominal'],r['within_native_pixel_neighbourhood'],r['total'])
