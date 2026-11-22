"""Measure the sash rails, masonry hoods, recessed glass and roof covering in the complete residence."""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/jingan-lutheran-residence-changde-310/source'
sys.path.insert(0,str(SRC))
from read_study import decode,hit
import residence_fabric as s

def review(path):
 tri,mat,_=decode(path);lo=tri.min(1);hi=tri.max(1);rows=[]
 def shot(label,point,direction,expected,interval):
    o=np.array(point,float);d=np.array(direction,float);d/=np.linalg.norm(d)
    subset=np.ones(len(tri),bool)
    for j in np.flatnonzero(np.abs(d)<1e-11):subset&=(lo[:,j]<=o[j]+1e-6)&(hi[:,j]>=o[j]-1e-6)
    inter=hit(tri[subset],mat[subset],o,d)
    distance=None if inter is None else float(np.linalg.norm(np.asarray(inter[1])-o))
    rows.append(dict(label=label,origin=o.tolist(),direction=d.tolist(),expected_materials=expected,depth_range_m=interval,actual=inter[0] if inter else None,depth=distance,passed=bool(inter and inter[0] in expected and interval[0]<=distance<=interval[1])))
 for row in s.DATA['windows']:
    if row['key'].startswith('bay ') and row['face']=='right':continue
    l,r,b,sp,t=[row[k] for k in ['left','right','bottom','spring','top']]
    side=row['face']=='right'; y=row['plane_m'];key=row['key']
    def send(x,z,materials,depth,offset=.40):
        point=[y+offset,x,z] if side else [x,y-offset,z]
        shot(key,point,[-1,0,0] if side else [0,1,0],materials,[v+offset for v in depth])
    for x in (l+.21*(r-l),l+.68*(r-l)):
        send(x,b-.044,[s.STONE],[-.131,-.129])
    for frac in (.15,.38,.61,.85):
        send(l+(r-l)*frac,b+(sp-b)*.27,[s.GLASS,s.LIGHT,s.DARK],[.187,.254])
    if row['profile']=='tympanum':send((l+r)/2,sp,[s.RED],[-.070,-.066])
    else:send((l+r)/2,sp,[s.WOOD,s.PALE],[.108,.176])
    if row['profile'] in ('shallow','shuttered'):send((l+r)/2,t+.23,[s.BRIGHT],[-.093,-.089])
    else:send((l+r)/2,t+.23,[s.BRIGHT],[-.143,-.139])
 for x,y in [(-9.4,.11),(-7.27,.71),(-.32,2.01),(1.12,2.13),(5.28,3.43),(6.25,4.92),(11.2,4.55)]:
    shot('Hipped roof clay and overlapping tile rolls',[x,y,24],[0,0,-1],[s.CLAY,s.GROOVE,s.SHADOW],[2.4,12.9])
 result=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(tri),passed=all(r['passed']for r in rows),cases=rows)
 return result
if __name__=='__main__':
 roles=('raw','full','lod');paths=list(map(Path,sys.argv[1:4]))
 result={k:review(p) for k,p in zip(roles,paths)}
 Path(sys.argv[4]).write_text(json.dumps(result,indent=2)+'\n')
 for k,v in result.items():
    print(k,len(v['cases']),sum(r['passed'] for r in v['cases']),flush=True)
    if not v['passed']:raise ValueError([(r['label'],r.get('actual'),r['depth'])for r in v['cases']if not r['passed']][:12])
