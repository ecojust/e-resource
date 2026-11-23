"""Trace the twenty photographed lights and five separate visible objects at full source resolution."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from register_courtyard import Camera
HERE=Path(__file__).resolve().parent
helper=HERE.parents[1]/'xuhui-hujiang-villas-changle-passage-bay/measurements/city-contact/glb_triangles.py'
SerialScene=runpy.run_path(str(helper))['SerialScene']
# Independent native-image picks. Rows follow the oblique projecting sill.
CENTRES=[
 [(424,120),(448,119),(471,119),(500,117)],
 [(425,132),(449,131),(474,130),(503,131)],
 [(427,145),(451,144),(477,144),(504,143)],
 [(429,157),(454,157),(478,156),(505,156)],
 [(430,170),(455,171),(481,169),(508,169)],
]
DETAIL=[('light sill',(468,181),('pale projecting sill',)),
        ('circular condenser face',(388,151),('weathered metal hardware','shaded inside reveal')),
        ('pale condenser case',(407,147),('pale enamel condenser',)),
        ('lower hood',(482,273),('blue edged shallow hood',)),
        ('lower shutter',(492,310),('dark shutter blades','shaded inside reveal','dark painted window joinery'))]
def examine(mesh):
    model=SerialScene(mesh);cam=Camera('case1')
    readings=[(f'leaf {col+1}, row {j+1}',uv,('reflected glass','blue grey glass')) for j,row in enumerate(CENTRES)for col,uv in enumerate(row)]
    readings+=DETAIL
    result=[]
    for label,uv,types in readings:
        hit=model.ray(cam.c,cam.ray(uv),45.)
        result.append({'label':label,'source_pixel':uv,'first_hit':hit,
                       'correct_direct_hit':bool(hit and any(s in hit['material']for s in types))})
    return {'asset':model.asset,'camera_sha256':hashlib.sha256((HERE/'courtyard-cameras.json').read_bytes()).hexdigest(),
            'count':len(readings),'exact':sum(v['correct_direct_hit']for v in result),'rays':result}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path)
    a=cli.parse_args();r=examine(a.mesh);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(r['exact'],r['count'],[(h['label'],h['first_hit']['material'] if h['first_hit']else None)for h in r['rays'] if not h['correct_direct_hit']])
