"""Reproject the measured eave lines and test the fixed roof/stack pixels against a GLB."""
import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent.parent/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
from register_street import Camera


def check(path):
    marks=json.loads((HERE/'roof-edge-photo-controls.json').read_text())
    cams={}
    def cam(k):
        if k not in cams:cams[k]=Camera(k)
        return cams[k]
    def fit_corner(xyz):
        return [v for k,p in marks['outer_corner_native'].items() for v in cam(k).pixel(xyz)-p]
    # IRLS for the soft-L1 reprojection loss, without a nonlinear solver dependency.
    corner=np.array([2.7,-.4,10.85])
    for _ in range(60):
        residual=np.array(fit_corner(corner))
        columns=[(np.array(fit_corner(corner+step*1e-5))-residual)/1e-5 for step in np.eye(3)]
        jacobian=np.column_stack(columns)
        weight=(1+residual**2)**-.25
        delta=np.linalg.lstsq(jacobian*weight[:,None],-residual*weight,rcond=None)[0]
        corner+=delta
        if np.linalg.norm(delta)<1e-9:
            break
    heights={}
    for name,y in [('top',-.419),('fascia',-.38),('inner',0.)]:
        heights[name]={k:[round(float(cam(k).wall(p,y)[2]),3)for p in pp]
                       for k,pp in marks['front_fitted_lines_native'][name].items()}
    scene=SerialScene(path)
    checks=[]
    for item in marks['held_out_native']:
        c=cam(item['station']);p=np.array(item['native_uv']); want=marks['surfaces'][item['surface']]
        radius=round(c.size[0]*.006)
        def material(dx,dy):
            hit=scene.ray(c.c,c.ray(p+[dx,dy]),50)
            return hit['material'] if hit else None
        primary=material(0,0)
        nearest=[0,0] if primary==want else None
        if nearest is None:
            directions=[(-1,0),(0,-1),(0,1),(1,0),(-.707,-.707),(.707,-.707),(.707,.707),(-.707,.707)]
            for r in sorted(set(max(1,round(radius*s))for s in [.2,.4,.6,.8,1.])):
                for dx,dy in directions:
                    off=[round(r*dx),round(r*dy)]
                    if material(*off)==want:nearest=off;break
                if nearest:break
        checks.append({**item,'expected':want,'first_hit_material':primary,
                       'first_hit_matches':primary==want,'search_radius_native_px':radius,'nearest_matching_offset_px':nearest})
    return {'asset':scene.asset,'fitted_outer_corner_m':corner.tolist(),
            'outer_corner_native_residual_xy_px':np.round(np.reshape(fit_corner(corner),(-1,2)),2).tolist(),
            'front_edge_z_samples_m':heights,'observations':checks,
            'summary':{'observations':len(checks),'exact_first_material':sum(o['first_hit_matches'] for o in checks),
                       'material_within_bound':sum(o['nearest_matching_offset_px'] is not None for o in checks)}}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('asset',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();report=check(args.asset);args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(report['asset']['sha256'],report['summary'])
