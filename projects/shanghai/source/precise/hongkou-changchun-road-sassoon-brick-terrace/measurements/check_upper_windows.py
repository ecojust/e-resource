"""First-surface checks on the released mesh, in the two original image spaces."""
from pathlib import Path
import argparse,hashlib,json,sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE.parent/'source'),str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact')]
from glb_triangles import SerialScene
from frontage_coordinates import EARLIER_CAMERA,FRONT_CAMERA,WINDOW_PLANES,facade_point
from shapely.geometry import Point
from upper_windows import PALETTE, opening_profiles
def inspect(asset):
    cams={'front':FRONT_CAMERA,'gao':EARLIER_CAMERA}
    scene=SerialScene(asset);profiles=opening_profiles();rows=[]
    known={'front':'9365c13fb25027eb54721ec1a4e21f87d7c32f8b78b0815a3fdae90f879a6381','gao':'50521aa6ca12d583de1a0789535ae65530dbd7e98b68b8580c76648a2d310793'}
    for item in json.loads((HERE/'upper-window-ray-observations.json').read_bytes())['test']:
        which=item['view'];uv=item['uv'];bay=int(item['window'][-2:]);wall=WINDOW_PLANES[bay];p=cams[which]
        eye=-np.linalg.solve(p[:,:3],p[:,3]);target=np.asarray(facade_point(*uv,wall,camera=p))
        got=scene.ray(eye,target-eye,np.linalg.norm(target-eye)+1.3)
        mat=got['material'] if got else None;xyz=np.asarray(got['point_enu_m']) if got else None
        correct=mat in PALETTE
        if item.get('accepted'):correct=mat in item['accepted']
        within=bool(got and profiles[item['window']].buffer(.002).covers(Point(xyz[0],xyz[2])))
        rows.append(dict(**item,actual=mat,first_xyz=xyz.round(4).tolist()if got else None,within_named_opening=within,passed=bool(correct and within)))
    return dict(asset_sha256=hashlib.sha256(asset.read_bytes()).hexdigest(),source_photo_sha256=known,
                count=len(rows),passed_rows=sum(q['passed'] for q in rows),passed=all(q['passed']for q in rows),readings=rows)
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('asset',type=Path);a.add_argument('output',type=Path)
    v=a.parse_args();o=inspect(v.asset);v.output.write_text(json.dumps(o,ensure_ascii=False,indent=1)+'\n')
    print(o['passed_rows'],o['count'],o['asset_sha256'])
    for r in o['readings']:
        if not r['passed']:print(r['view'],r['window'],r['uv'],r['actual'])
    raise SystemExit(int(not o['passed']))
