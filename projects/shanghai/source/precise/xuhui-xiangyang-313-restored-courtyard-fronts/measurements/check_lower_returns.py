"""Intersect left return glazing, open louvres, cropped east shutter and visible tap."""
import argparse
import json
import numpy as np
from pathlib import Path
from check_large_window import SerialScene
from register_courtyard import Camera
from plan_points import load

PICKS=[
    ('visible left return pane',(375,308),('glass','joinery')),
    ('visible left return pane beside hinges',(384,303),('glass','joinery')),
    ('hinged shutter frame',(391,300),('joinery',)),
    ('dark behind slats of open shutter',(397,313),('shaded inside reveal','shutter blades')),
    ('outer blade of open shutter',(402,316),('shutter blades','joinery')),
    ('cropped opposite shutter',(578,300),('shaded inside reveal','shutter blades','joinery')),
    ('short tap near entrance jamb',(541,295),('weathered metal hardware',)),
    ('service tap cross pipe',(555,298),('weathered metal hardware',)),
    ('upturned end of tap',(565,299),('weathered metal hardware',)),
]
def examine(path):
    scene=SerialScene(path);cam=Camera('case1')
    t=np.asarray(load()['facade_frames']['case1']['local_to_ENU']);eye=(t@[*cam.c,1])[:3]
    rows=[]
    for label,pixel,materials in PICKS:
        hit=scene.ray(eye,t[:3,:3]@cam.ray(pixel),45)
        rows.append({'label':label,'pixel':pixel,'first_hit':hit,'expected':materials,
                     'direct':bool(hit and any(s in hit['material'] for s in materials))})
    return {'asset':scene.asset,'count':len(rows),'direct':sum(r['direct'] for r in rows),'probes':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('model',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();r=examine(a.model);a.output.write_text(json.dumps(r,indent=2)+'\n');print(r['direct'],r['count'])
