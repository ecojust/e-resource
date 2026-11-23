"""First-hit checks on house 9 in the two original 650 by 487 photographs."""
import argparse
from hashlib import sha256
import json
from math import hypot
from pathlib import Path
import runpy
import sys

from register_court import Camera

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from no9_court import COPING, ENAMEL, IRON, LETTER, PIER, RENDER, SLAB

# Fixed observed image points. A thin iron bar can be narrower than a source pixel.
# The tolerance search reports the closest actual first hit independently of the central ray.
SAMPLES={
 20:[
 ('middle slab, left of divider',(233,281),SLAB,3),
 ('middle slab, clear centre',(368,260),SLAB,3),
 ('middle slab, right of pair of doors',(508,236),SLAB,3),
 ('middle slab, terminal nose',(588,229),SLAB,5),
 ('upper slab, left of divider',(180,157),SLAB,3),
 ('upper slab, right of divider',(325,97),SLAB,3),
 ('upper slab, halfway',(404,65),SLAB,3),
 ('upper slab, near terminal',(523,21),SLAB,3),
 ('middle handrail on cream wall',(450,185),IRON,3),
 ('middle clear iron upright',(447,213),IRON,3),
 ('middle lozenge centre bar',(463,211),IRON,3),
 ('middle clear right upright',(552,195),IRON,3),
 ('upper rail, part left of drain',(175,118),IRON,3),
 ('upper rail against first window',(197,109),IRON,3),
 ('pale foreground wall',(281,415),RENDER,3),
 ('foreground coping',(287,364),COPING,3),
 ('left gate pier',(115,408),PIER,3),
 ('left green enamel',(114,384),ENAMEL,2),
 ('digit on left plate',(121,385),LETTER,3),
 ('right narrow green plate',(612,380),ENAMEL,3)],
 19:[
 ('lower slab, inside shared bay',(12,358),SLAB,5),
 ('lower slab towards terminal',(43,355),SLAB,5),
 ('upper slab left of pier',(20,214),SLAB,5),
 ('upper slab towards its terminal',(55,208),SLAB,5),
 ('middle guard handrail',(24,312),IRON,5),
 ('upper guard handrail',(34,177),IRON,5)]}
def examine(path):
    helper=HERE.parents[3]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
    scene=runpy.run_path(str(helper))['SerialScene'](path)
    reports=[]
    for view,group in SAMPLES.items():
        camera=Camera(view)
        for label,uv,material,radius in group:
            offsets=sorted((hypot(dx,dy),dx,dy) for dx in range(-radius,radius+1)
                           for dy in range(-radius,radius+1) if hypot(dx,dy)<=radius)
            central=None
            nearest=None
            for distance,dx,dy in offsets:
                sample=(uv[0]+dx,uv[1]+dy)
                hit=scene.ray(camera.c,camera.ray(sample),90.)
                if distance==0:
                    central=hit
                if hit and hit['material']==material:
                    nearest={'offset_px':[dx,dy],'distance_px':distance,'hit':hit}
                    break
            reports.append(dict(view=view,detail=label,uv=uv,expected=material,radius_px=radius,
                                central_first_hit=central,nearest_matching_first_hit=nearest))
    return {'asset':path.name,'asset_sha256':sha256(path.read_bytes()).hexdigest(),
            'camera_sha256':sha256((HERE/'court-cameras.json').read_bytes()).hexdigest(),
            'controls_sha256':sha256((HERE/'no9-court-controls.json').read_bytes()).hexdigest(),
            'exact':sum(bool(r['central_first_hit'] and r['central_first_hit']['material']==r['expected']) for r in reports),
            'within_reading_radius':sum(r['nearest_matching_first_hit'] is not None for r in reports),
            'total':len(reports),'checks':reports}
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('input',type=Path);cli.add_argument('result',type=Path)
    args=cli.parse_args();result=examine(args.input)
    args.result.parent.mkdir(exist_ok=True,parents=True)
    args.result.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['exact'],result['within_reading_radius'],result['total'])
