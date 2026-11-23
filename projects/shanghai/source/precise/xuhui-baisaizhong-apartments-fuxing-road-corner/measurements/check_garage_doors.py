"""Bounded photo-plane and first-hit tests for the optional Route Magy garage leaf group."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from garage1930s import BAYS,BOTTOM,HEAD,wing_basis
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact'))
from glb_triangles import SerialScene
# On a scan reduced from 4558 to exactly 1000 pixels wide. In bay one the
# unobserved bank is excluded; its vanishing/hinge location cannot calibrate a
# plane. Upper/lower right refer to the exposed edge of the off-centre gap.
REGIONS={
 'near visible bank': ([(675,145),(766,150),(766,337),(676,347)],(BAYS[0][0], BAYS[0][0]+.58*(BAYS[0][1]-BAYS[0][0]))),
 'far opening': ([(825,155),(937,165),(933,315),(825,333)],BAYS[1])}
# Samples intrinsic to the scan. The left jamb of the far leaf is behind a pole.
SAMPLES={
 'near visible bank': [(693,212,'boarding'),(713,230,'boarding'),(744,238,'boarding'),
                     (739,256,'boarding'),(689,170,'rail'),(742,192,'rail'),
                     (738,165,'shadow'),(724,230,'stiles')],
 'far opening': [(835,242,'boarding'),(864,233,'boarding'),(874,261,'boarding'),
                 (898,243,'boarding'),(918,234,'boarding'),(915,278,'boarding'),
                 (881,208,'rail'),(901,194,'rail'),(908,174,'shadow'),
                 (925,175,'rail'),(880,274,'stiles')]}
def affine_quad(px,world):
    rows=[]; q=[]
    for (u,v),(s,z) in zip(px,world):
        rows.extend([[u,v,1,0,0,0,-u*s,-v*s],[0,0,0,u,v,1,-u*z,-v*z]])
        q.extend([s,z])
    return np.r_[np.linalg.solve(rows,q),1].reshape(3,3)
def inspect(mesh,main=None):
    garage=SerialScene(mesh);scene=SerialScene(main) if main else None
    a,u,n=wing_basis(); results={}
    for key,(uv,(s0,s1)) in REGIONS.items():
        H=affine_quad(uv,[(s0,HEAD),(s1,HEAD),(s1,BOTTOM),(s0,BOTTOM)])
        rows=[]
        for px,py,want in SAMPLES[key]:
            x=H@[px,py,1];s,z=x[:2]/x[2];xy=a+u*s+n*3
            origin=[*xy,z]; ray=[*-n,0.]
            g=garage.ray(origin,ray,12);m=scene.ray(origin,ray,12) if scene else None
            visible=bool(g and (not m or g['distance_m']<m['distance_m']))
            rows.append({'scan_at_1000px':[px,py],'scan_native_4558px':np.round([px*4.558,py*4.558],1).tolist(),
                         'wall_sz_m':[round(s,5),round(z,5)],'expected_contains':want,
                         'historic_hit':g,'modern_first_hit':m,'nearer_than_modern':visible,
                         'material_match':bool(g and want in g['material'] and visible)})
        results[key]={'source_quad_at_1000px':uv,'scan_to_wall_sz':H.tolist(),'samples':rows,
                      'exact_visible_material_matches':sum(i['material_match'] for i in rows),
                      'count':len(rows),'historic_face_first':sum(i['nearer_than_modern'] for i in rows)}
    return {'garage_mesh':garage.asset,'contemporary_mesh':scene.asset if scene else None,
            'method':'Two local planar rectifications in the Forman photograph; shoot along the surveyed street normal. The street pole, parked vehicle, and person are excluded. For the contemporary control compare depths on the identical ray.',
            'stations':results}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('garage',type=Path);p.add_argument('output',type=Path);p.add_argument('--modern',type=Path);a=p.parse_args()
    result=inspect(a.garage,a.modern);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for key,t in result['stations'].items(): print(key,t['exact_visible_material_matches'],t['count'],t['historic_face_first'],[(v['scan_at_1000px'],v['historic_hit']['material'] if v['historic_hit'] else None) for v in t['samples'] if not v['material_match']])
