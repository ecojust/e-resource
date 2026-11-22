"""Measure the stepped quoins, the glazed bay and the roof in three real GLBs."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'source/precise/jingan-xianlin-villa-no19-terrace/source'))
from read_study import decode,hit
from residence_shell import MATERIAL,ROUGH,POWDER,GLASS,BLUE,DRAIN,FASCIA,TILES,TILERIM,GREEN,RED
from courtyard_photo_plane import CAMERA,P

def review(path):
    tri,mat,_=decode(path);lo=tri.min(1);hi=tri.max(1);rows=[]
    def probe(name,origin,direction,expected,interval):
        o=np.array(origin,float);d=np.array(direction,float);d/=np.linalg.norm(d)
        active=np.ones(len(tri),bool)
        for i in np.flatnonzero(np.abs(d)<1e-10):
            active&=(lo[:,i]<=o[i]+1e-6)&(hi[:,i]>=o[i]-1e-6)
        r=hit(tri[active],mat[active],o,d)
        dist=None if r is None else float(np.linalg.norm(np.asarray(r[1])-o))
        rows.append(dict(label=name,origin_m=list(o),direction=list(d),first_material=r[0] if r else None,
                         range_m=dist,expected=expected,accepted_distance_m=interval,
                         passed=bool(r and r[0] in expected and interval[0]<=dist<=interval[1])))
    low,high=3.785,6.665
    count=round((high-low)/.0687)
    for i in range(count):
        z=low+(i+.5)*(high-low)/count
        length=(.25,.34,.44)[i%3]
        if i==count-1:
            # The photographed white overhanging fascia covers this part of
            # the upper course and the roughcast behind it.
            for dx in (.052,-.050):
                probe('Fascia covering upper quoin course',[1.913-length+dx,-.15,z],[0,1,0],['No.19 terrace | white rendered fascia'],[.110,.120])
            continue
        probe('Stepped corner, exposed course',[1.913-length+.052,-.15,z],[0,1,0],[MATERIAL],[.125,.135])
        probe('Roughcast beside the end of the same course',[1.913-length-.050,-.15,z],[0,1,0],[ROUGH],[.149,.151])
    for y in (.86,1.52,2.68,3.14):
        for z in (4.90,5.35,5.58,6.12):
            probe('Three garden lights',[2.07,y,z],[-1,0,0],[GLASS],[.32,.35])
    for y in (2.53,3.04,3.73,4.02,4.87,5.19):
        for z in (8.20,8.50,8.92,9.12):
            probe('Upper blue glass front',[1.80,y,z],[-1,0,0],[BLUE],[.46,.49])
    for x in (.30,.59,.93,1.23):
        for z in (8.01,8.55,8.88):
            probe('Sunroom side return',[x,1.91,z],[0,1,0],[BLUE],[.38,.40])
    for z in (3.065,3.20,3.335,3.42,3.645,3.783):
        for y in (1.32,2.47,3.66):
            probe('White horizontal belt',[2.30,y,z],[-1,0,0],[POWDER],[.23,.35])
    for x in (-8.72,-7.23,-4.37,-1.36):
        for y in (.28,1.12,2.22,3.70,5.62):
            surface=10.62+.37*((y+.33)/3.34 if y<3.01 else (6.40-y)/3.39)
            probe('Roof tile or overlap',[x,y,surface+.15],[0,0,-1],[TILES,TILERIM],[.107,.155])
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(tri),cases=rows,passed=all(x['passed']for x in rows))

if __name__=='__main__':
    data={role:review(Path(p))for role,p in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    for k,v in data.items():
        print(k,len(v['cases']),[(x['label'],x['first_material'],x['range_m'])for x in v['cases']if not x['passed']][:16])
    sys.exit(0 if all(v['passed']for v in data.values())else 1)
