"""Check the entire mesh at three published cameras, including the full triangular roof outline."""
from pathlib import Path
import sys, argparse,json
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def bounds(cam,points):
    eye=np.array(cam['eye'],float); forward=np.array(cam['target'],float)-eye
    distance=np.linalg.norm(forward);forward/=distance
    right=np.cross(forward,[0,0,1]);right/=np.linalg.norm(right)
    up=np.cross(right,forward)
    offset=points-eye; depth=offset@forward
    assert depth.min()>0
    w=cam['width_m'];h=w*cam['height']/cam['width']
    u=.5+(offset@right)*distance/(depth*w)
    v=.5+(offset@up)*distance/(depth*h)
    return [float(t)for t in (u.min(),u.max(),v.min(),v.max())]

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('packaged',type=Path);parser.add_argument('out',type=Path);args=parser.parse_args()
    cams=json.loads((HERE.parent/'source/cameras.json').read_bytes())
    files=[next(args.packaged.glob('*-raw.glb')),args.packaged/'decoded-full.glb',args.packaged/'decoded-lod.glb']
    result={}
    for file in files:
        scene=SerialScene(file);points=scene.tri.reshape(-1,3);views={}
        for c in cams:
            if c['name'] not in ['overview','roof','plan']:continue
            box=bounds(c,points)
            assert min(box)>.035 and max(box)<.965,(c['name'],box)
            views[c['name']]=box
        result[file.name]={'asset':scene.asset,'xy_bounds_from_lower_left_0_1':views}
    args.out.write_text(json.dumps(result,indent=2)+'\n')
