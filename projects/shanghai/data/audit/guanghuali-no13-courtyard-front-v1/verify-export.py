"""Measure the outside-face intersections of the canted facade and broad sash."""
from pathlib import Path
import hashlib,json,math,sys
import numpy as np
SRC=Path(__file__).resolve().parents[3]/'source/precise/jingan-guanghuali-no13-courtyard-front/source'
sys.path.insert(0,str(SRC))
from read_study import decode,hit
import residential_facade as f

def inspect(path):
    tris,materials,_=decode(path)
    samples=[]
    def cast(label,origin,along,expected,span):
        origin=np.asarray(origin);along=np.asarray(along)
        actual=hit(tris,materials,origin,along)
        distance=float(np.linalg.norm(np.array(actual[1])-origin)) if actual else None
        passed=bool(actual and actual[0] in expected and span[0]<=distance<=span[1])
        samples.append(dict(label=label,origin=origin.tolist(),direction=along.tolist(),expected=expected,depth_m=span,hit=actual[0] if actual else None,measured_m=distance,passed=passed))
    off=np.asarray(f.PLACE['origin'])
    for panel in f.SURVEY['panels']:
        w=f.Face(None,panel['from'],panel['to'],panel['label'])
        tangent=np.r_[w.axis,0];normal=np.r_[w.normal,0]
        def test(name,x,z,expected,y0,y1,start=-.36):
            origin=np.array(w.point(x,z,start))+off
            cast(w.tag+' '+name,origin,normal,expected,[y0-start-.002,y1-start+.002])
        l,r,b,t=[panel[k] for k in ('trim_left','trim_right','trim_bottom','trim_top')]
        for j in [1,3,5,7]:
            for edge in [l+.052,r-.051]:test('grey rendered jamb',edge,b+(t-b)*j/8,[f.GREY],-.033,-.031)
        for j in range(1,7):test('sill',l+(r-l)*j/7,b-.022,[f.GREY],-.131,-.128)
        for x in [l+.109,r-.134]:test('stone sill bracket',x,b-.267,[f.GREY],-.065,-.063)
        for x in [l+.12,r-.13]:
            for z in [b-.49,b-.68]:test('brickwork beneath sill',x,z,[f.BRICK],-.001,.001)
        a=l+.12;c=r-.12;recess=panel['frame_recess_m'];bar=panel['upper_transom_z']
        leaves=panel['columns'];width=(c-a)/leaves
        for j in range(leaves):
            if j==0 and w.tag=='Front bay face':continue
            for h in range(4):
                z=(b+.138)+(bar-.144-b-.138)*(h+.37)/4
                test('casement glass',a+(j+.51)*width,z,f.GLASS,recess-.022+.003,recess-.022+.006)
        for u in [.21,.77]:
            test('transom glass',a+u*(c-a),(bar+t-.15)/2,f.GLASS,recess-.003,recess+.002)
        test('upper stone head',(l+r)/2,t-.05,[f.GREY],-.034,-.031)
        if panel['lower_window_head_z'] is not None:
            test('lower opening lintel',(l+r)/2,panel['lower_window_head_z']-.04,[f.GREY],-.035,-.033)
    return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),triangles=len(tris),passed=all(s['passed']for s in samples),cases=samples)
if __name__=='__main__':
    paths=[Path(k)for k in sys.argv[1:4]]
    results={role:inspect(path)for role,path in zip(['raw','full','lod'],paths)}
    Path(sys.argv[4]).write_text(json.dumps(results,indent=2)+'\n')
    for key,j in results.items():
        misses=[(s['label'],s['hit'],s['measured_m']) for s in j['cases']if not s['passed']]
        print(key,len(j['cases']),len(misses),misses[:8]);assert not misses
