"""Verify model extent and registered pixel directions in the nine published cameras."""
from pathlib import Path
import argparse, hashlib,json,runpy
import numpy as np
from register_court import Camera

HERE=Path(__file__).absolute().parent
CAMERAS=HERE.parent/'source/cameras.json'
HELPER=HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py'
LOAD=runpy.run_path(str(HELPER))['load_triangles']
# Small groups of built points select the subject of each auxiliary camera.
SUBJECT={
    'entry':[(-.92,0,.84),(.92,0,3.48),(0,1.07,2.80)],
    'plaque':[(1.14,0,2.60),(1.37,0,2.44),(1.31,0,1.98)],
    'balconies':[(4.10,-.19,1.),(6.92,-.19,2.),(4.12,-.19,12.85),(6.90,-.19,12.85)],
    'openwork':[(4.13,-.19,3.84),(6.88,-.19,4.91),(5.49,-.19,4.55)],
    'court-windows':[(-2.68,0,4.83),(3.05,0,6.16),(-2.63,0,9.29),(3.08,0,7.85),(.12,0,4.36)],
    'upper-eave':[(4.10,0,10.1),(6.90,-.19,12.85),(-.86,0,12.35),(3.10,0,13.13)],
}

def setup(v):
    eye,target=np.array(v['eye']),np.array(v['target'])
    axis=target-eye;dist=np.linalg.norm(axis); axis/=dist
    up=np.array(v.get('world_up',[0,0,1]),dtype=float)
    right=np.cross(axis,up);right/=np.linalg.norm(right);up=np.cross(right,axis)
    r=np.stack([right,-up,axis]);w,h=v['width'],v['height']
    f=w*dist/v['width_m'];center=np.array([(w-1)/2,(h-1)/2])
    def project(p):
        local=(p-eye)@r.T
        return local[:,:2]*f/local[:,2:]+center
    return project,f

def check(path):
    tri,_,_,asset=LOAD(path);vertices=tri.reshape(-1,3)
    result=[]
    picks=json.loads((HERE/'independent-court-pixels.json').read_text())
    for view in json.loads(CAMERAS.read_text()):
        project,f=setup(view);name=view['name'];w,h=view['width'],view['height']
        if name.startswith('photo-'):
            key='04' if name.endswith('2013') else '25';camera=Camera(key)
            observed=np.array([r['xy'] for g in picks['views'] if g['camera']==key for r in g['controls']])
            xyz=np.stack([camera.wall(row,0) for row in observed]);uv=project(xyz)
            error=float(np.max(np.linalg.norm(uv-observed,axis=1)))
        else:
            xyz=vertices if name=='overview' else np.array(SUBJECT[name],dtype=float)
            uv=project(xyz);error=None
        lo=uv.min(axis=0);hi=uv.max(axis=0)
        ok=bool(lo[0]>=-.5 and lo[1]>=-.5 and hi[0]<=w-.5 and hi[1]<=h-.5 and (error is None or error<.001))
        result.append({'name':name,'size':[w,h],'focal_length_px':f,'points':len(xyz),'native_uv_bounds':[lo.tolist(),hi.tolist()],
                       'physical_camera_reprojection_max_px':error,'framed':ok})
    return {'asset':asset,'cameras_sha256':hashlib.sha256(CAMERAS.read_bytes()).hexdigest(),'views':result,'all_framed':all(v['framed']for v in result)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    r=check(a.mesh);a.output.parent.mkdir(exist_ok=True,parents=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print([(v['name'],v['framed'])for v in r['views']])
