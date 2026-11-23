"""Reproject identifiable forecourt details and test the actual first surface of each public view."""
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
from court_three import CAP, CAST, CHARCOAL, CREAM, ENAMEL, GLASS, GREEN, LETTER, SEAM
from court_terrace import BLUE, EYE, IRON, RIGHT, SLAB, TOP, Terrace
from build_model import FRONT_Y, WALL_Y
from court_frontage import CLAY


def samples():
    terrace = Terrace(None, FRONT_Y, WALL_Y, False)
    def rail(x, depth, z):
        return terrace.point(x, depth, z)
    def window(x, y, z):
        t = (WALL_Y + y - EYE[1]) / (.70 - EYE[1])
        return (EYE[0] + (x-EYE[0])*t, WALL_Y+y, EYE[2] + (z-EYE[2])*t)

    plaque = ('green enamel plate', (.10, -.009, 2.36), ENAMEL)
    cap = ('overhanging coping', (.16, -.091, 2.62), CAP)
    door = ('dark metal gate', (.65, .085, 1.68), CHARCOAL)
    letter = ('painted numeral 3', (.0493, -.0102, 2.3929), LETTER)
    beam = ('outer face of terrace beam', rail(-.33, 0, 3.228), SLAB)
    beam_under = ('underside of deck', rail(.31,.32,3.155), SLAB)
    front_rail = ('long iron handrail', rail(.4,0,TOP), IRON)
    end_rail = ('short return handrail', rail(RIGHT,.39,TOP), IRON)
    blue = ('blue sheet behind grille', rail(.145,.024,3.598), BLUE)
    pane = ('upper window pane', window(.306,.046,4.915), GLASS)
    stile = ('green centre stile', window(.108,.028,4.915), GREEN)
    corner = ('left window surround', window(-.446,-.044,5.053), CREAM)
    dentil = ('third dentil', window(-.499+2*1.049/19+.013,-.075,5.359), CREAM)
    band = ('projecting head band', window(.20,-.0905,5.416), CREAM)
    return {'overview':[plaque,beam,pane,('green head behind the court gate',(-1.07,WALL_Y+.035,2.82),GREEN)], 'original':[door,front_rail,pane],
            'number':[plaque,letter,cap,('terracotta lug below the plate',(.05,-.030,2.15),CLAY)], 'gate':[door,('vertical folded seam',(.919,.078,1.51),SEAM),('rendered pier',(-.119,0,1.8),CAST)],
            'terrace':[beam,blue,front_rail], 'ironwork':[front_rail,end_rail,blue],
            'green-sash':[pane,stile,corner], 'underside':[beam,beam_under,cap],
            'dentils':[dentil,band,('lower head fillet',window(.11,-.0625,5.315),CREAM)]}


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
            tolerance=.035 if material==IRON else .008
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
