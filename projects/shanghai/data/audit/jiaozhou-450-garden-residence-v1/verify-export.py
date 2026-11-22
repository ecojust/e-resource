"""Measure directly on the decoded gable, chimney and tile surfaces of the released house."""
import hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/jingan-jiaozhou-450-garden-residence/source'
sys.path.insert(0,str(SOURCE))
from read_study import decode,hit
from west_gable_and_roof import OPENINGS,FRAME,LEAF,SHADOW,BRICK_HEAD,ROOF_TONES,ROOF,roof_z
import garden_arcade as arcade

def review(path):
    tri,mat,_=decode(path);lo=tri.min(1);hi=tri.max(1);rows=[]
    def probe(label,origin,direction,expected,range_m):
        o=np.asarray(origin,float);d=np.asarray(direction,float);active=np.ones(len(tri),bool)
        for i in np.flatnonzero(np.abs(d)<1e-10):
            active&=(lo[:,i]<=o[i]+1e-6)&(hi[:,i]>=o[i]-1e-6)
        found=hit(tri[active],mat[active],o,d)
        dist=None if found is None else float(np.linalg.norm(np.asarray(found[1])-o))
        rows.append(dict(label=label,origin=o.tolist(),direction=d.tolist(),expected=expected,first=found,distance_m=dist,
                         passed=bool(found and found[0] in expected and range_m[0]<=dist<=range_m[1])))
    for win in OPENINGS:
        l,z,r,t=win['yz'];center=(l+r)/2;n=win['louvre_rows'];name=win['label']
        def west(y,h,material,interval,part):probe(name+' | '+part,[-.5,y,h],[1,0,0],material,interval)
        for y in (l+.022,r-.022):west(y,(z+t)/2,[FRAME],(.585,.605),'side frame')
        west(center,z-.041,[BRICK_HEAD],(.38,.41),'projected sill')
        west(center,t+.09,[BRICK_HEAD,arcade.FACE],(.47,.505),'flat brick lintel')
        west(r+.14,(z+t)/2,[arcade.FACE],(.49,.51),'solid outer wall')
        for j in range(win['leaves']):
            y=l+(r-l)*(j+.5)/win['leaves']
            for i in range(n):
                h=z+.047+(i+.48)*(t-z-.094)/n
                west(y,h,[LEAF],(.60,.68),'sloping blade '+str(i+1))
        if win['leaves']==2:west(center,(z+t)/2,[FRAME],(.57,.60),'two-leaf meeting stile')
    for xx in (1.1,4.,6.4,8.,12.,15.5,16.15):
        for yy in (3.6,4.20,5.2,7.6,9.6,10.5,11.8,12.7):
            if 6.792<=xx<=15.081 and 4.55<=yy<=9.17:continue
            zz=roof_z(yy)
            probe('South tile profile',[xx,yy,zz+.6],[0,0,-1],ROOF_TONES,(.49,.70))
    for xx in (2.,5.,10.,14.):
        for yy in (14.,16.,18.):
            h=ROOF['ridge_z']-(yy-ROOF['ridge_y'])*(ROOF['ridge_z']-10.07)/(19.32-ROOF['ridge_y'])
            probe('North tile profile',[xx,yy,h+.5],[0,0,-1],ROOF_TONES,(.38,.63))
    for y in (.86,1.04,1.43,1.81,2.27,2.65,3.04):
        theta=np.arccos((y-2.02)/1.30);z=2.82+1.035*np.sin(theta)
        probe('West return arch | brick ring',[-1.,y,z+.16],[1,0,0],[*arcade.RINGS,arcade.JOINT],(.97,1.05))
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(tri),cases=rows,passed=all(r['passed'] for r in rows))
if __name__=='__main__':
    rec={k:review(Path(s))for k,s in zip(('raw','full','lod'),sys.argv[1:4])}
    Path(sys.argv[4]).write_text(json.dumps(rec,indent=2,ensure_ascii=False)+'\n')
    for k,j in rec.items():print(k,len(j['cases']),[(v['label'],v['first'])for v in j['cases'] if not v['passed']],flush=True)
    sys.exit(0 if all(j['passed'] for j in rec.values()) else 1)
