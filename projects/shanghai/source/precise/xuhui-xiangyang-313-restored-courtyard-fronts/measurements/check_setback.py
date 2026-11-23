"""Independently picked source pixels of the receding front, traced into the serialized GLB."""
from pathlib import Path
import argparse
import json
import numpy as np
from check_large_window import SerialScene
from register_courtyard import Camera
from plan_points import load

PICKS=[
    ('cream over balcony',(261,106),('pale courtyard render',)),
    ('cream between eastern windows',(309,113),('pale courtyard render',)),
    ('violet hood, upper left',(111,21),('blue violet fabric',)),
    ('violet hood, side of upper left',(148,25),('blue violet fabric',)),
    ('top border cyan sheet',(216,3),('translucent cyan canopy',)),
    ('top border cyan sheet, eastern end',(324,3),('translucent cyan canopy',)),
    ('upper middle transom, left light',(207,41),('glass',)),
    ('upper middle transom, right light',(232,41),('glass',)),
    ('upper middle shadow in left opening',(209,58),('shaded inside reveal',)),
    ('upper right glass above rail',(301,38),('glass',)),
    ('upper right glass above rail, right light',(324,39),('glass',)),
    ('upper right metal rail',(314,73),('service window railing','weathered metal hardware')),
    ('small fabric hood',(301,131),('blue violet fabric',)),
    ('middle right window first left pane',(292,151),('glass',)),
    ('middle right window first right pane',(317,151),('glass',)),
    ('middle right window left pane near sill',(293,195),('glass',)),
    ('middle right window right pane near sill',(318,195),('glass',)),
    ('middle right window sill',(328,205),('pale projecting sill',)),
    ('central bottom window two transom lights',(186,307),('glass',)),
    ('ground window right side of transom',(212,307),('glass',)),
    ('ground window lower central post',(199,343),('dark painted window joinery',)),
    ('window beside balcony awning, shaded left field',(111,159),('shaded inside reveal',)),
    ('left balcony door open reflected leaf',(87,165),('door reflection','dark painted window joinery')),
    ('right balcony door lower reflected glazing',(204,169),('door reflection','dark painted window joinery')),
]
def inspect(path,local):
    model=SerialScene(path);cam=Camera('case1')
    pose=np.eye(4) if local else np.asarray(load()['facade_frames']['case1']['local_to_ENU'])
    eye=(pose@[*cam.c,1])[:3]
    rows=[]
    for label,uv,mats in PICKS:
        ray=pose[:3,:3]@cam.ray(uv);hit=model.ray(eye,ray,60)
        rows.append(dict(label=label,pixel=uv,expected_material=mats,hit=hit,
                         direct=bool(hit and any(s in hit['material']for s in mats))))
    return {'asset':model.asset,'count':len(rows),'direct':sum(r['direct']for r in rows),'readings':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);p.add_argument('--local',action='store_true')
    a=p.parse_args();r=inspect(a.mesh,a.local);a.out.write_text(json.dumps(r,indent=2)+'\n')
    print(r['direct'],r['count'],[(h['label'],h['hit']['material']if h['hit']else None)for h in r['readings']if not h['direct']])
