"""Test fixed pixels from the published courtyard views and independent passage sections."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys
from math import hypot

import numpy as np
from register_garden import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from southwest_colonnade import COPING,WALL,WHITE,TERRACE,WOOD,PANEL,STONE

SAMPLES={
    '4':[
        ('west round post',43,467,[WHITE],5),('east round post high',78,449,[WHITE],6),
        ('east round post low',66,506,[WHITE],7),
        ('door panel seen through arched passage',119,482,[WOOD,PANEL],4),
        ('second view through arch near lower panel',111,519,[WOOD,PANEL],5),
        ('near front reveal edge',99,494,[WHITE],7),
        ('rear cream return pier',166,490,[WHITE,WALL],5),
    ],
    '6':[
        ('western white post, above planting',78,536,[WHITE],5),
        ('inner white post, above rail',552,524,[WHITE],4),
        ('stained wood at upper left',213,503,[WOOD,PANEL],4),
        ('stained wood low on left',202,615,[WOOD,PANEL],4),
        ('continuous square door lintel',254,479,[WOOD],5),
        ('roughcast beside wood door',333,516,[WALL],4),
        ('west-facing arch band at far jamb',429,522,[WHITE],7),
        ('roughcast above arch',480,452,[WALL],6),
        ('upper threshold',290,657,[STONE,TERRACE],7),
        ('raised landing',410,651,[TERRACE],6),
    ]}


def inspect(path):
    reader=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=reader['SerialScene'](path)
    records=[]
    for number, rows in SAMPLES.items():
        cam=Camera(number)
        for label,x,y,materials,radius in rows:
            offsets=sorted((hypot(dx,dy),dx,dy) for dx in range(-radius,radius+1)
                           for dy in range(-radius,radius+1) if hypot(dx,dy)<=radius)
            first=None
            closest=None
            for ds,dx,dy in offsets:
                hit=scene.ray(cam.c,cam.ray((x+dx,y+dy)),90.)
                if ds==0:
                    first=hit
                if hit and hit['material'] in materials:
                    closest={'delta_px':[dx,dy],'radius_px':ds,'hit':hit}
                    break
            records.append(dict(view=number,detail=label,source_pixel=[x,y],material_options=materials,
                                first_hit=first,closest=closest))
    # Clip the transverse rays to the wall thickness. A jamb must be solid on both sides,
    # while the exact same X cross-section must be empty in the passage above/below spring.
    sections=[]
    for label,y,z,should_close in [('lower opening',-1.04,.75,False),('arched head',-1.04,2.06,False),
                                    ('shallow rear jamb',-.23,1.10,True),('wall over crown',-1.04,2.55,True)]:
        hit=scene.ray(np.array([-5.39,y,z]),np.array([1.,0.,0.]),.60)
        sections.append(dict(section=label,y=y,z=z,expect_solid=should_close,hit=hit,
                             accepted=bool(hit)==should_close))
    # The far edge of the soffit lies within the photo-plane residual of the textured
    # back wall. What the source establishes independently at this seam is opacity.
    seam=[]
    cam=Camera(6)
    for uv in [(140,416),(124,419),(201,420),(185,423)]:
        hit=scene.ray(cam.c,cam.ray(uv),65.)
        seam.append(dict(pixel=list(uv),hit=hit,accepted=hit is not None and hit['material'] in (WALL,COPING)))
    return {'west_soffit_interface':seam, 'asset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'file':path.name,
            'camera_sha256':hashlib.sha256((HERE/'garden-cameras.json').read_bytes()).hexdigest(),
            'source_controls_sha256':hashlib.sha256((HERE/'southwest-court-photo-controls.json').read_bytes()).hexdigest(),
            'rays':records,'exact_count':sum(r['first_hit'] is not None and r['first_hit']['material'] in r['material_options'] for r in records),
            'within_tolerance':sum(r['closest'] is not None for r in records),'total':len(records),'passage_sections':sections}


if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('input',type=Path);cli.add_argument('result',type=Path)
    args=cli.parse_args();result=inspect(args.input);args.result.parent.mkdir(exist_ok=True,parents=True)
    args.result.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(result['exact_count'],result['within_tolerance'],result['total'],sum(i['accepted'] for i in result['passage_sections']))
