"""Sample the wave and the cartouche on the stored entrance geometry."""
import argparse
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene

def check(mesh):
    scene=SerialScene(mesh)
    data=json.loads((HERE/'portal-profile.json').read_bytes())
    scale=np.array(json.loads((HERE/'model-to-street-control.json').read_bytes())['solutions']['combined']['model_scales_xyz'])
    x0=582/50-12.2
    head=16.75-726/50
    rows=[]
    for name,points,claimed in [('wave',data['wave_upper_profile_px'],.226),
                                ('cartouche',data['cartouche_outline_px'],.185)]:
        for u,v in points[1:-1]:
            x=x0+(u-407)/224*(642-582)/50
            z=head+(428-v)*.00533
            h=scene.ray(np.array([x,-3,z])*scale,[0,1,0],4)
            protrusion=-h['point_enu_m'][1] if h else None
            expect=claimed*scale[1]
            ok=bool(h is not None and abs(protrusion-expect)<.009)
            rows.append(dict(profile=name,pixel_xy=[u,v],depth_from_brick_face_m=protrusion,
                             expected_rim_depth_m=expect,material=h['material'] if h else None,hit_rim=ok))
    return dict(asset=scene.asset,reference=data['working_2015_image'],
                method='Flat front registration from the door header followed by the documented metric scales. A perpendicular ray checks actual relief height at each retained photograph mark; the cast depth itself is inferred.',
                hit=sum(v['hit_rim'] for v in rows),total=len(rows),samples=rows)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();r=check(args.mesh);args.output.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    print(r['hit'],r['total'])
