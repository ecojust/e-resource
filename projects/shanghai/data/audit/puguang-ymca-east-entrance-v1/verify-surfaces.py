"""First-hit tests against each exported mesh for the whole joined street front."""
import argparse,json,math
from hashlib import sha256
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[2]
ID='huangpu-puguang-ymca-east-entrance'
SOURCE=PROJECT/'source/precise'/ID/'source'
read=lambda p:json.loads(p.read_bytes())

def verify(work,out):
    bundle=read(HERE/'stone-entrance-rays.json')
    assert bundle['source_sha256']==sha256((SOURCE/'stone_entrance.py').read_bytes()).hexdigest()
    all_results={}
    for row in read(work/'delivered-decode.json'):
        kind=row['variant'];lod=kind=='lod'
        v=np.fromfile(row['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        names=np.array(row['material_names'])[np.fromfile(row['triangle_material_ids_file'],np.uint16)]
        assert len(names)==len(v)==row['triangles']
        low=v.min(axis=1);high=v.max(axis=1);checks=[]
        def sample(label,x,z,expected,depth=None):
            ix=np.flatnonzero((low[:,0]<=x+.000001)&(high[:,0]>=x-.000001)&(low[:,2]<=z+.000001)&(high[:,2]>=z-.000001))
            vv=v[ix];a=vv[:,1]-vv[:,0];b=vv[:,2]-vv[:,0];X=x-vv[:,0,0];Z=z-vv[:,0,2]
            det=a[:,0]*b[:,2]-b[:,0]*a[:,2]
            with np.errstate(divide='ignore',invalid='ignore'):
                u=(X*b[:,2]-b[:,0]*Z)/det;t=(a[:,0]*Z-X*a[:,2])/det
                use=(np.abs(det)>1e-9)&(u>=-1.e-6)&(t>=-1.e-6)&(u+t<=1.000001)
            good=np.flatnonzero(use)
            if len(good):
                ys=vv[good,0,1]+u[good]*a[good,1]+t[good]*b[good,1]
                best=good[ys.argmin()];tri=ix[best];d=-float(ys.min());material=str(names[tri])
                n=np.cross(a[best],b[best]);facing=float(-n[1]/np.linalg.norm(n))
            else:d=material=facing=None
            expected=[expected] if isinstance(expected,str) else expected
            ok=(material in expected and (depth is None or depth[0]-.0035<=d<=depth[1]+.0035) and facing is not None and facing>.24)
            checks.append(dict(target=label,x=x,z=z,material=material,expected=expected,front_d_m=d,depth_range=depth,front_normal=facing,passed=bool(ok)))
        for rec in bundle['checks']['lod'if lod else'full']['probes']:
            d=rec['front_d_m']
            sample(rec['detail'],rec['x_m'],rec['z_m'],rec['material'],[d-.007,d+.007])
        for x,lbl in [(-5.69,'south'),(.08,'entrance axis'),(5.75,'north')]:
            for z in (8.80,13.12):
                sample(lbl+' recessed upper glass',x+.28,z,'sky grey upper glass',[-.275,-.265])
                sample(lbl+' upper wood centre mullion',x,z,'reddish brown shop sash',[-.109,-.099])
        sample('central extended sash behind top of English lintel',.39,6.64,'sky grey upper glass',[-.28,-.26])
        for side in (-1,1):
            sample('column at split pediment',side*2.05,9.5,'orange radial brick',[.495,.518])
            sample('rebated masonry course',side*2.94,8.31,'exposed warm Shanghai brick',[.30,.32])
            sample('pilaster in a recessed bed joint',side*2.94,7.634,'deep bed in channelled brickwork',[.209,.233])
            sample('attached column plinth',side*2.05,7.466,'edge of pediment stone',[.47,.51])
            sample('capital under split pediment',side*2.05,11.345,'edge of pediment stone',[.56,.58])
            sample('raking stone under the broken apex',side*1.62,12.865,'sand grey pediment stone',[.37,.46])
            sample('original wall beside split pediment',side*4.22,12.27,'exposed warm Shanghai brick',[-.027,-.019])
        for x,sz,rise,side in [(-6.895,4.535,1.08,'south'),(6.99,4.57,.985,'north')]:
            for u in (-.5,.48):
                sample(side+' shop fanlight glass',x+u,sz+.44,'shadow glass in shop fanlights',[-.395,-.385])
            sample(side+' fanlight centre bar',x,sz+.43,'reddish brown shop sash',[-.224,-.212])
            sample(side+' shop keystone',x,6.09,'edge of pediment stone',[.172,.181])
            for phi in (.52,1.04,2.15,2.57):
                radius=2.185 if side=='south' else 2.12
                sample(side+' curved fired brick',x+(radius+.16)*math.cos(phi),sz+(rise+.18)*math.sin(phi),
                       ['pink radial brick','orange radial brick','umber radial brick'],[.088,.098])
        sample('south shop inset horizontal pane',-6.625,2.27,'shadow glass in shop fanlights',[-.277,-.264])
        sample('south shop later brick below the glazing',-6.75,1.04,'exposed warm Shanghai brick',[-.28,-.268])
        sample('north shop corrugated closure',6.62,2.444,['pale blue grey shutter','shutter profile shadows'],[-.34,-.308])
        sample('north side rail at shutter',6.99+2.12-.055,2.51,'shutter profile shadows',[-.112,-.101])
        bad=[r for r in checks if not r['passed']]
        all_results[kind]=dict(sha256=row['sha256'],triangles=len(v),tested=len(checks),passed=not bad,rays=checks)
        if bad:print(kind,[(t['target'],t['material'],t['front_d_m'],t['front_normal'])for t in bad][:22],flush=True)
    passed=all(r['passed']for r in all_results.values()) and set(all_results)=={'raw','web','lod'}
    out.write_text(json.dumps(dict(id=ID,passed=passed,checks=all_results,source_checker_sha256=sha256(Path(__file__).read_bytes()).hexdigest()),ensure_ascii=False,indent=2)+'\n')
    print([(k,v['tested'],v['passed'])for k,v in all_results.items()])
    assert passed
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--work',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();verify(a.work,a.out)
