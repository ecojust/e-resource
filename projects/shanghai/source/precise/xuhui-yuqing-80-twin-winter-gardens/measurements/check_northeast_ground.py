"""Read the original photograph pixels as rays into the delivered, fully decoded triangles."""
import argparse
import hashlib
import json
from math import hypot
from pathlib import Path
import runpy
import sys
import numpy as np
from register_garden import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from central_front import PLASTER, COPING, FRAME, GLASS, PANEL, TERRACE, RAILING

# Stored as measured pixels, independent of any model mesh projection.
SAMPLES={
 4:[('leftmost sliver, upper steel leaf',550,473,[FRAME,GLASS]),
    ('first cream pier',560,498,[PLASTER]),
    ('second light, left pane',581,474,[GLASS]),
    ('second light, right pane',606,475,[GLASS]),
    ('second light, centre stile',595,470,[FRAME]),
    ('second intervening pier',630,476,[PLASTER]),
    ('third light, top left',658,441,[GLASS]),('third light upper right',706,474,[GLASS]),
    ('third meeting stile',684,474,[FRAME]),('third lower left',663,503,[GLASS]),
    ('third opaque low panel',659,582,[PANEL]),('third-to-fourth pier',737,498,[PLASTER]),
    ('fourth light, upper left',769,474,[GLASS]),('fourth light, right pane',812,509,[GLASS]),
    ('fourth opaque panel',780,586,[PANEL]),('fourth-to-fifth pier',841,486,[PLASTER]),
    ('fifth light, central glass',878,478,[GLASS]),('east curved reveal',899,482,[PLASTER]),
    ('cream wall above the five windows',685,414,[PLASTER]),
    ('foreground coping',786,616,[COPING]),
    ('retaining face below curved end',902,644,[PLASTER]),
    ('foreground upper rail',689,549,[RAILING])],
 6:[('western glass chord, top left',752,496,[GLASS]),('western glass chord, right pane',777,511,[GLASS]),
    ('westernmost opaque lower panel',767,554,[PANEL]),
    ('first cream intervening pier',795,512,[PLASTER]),
    ('middle aperture left pane',811,500,[GLASS]),('middle aperture right pane',827,509,[GLASS]),
    ('next cream pier',844,500,[PLASTER]),('third foreshortened glass bay',854,501,[GLASS]),
    ('wall below overhang above middle window',821,463,[PLASTER])]
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def inspect(path):
    reader=runpy.run_path(str(HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))
    scene=reader['SerialScene'](path);result=[]
    for number,rows in SAMPLES.items():
        cam=Camera(number)
        for label,x,y,expected in rows:
            first=scene.ray(cam.c,cam.ray((x,y)),90.)
            found=None
            # Window/rail edges are much smaller than the global camera residuals.
            for d,dx,dy in sorted((hypot(u,v),u,v) for u in range(-5,6) for v in range(-5,6) if hypot(u,v)<=5):
                hit=first if d==0 else scene.ray(cam.c,cam.ray((x+dx,y+dy)),90.)
                if hit and hit['material'] in expected:
                    found={'offset_px':[dx,dy],'distance_px':d,'hit':hit};break
            result.append({'view':number,'feature':label,'source_pixel':[x,y],'expected':expected,'first_hit':first,'nearest_within_5_px':found})
    return {'file':path.name,'file_sha256':digest(path),'control_sha256':digest(HERE/'northeast-ground-controls.json'),
            'camera_sha256':digest(HERE/'garden-cameras.json'),'rays':result,
            'exact':sum(r['first_hit'] is not None and r['first_hit']['material'] in r['expected'] for r in result),
            'within_5_working_pixels':sum(bool(r['nearest_within_5_px']) for r in result),'total':len(result)}

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mesh',type=Path);ap.add_argument('report',type=Path);a=ap.parse_args()
    d=inspect(a.mesh);a.report.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n');print(d['exact'],d['within_5_working_pixels'],d['total'])
