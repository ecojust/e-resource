"""Check projected image coordinates and the first visible surface at each page camera."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'source'
sys.path[:0]=[str(SOURCE),str(HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact')]
from glb_triangles import SerialScene
from build_model import SCALE
import street_materials as m
from roof_lattice import CAP, LATTICE, levels, height, plan, RAFTERS, rafter_points


def stem(index):
    u,d,tip,base=rafter_points(RAFTERS[index])
    return (u,d*.55,.55*tip+.45*base-.025)


def features():
    return {
        'overview':[('central entrance leaf',(.05,-.095,1.46),m.GREEN),('stair yellow pier',(-1.03,0.,7.93),m.YELLOW),
                    ('second folded bay lintel',(-3.75,-.6,9.55),m.SOLDIER)],
        'four-bays':[(f'folded front {i}',(x,y,9.55),m.SOLDIER) for i,(x,y) in enumerate([(-7.6,-.57),(-3.75,-.60),(3.22,-.62),(8.56,-.65)],1)],
        'folded-bay':[('upper front spandrel',(3.30,-.62,9.72),m.SOLDIER),('central lower pane',(3.10,-.55,8.59),m.GLASS),
                      ('right return sill panel',(4.23,-.40,6.92),m.CREAM)],
        'brickwork':[('ochre field',(1.23,0,5.80),m.YELLOW),('red return',(2.00,-.31,7.19),m.SOLDIER),
                     ('relief on front bay',(3.25,-.62,6.92),m.CREAM)],
        'entrance':[('green door',(.03,-.10,1.0),m.GREEN),('entry left jamb',(-.66,-.13,1.5),m.LIME),
                    ('stepped head',(-.61,-.14,3.53),m.CREAM)],
        'stair-panels':[('left cast stair panel',(-.5,-.064,8.79),m.CREAM),('right cast stair panel',(.22,-.064,8.79),m.CREAM),
                       ('upper dark glazed stair light',(.31,.11,10.58),m.GLASS)],
        'lattice':[('broad dark glass',(plan(1440),.079,height(180)),m.GLASS),
                   ('double arch crest',(plan(1434),-.006,height(levels(1454)[0])),LATTICE),
                   ('right diagonal crossing',(plan(1513),-.006,height(levels(1454)[1]+18.5)),LATTICE)],
        'rafters':[('rafter near right of stair head',stem(8),CAP),('rafter at second single attic light',stem(10),CAP),
                  ('first glazed side panel',(plan(1173),.079,height(175)),m.GLASS)],
        'south-roof':[(f'south window {i+1}',(-11.35,(d+.11)/SCALE[1],(lo+.22*(hi-lo))/SCALE[2]),m.SHADE if i==3 else m.GLASS)
                      for i,(d,lo,hi) in enumerate([(1.11,4.04,5.30),(1.12,7.47,8.58),(1.04,10.76,11.90),(4.25,11.48,12.02),(4.29,13.50,14.55)])]
                     +[('short upper roof',(-8.9,2.50,15.09),m.STONE)],
    }


def projected(c,xyz):
    eye=np.array(c['eye']);direction=np.array(c['target'])-eye;distance=np.linalg.norm(direction)
    direction/=distance;right=np.cross(direction,[0.,0.,1.]);right/=np.linalg.norm(right);down=np.cross(direction,right)
    delta=xyz-eye;depth=float(delta@direction);f=c['width']*distance/c['width_m']
    return [round(.5+(delta@right)*f/(c['width']*depth),5),round(.5+(delta@down)*f/(c['height']*depth),5)]


def inspect(mesh,cameras):
    rows=[];scene=SerialScene(mesh);cams=json.loads(cameras.read_bytes());tests=features()
    assert {c['name']for c in cams}==set(tests)
    for c in cams:
        for label,pt,target in tests[c['name']]:
            xyz=np.asarray(pt)*SCALE;eye=np.array(c['eye'])
            uv=projected(c,xyz);hit=scene.ray(eye,xyz-eye,110)
            rows.append(dict(pose=c['name'],feature=label,world_m=xyz.tolist(),image_fraction=uv,expected=target,first_hit=hit,
                             matches=bool(all(0<x<1 for x in uv) and hit and hit['material']==target)))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    return dict(mesh=mesh.name,sha256=digest(mesh),cameras_sha256=digest(cameras),count=len(rows),matched=sum(r['matches']for r in rows),rays=rows)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--cameras',type=Path,default=SOURCE/'cameras.json');a=p.parse_args()
    r=inspect(a.mesh,a.cameras);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['matched'],r['count'])
    for x in r['rays']:
        if not x['matches']:print(x['pose'],x['feature'],x['image_fraction'],x['first_hit']and x['first_hit']['material'])
