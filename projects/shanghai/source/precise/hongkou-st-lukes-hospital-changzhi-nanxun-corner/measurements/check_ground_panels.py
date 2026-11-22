"""Measure the blind panels, surrounding wall and fascia blocks on each serialized model."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / 'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene

def check(path):
    layout = json.loads((HERE.parent/'source/street-layout.json').read_bytes())
    data = json.loads((HERE/'nanxun-lower-storeys-and-dated-panels.json').read_bytes())
    dimensions = data['model_registration']
    face = next(f for f in layout['faces'] if f['id']=='nanxun')
    along = (np.array(face['b'])-face['a'])/face['length']
    normal = np.array(face['out'])
    def point(s, z, outward):
        xy = face['a'] + along*s + normal*outward
        return np.r_[xy,z]
    measured = []
    scene = SerialScene(path)
    def ray(feature, origin, expected):
        surface = scene.ray(origin, expected-origin, 25.)
        hit = np.array(surface['point_enu_m']) if surface else None
        error = float(np.linalg.norm(hit-expected)) if hit is not None else None
        measured.append(dict(feature=feature, origin=origin.round(5).tolist(),
                             target=expected.round(5).tolist(), actual=hit.round(6).tolist() if hit is not None else None,
                             material=surface['material'] if surface else None, error_m=error,
                             matched=error is not None and error<.002))
    for i,(left,right) in enumerate(dimensions['model_along_extents_m'],1):
        width = right-left
        for t,z in ((.22,.43), (.79,.52), (.50,1.31), (.19,2.18), (.78,2.25)):
            s = left+width*t
            # The original fifth point in bay two falls on the right-hand hanging
            # block already resolved in the 2023 district view. Retain that point.
            under_drop = i == 2 and t == .78
            depth = .068 if under_drop else -.068
            feature = 'district third fascia block' if under_drop else f'blind plaster back {i}'
            ray(feature, point(s,z,.7), point(s,z,depth))
        if i == 2:
            s = left + .61*width
            ray('blind plaster between the two drops', point(s,2.25,.7), point(s,2.25,-.068))
        for edge,other in ((left,.55),(right,-.55)):
            ray(f'wall cheek {i}', point(edge+other,1.25,.68), point(edge,1.25,-.032))
        for edge,sign in ((left,-1),(right,1)):
            s = edge + sign*.045
            ray(f'solid surround {i}',point(s,1.31,.65),point(s,1.31,0.))
        top = layout['low_fascia']-.142
        mid=left+.38*width
        ray(f'upper return {i}',point(mid,top-.43,.65),point(mid,top,-.035))
    for group,depth in ((dimensions['existing_first_three_pendants'],.068),
                        (dimensions['last_three_pendants_estimated_s_width_drop_below_fascia_m'],.056)):
        for s,width,drop in group:
            z=layout['low_fascia']-.10-(drop-.10)*.66
            ray('fascia drop',point(s,z,.7),point(s,z,depth))
    return dict(asset_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),observations=measured,
                total=len(measured),hits=sum(p['matched'] for p in measured))
if __name__=='__main__':
    path,output=map(Path,sys.argv[1:]);report=check(path)
    temp=output.with_suffix('.new');temp.write_text(json.dumps(report,ensure_ascii=False,indent=1)+'\n');temp.replace(output)
    print(path,report['hits'],report['total'])
    if report['hits']!=report['total']:
        print([(s['feature'],s['material'],s['actual'],s['target']) for s in report['observations'] if not s['matched']])
        raise SystemExit(1)
