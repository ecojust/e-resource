"""Compare the visible 2018 arch with the front triangles of an exported GLB."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,Point
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
sys.path.insert(0,str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from build_model import SCALE
from wing_finishes import ROUGHCAST
from glb_triangles import SerialScene

def inspect(mesh):
    survey=json.loads((HERE/'loggia-arch-control.json').read_bytes())
    c=json.loads((HERE/'front-camera.json').read_bytes())
    K,R,C=(np.asarray(c[k]) for k in ['intrinsic','world_to_camera','camera_centre'])
    inv=R.T@np.linalg.inv(K);eye=C*SCALE
    def glass_plane(pixel):
        ray=inv@[*pixel,1.];xyz=eye-ray*(eye[1]/ray[1])
        return xyz[[0,2]]
    scene=SerialScene(mesh);tid=scene.materials.index(ROUGHCAST)
    ids=np.where((scene.mi==tid)&(np.max(np.abs(scene.tri[:,:,1]),axis=1)<.00005))[0]
    surface=unary_union([Polygon(scene.tri[i][:,[0,2]])for i in ids])
    c=survey['model_parameters']
    mid=np.array([c['centre_x'],c['spring_z']])*SCALE
    rad=np.array([c['radius_x'],c['rise']])*SCALE
    rows=[]
    def pixel(xz):
        p=K@R@(np.r_[xz[0],0.,xz[1]]-eye)
        return p[:2]/p[2]
    for pp in survey['selected_control_xy_px']:
        p=np.array(pp);xz=glass_plane(p)
        radial=(xz-mid)/rad**2;radial/=np.linalg.norm(radial)
        norm=pixel(xz+radial*.05)-p;norm/=np.linalg.norm(norm)
        def facade(t):
            return surface.covers(Point(glass_plane(p+t*norm)))
        inner,outer=-9.,9.
        if facade(inner) or not facade(outer):
            rows.append({'photo_xy':pp,'bracketed':False});continue
        for _ in range(15):
            t=(inner+outer)/2
            if facade(t):outer=t
            else:inner=t
        rows.append({'photo_xy':pp,'bracketed':True,'edge_error_px':round(float((outer+inner)/2),4)})
    errors=[abs(r['edge_error_px'])for r in rows if r['bracketed']]
    return dict(asset=scene.asset,unit='pixels of the 1300 × 731 photo',photo_readings=len(rows),
                traced_edges=len(errors),exported_front_triangles=len(ids),
                median_absolute_error=float(np.median(errors)),p90_absolute_error=float(np.percentile(errors,90)),
                maximum_absolute_error=max(errors),observations=rows)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();r=inspect(args.mesh)
    args.output.write_text(json.dumps(r,indent=2,ensure_ascii=False)+'\n')
    print(r['traced_edges'],r['photo_readings'],round(r['median_absolute_error'],3),round(r['p90_absolute_error'],3))
