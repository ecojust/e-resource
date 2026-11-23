"""Project the measured 2015 facade and roof anchors into all nine public views and compare actual first intersections on each model. """
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / 'source'
sys.path[:0] = [str(SOURCE), str(HERE.parents[1] / 'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
def samples():
    register=json.loads((HERE/'public-camera-controls.json').read_bytes())
    controls=register['independent_anchors']
    views={
        'overview':['white diamond upper stroke','west middle sash','balcony pale edge 2'],
        'street':['key','stair pane 2','middle broad ground sash','east enamel'],
        'entrance':['key','west enamel','upper transom'],
        'stair':['stair pane 1','stair pane 2','stair pane 3','white diamond upper stroke'],
        'balconies':['balcony handrail 1','balcony pale edge 1','balcony handrail 2','balcony pale edge 2'],
        'left-bay':['west lower west glazing','west middle sash','west lower left sill'],
        'folded-bay':['middle broad ground sash','middle angled ground sash','middle broad sill'],
        'roof':register.get('roof_controls',[]),
        'lane':['east enamel','end lower pane','end head']}
    return {name:[(k,controls[k]['xyz'],controls[k]['expected']) for k in keys] for name,keys in views.items()}


def image_fraction(camera, eye, point):
    forward = np.asarray(camera['target']) - eye
    distance = np.linalg.norm(forward)
    forward /= distance
    right = np.cross(forward,[0,0,1])
    right /= np.linalg.norm(right)
    down = np.cross(forward,right)
    delta = point-eye
    depth = float(delta @ forward)
    focal = camera['width']*distance/camera['width_m']
    return [round(.5+float(delta@right)*focal/(camera['width']*depth),6),
            round(.5+float(delta@down)*focal/(camera['height']*depth),6)]


def inspect(mesh,camera_file):
    scene=SerialScene(mesh);cameras=json.loads(camera_file.read_bytes());features=samples();rows=[]
    assert {c['name'] for c in cameras}==set(features)
    for camera in cameras:
        eye=np.asarray(camera['eye'],dtype=float)
        for label,xyz,material in features[camera['name']]:
            point=np.asarray(xyz,dtype=float);uv=image_fraction(camera,eye,point)
            hit=scene.ray(eye,point-eye,50)
            separation=float(np.linalg.norm(np.asarray(hit['point_enu_m'])-point)) if hit else None
            tolerance=.035
            passed=bool(hit and hit['material']==material and separation<=tolerance and all(0<v<1 for v in uv))
            rows.append(dict(camera=camera['name'],feature=label,world_m=point.tolist(),image_fraction=uv,
                             expected=material,first_hit=hit,separation_m=separation,tolerance_m=tolerance,passed=passed))
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(mesh=mesh.name,sha256=sha(mesh),cameras_sha256=sha(camera_file),count=len(rows),
                matched=sum(r['passed'] for r in rows),rays=rows)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--cameras',type=Path,default=SOURCE/'cameras.json')
    args=parser.parse_args();result=inspect(args.mesh,args.cameras)
    args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(result['matched'],result['count'])
    for r in result['rays']:
        if not r['passed']: print(r['camera'],r['feature'],r['image_fraction'],(r['first_hit'] or {}).get('material'))
