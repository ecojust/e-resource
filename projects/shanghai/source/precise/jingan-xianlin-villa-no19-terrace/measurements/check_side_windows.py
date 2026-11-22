"""Verify first-hit materials of the three photographed side windows in a decoded building."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from courtyard_photo_plane import CAMERA,P
import courtyard_side_windows as part

def check(asset):
    scene=SerialScene(asset)
    origin=np.array(CAMERA['camera_origin_xyz_m'])
    details=json.loads((HERE/'side-window-photo-checks.json').read_text())
    measures=json.loads((HERE/'side-window-measurements.json').read_text())
    hits=[]
    def observe(tag,start,ray,length,accepted,**data):
        found=scene.ray(start,ray,length)
        name=found['material'] if found else None
        hits.append(dict(label=tag,expected=accepted,first_hit=name,
                         passed=name in accepted,**data))
    for item in details['points']:
        px=item['pixel']
        direction=np.linalg.solve(P[:,:3],[*px,1.])
        k=item['visible_material']
        materials=k if isinstance(k,list) else [k]
        observe(item['window']+' / photo',origin,direction,40,[getattr(part,name) for name in materials],original_px=px)
    for w in measures['windows']:
        l,r,b,t=[w[k]for k in ('left','right','bottom','top')]
        n=w['key']
        for side,x in [('left',l-.02),('right',r+.02)]:
            for j in range(5):
                z=b+(t-b)*(j+1)/6
                observe(n+' / '+side+' white jamb',[x,-.35,z],[0,1,0],.7,[part.WHITE],xz_m=[x,z])
        for where,z in [('above',t+.035),('below',b-.025)]:
            for j in range(5):
                x=l+(r-l)*(j+1)/6
                observe(n+' / '+where+' moulding',[x,-.36,z],[0,1,0],.85,[part.EDGE,part.WHITE],xz_m=[x,z])
        for tag in ('disc_one','disc_two','central_stile','middle_stile','lower_rail','upper_rail','transom_rail'):
            if tag not in w['features']:
                continue
            x,_,z=w['features'][tag]
            selection=([part.DISC] if tag.startswith('disc_') else
                       [part.BLUEFRAME] if n=='upper_glazed' else [part.RED])
            observe(n+' / '+tag,[x,-.43,z],[0,1,0],1.1,selection,xz_m=[x,z])
    return {**scene.asset,'method':'Nearest triangle in the unfiltered decoded mesh. The first group uses original photograph pixels and its calibrated camera.', 'count':len(hits),'passed':all(i['passed']for i in hits),'checks':hits}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();j=check(args.mesh);args.output.write_text(json.dumps(j,indent=1)+'\n')
    bad=[h for h in j['checks'] if not h['passed']]
    print(j['count']-len(bad),'/',j['count'],[(h['label'],h.get('original_px'),h['first_hit'])for h in bad])
    raise SystemExit(int(bool(bad)))
