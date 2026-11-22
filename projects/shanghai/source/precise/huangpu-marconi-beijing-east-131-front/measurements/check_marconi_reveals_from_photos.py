"""Verify that both photographed views see masonry, sash or recess at the former open sides."""
import argparse,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from marconi_photo_plane import CALIBRATION
from glb_triangles import SerialScene
def inspect(path):
    src=json.loads((HERE/'photographic-reveal-sightlines.json').read_text())
    scene=SerialScene(path);records=[]
    for group in src['patches']:
        P=np.array(CALIBRATION['camera_matrices'][group['camera']]);A=P[:,:3]
        eye=-np.linalg.solve(A,P[:,3])
        for uv in group['witnesses_px']:
            ray=np.linalg.solve(A,[*uv,1.]);ray/=np.linalg.norm(ray)
            hit=scene.ray(eye,ray,100.)
            xyz=hit['point_enu_m'] if hit else None
            ok=bool(hit and -.9<xyz[1]<1.90 and 1.<xyz[2]<25)
            records.append(dict(camera=group['camera'],source_pixel=uv,first_material=hit['material']if hit else None,point_m=xyz,passed=ok))
    return dict(**scene.asset,views=src['cameras'],photographic_patches=len(src['patches']),passed=all(v['passed'] for v in records),rays=len(records),checks=records)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mesh',type=Path);p.add_argument('report',type=Path);args=p.parse_args()
    result=inspect(args.mesh);args.report.write_text(json.dumps(result,indent=1,ensure_ascii=False)+'\n')
    print(sum(x['passed']for x in result['checks']),result['rays'])
    raise SystemExit(int(not result['passed']))
