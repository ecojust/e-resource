"""Check the gallery mullions, white sill, three-sided balustrade and west returns in decoded GLBs."""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
HERE=Path(__file__).resolve().parent
SRC=HERE.parents[2]/'source/precise/jingan-daren-school-kangding-20-street-front/source'
sys.path.insert(0,str(SRC))
from read_study import decode,hit
import school_fabric as s
import street_brick_arcade as a

def review(path):
 tri,mat,_=decode(path);lo=tri.min(1);hi=tri.max(1);rows=[]
 def shot(label,point,direction,expected,interval):
    o=np.array(point,float);d=np.array(direction,float);d/=np.linalg.norm(d)
    subset=np.ones(len(tri),bool)
    for j in np.flatnonzero(np.abs(d)<1e-11):subset&=(lo[:,j]<=o[j]+1e-6)&(hi[:,j]>=o[j]-1e-6)
    inter=hit(tri[subset],mat[subset],o,d)
    distance=None if inter is None else float(np.linalg.norm(np.asarray(inter[1])-o))
    rows.append(dict(label=label,origin=o.tolist(),direction=d.tolist(),expected_materials=expected,depth_range_m=interval,actual=inter[0] if inter else None,depth=distance,passed=bool(inter and inter[0] in expected and interval[0]<=distance<=interval[1])))
 for o in s.OPENINGS:
    i=o['number'];l,r,z,t=o['left'],o['right'],o['bottom'],o['top'];n=4 if r-l>1.5 else 2
    for x in np.linspace(l+.0205,r-.0205,n+1):
        shot('Window '+str(i)+' full-height stile',[x,-.50,z+.38],[0,1,0],[s.STEEL],[.652,.656])
    for frac in (.17,.43,.73):
        x=l+(r-l)*frac
        shot('Window '+str(i)+' stone sill',[x,-.50,z-.029],[0,1,0],[s.CHALK],[.396,.401])
        shot('Window '+str(i)+' head rail',[x,-.50,t-.32],[0,1,0],[s.STEEL],[.649,.655])
    for k in range(n):
        x=l+.041+(r-l-.082)*(k+.30)/n
        shot('Window '+str(i)+' lower daylight opening',[x,-.5,z+(t-z)*.42],[0,1,0],[s.LIGHT,s.DARK,s.MID,s.SHADE],[.679,.701])
 ps=np.asarray(json.loads((SRC.parent/'measurements/video-terrace-and-roof.json').read_text())['triangulated_terrace_cap_centres_xyz_m'])
 for p,q,count in zip(ps,ps[1:],(15,2,14)):
    u=q[:2]-p[:2];length=np.linalg.norm(u);u/=length;out=np.array([u[1],-u[0]])
    for i in range(count):
        xy=p[:2]+u*(.218+(length-.436)*(i+.5)/count)
        shot('Turned terrace baluster',list(xy+out*.28)+[5.48],list(-out)+[0],[s.CREAM],[.195,.26])
    for i in range(count-1):
        xy=p[:2]+u*(.218+(length-.436)*(i+1)/count)
        # Look through the gap and stop before the house wall.
        ray=np.r_[xy+out*.28,5.48];d=np.r_[-out,0];mask=(lo[:,2]<=5.48)&(hi[:,2]>=5.48)
        inter=hit(tri[mask],mat[mask],ray,d)
        depth=None if inter is None else float(np.linalg.norm(np.asarray(inter[1])-ray));rows.append(dict(label='Open air between terrace balusters',origin=ray.tolist(),direction=d.tolist(),nearest=inter[0]if inter else None,depth=depth,passed=bool(depth is None or depth>.55)))
 for l,r in ((.56,1.74),(4.74,6.01),(10.19,11.46)):
    x=(l+r)/2;shot('West return upper central leaf',[-.4,x,10.22],[1,0,0],[s.STEEL],[.52,.53])
 for x in (1.7,3.98,16.02,19.,21.,23.21):
    for y in (.4,.9,1.4,2.3):
        shot('Street roof terracotta tile',(x,y,19.),[0,0,-1],s.TILES+[s.RED],[2.,8.2])
 result=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(tri),passed=all(r['passed']for r in rows),cases=rows)
 return result
if __name__=='__main__':
 roles=('raw','full','lod');paths=list(map(Path,sys.argv[1:4]))
 result={k:review(p) for k,p in zip(roles,paths)}
 Path(sys.argv[4]).write_text(json.dumps(result,indent=2)+'\n')
 for k,v in result.items():
    print(k,len(v['cases']),sum(r['passed'] for r in v['cases']),flush=True)
    if not v['passed']:raise ValueError([(r['label'],r.get('actual'),r['depth'])for r in v['cases']if not r['passed']][:12])
