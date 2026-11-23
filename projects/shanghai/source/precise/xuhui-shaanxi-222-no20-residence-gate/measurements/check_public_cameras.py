"""Reproject the enamel address, entrance, bronze hardware and moulded cornice and test the actual first surface of each public view."""
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
from residence_gate import WALL, SHAFT, DARK, PANEL
from gate_frieze import DEFAULT, STONE, EDGE, RELIEF
from gate_hardware import ENAMEL, PAINT, GREY, ALLOY, RIDGE, HOLLOW

def samples():
    door=('left door leaf',(-.39,.12,1.23),DARK)
    plate=('green enamel left of numerals',(-.110,-.004,2.47),ENAMEL)
    zero=('left stroke of numeral zero',(.014,-.0047,2.467),PAINT)
    pier=('right pier shaft',(1.34,-.077,2.50),SHAFT)
    panel=('recessed head of entrance',(.13,.043,3.055),PANEL)
    shoulder=('right shoulder band',(1.28,-.138,2.755),SHAFT)
    head=('left head relief',(-1.10,-.248,3.57),RELIEF)
    centre=('middle cornice cove',(-.14,-.263,3.71),STONE)
    cap=('top cornice rim',(.74,-.32,3.985),EDGE)
    coil_left=('left pull lower arc',(-.14339,.079,.910),RIDGE)
    coil_right=('right pull lower arc',(.17056,.079,.912),RIDGE)
    box=('dark call button',(.958,-.025,.936),HOLLOW)
    jamb=('opening right side',(1.002,0,1.62),WALL)
    return {'overview':[door,pier,plate], 'front':[door,panel,plate],
            'number':[plate,zero], 'knockers':[coil_left,coil_right],
            'hardware':[coil_right,box], 'opening':[door,plate,jamb],
            'pier':[pier,shoulder], 'frieze':[centre,cap], 'cornice':[head,centre,cap]}

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
            tolerance=.025 if material in (RIDGE,STONE,EDGE,RELIEF) else .008
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
