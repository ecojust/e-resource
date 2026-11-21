"""Cast rays directly into the three serialized corner facades, in model metres."""
from pathlib import Path
import argparse, hashlib, json, runpy

def check(scene):
    rows=[]
    def ray(name,origin,direction,maximum,material=None,distance=None,tolerance=.035):
        hit=scene.ray(origin,direction,maximum)
        if material is None:
            assert hit is None,(name,origin,hit)
        else:
            assert hit and hit['material']==material and abs(hit['distance_m']-distance)<=tolerance,(name,origin,material,distance,hit)
        rows.append(dict(feature=name,origin_m=origin,direction=direction,maximum_distance_m=maximum,first_hit=hit))
    def front(name,x,z,y,material):
        ray(name,[x,-6.,z],[0,1,0],12.,material,6+y)
    for x in (-.81,.78):
        front('separate narrow top light',x,17.88,.23,'grey green apartment glass')
    front('substantial pier between top windows',0.,18.0,0.,'silver grey roughcast')
    for i,(x,z) in enumerate(((-1.22,9.35),(.43,9.75),(-.78,10.18),(1.12,13.35),(-.48,14.68))):
        front('broad glazed window over entrance',x,z,.23,'green glass in lower broad window' if z<12 else 'grey green apartment glass')
    for z in (7.92,11.97,15.76):
        front('light vertical strip between broad windows',.05,z,-.0415,'pale textured panels')
    front('set back upper window',.30,5.43,.495,'grey green apartment glass')
    front('separate narrow window guard',.35,5.13,-.3645,'wrought metal window guard')
    front('narrow ledge before upper opening',.31,4.415,-.403,'light artificial stone')
    front('light hood above upper opening',.10,7.23,-.465,'light artificial stone')
    front('shallow shop canopy',.10,3.12,-.595,'dark narrow shop canopy')
    front('warm door below glazing',.15,.50,.36,'warm shop front timber')
    for x in (-1.88,1.88):
        front('stone ground wall beside shop',x,1.06,0.,'mottled grey plinth')
        for z in (4.80,5.37,5.86,6.33,6.72,7.08):
            px=x+(.013 if x>0 else -.013)
            hit=scene.ray([px,-3.,z],[0,1,0],4.)
            assert hit and hit['material'] in ('light artificial stone','pale textured panels') and 2.64<hit['distance_m']<2.83,(px,z,hit)
            rows.append(dict(feature='separate stepped projecting cheek',origin_m=[px,-3,z],direction=[0,1,0],maximum_distance_m=4.,first_hit=hit))
    import numpy as np
    params=json.loads((Path(__file__).resolve().parents[3]/'source/precise/xuhui-midget-apartments/source/parameters.json').read_bytes())
    edges=[(params['left_return_end'],params['front_left'],1),(params['front_right'],params['right_return_end'],-1)]
    for a,b,side in edges:
        a,b=np.array(a),np.array(b);mid=(a+b)/2;length=np.linalg.norm(b-a);t=(b-a)/length;n=np.array([t[1],-t[0]])
        for u,z,depth in [(side*(length/2-.80)+.13,5.03,-.23),(-side*.73+.08,5.68,.43-.118),(-side*.73+.09,13.05,.43-.118)]:
            origin=mid+t*u+n*2.9
            ray('faceted oriel or narrow return window',list(origin)+[z],list(-n)+[0],5.,'grey green apartment glass',2.9-depth)
    for x,y in ((-8.,0.),(8.,0.),(0.,6.),(0.,-3.)):
        ray('outside this limited reconstruction',[x,y,24],[0,0,-1],24)
    return rows

def run():
    parser=argparse.ArgumentParser()
    for flag in ('project','manifest','decoded','out'):parser.add_argument('--'+flag,type=Path,required=True)
    a=parser.parse_args();manifest=json.loads(a.manifest.read_bytes())
    helper=runpy.run_path(str(a.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
    variants=[]
    for role in ['full','lod','raw']:
        rec=manifest['assets'][role];file=a.manifest.parent/rec['file']
        assert h(file)==rec['sha256']
        decoded=file if role=='raw' else a.decoded/(role+'.glb')
        scene=helper['SerialScene'](decoded);probes=check(scene)
        assert len(scene.tri)==rec['triangles']
        variants.append(dict(role=role,triangles=len(scene.tri),sha256=h(file),decoded_sha256=h(decoded),samples=probes))
    data=dict(id=manifest['id'],passed=True,manifest_sha256=h(a.manifest),script_sha256=h(Path(__file__)),
              count=sum(len(v['samples'])for v in variants),variants=variants)
    a.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':run()
