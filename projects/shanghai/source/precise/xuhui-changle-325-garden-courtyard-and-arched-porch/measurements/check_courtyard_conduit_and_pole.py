"""Test the photographed wall bend and independent courtyard pole against delivered triangles."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys


def read(path):
    return json.loads(path.read_bytes())


def digest(path):
    with path.open('rb') as fd:
        return hashlib.file_digest(fd,'sha256').hexdigest()


p=argparse.ArgumentParser(description=__doc__)
p.add_argument('project',type=Path,help='Shanghai project root')
p.add_argument('mesh',type=Path)
p.add_argument('output',type=Path)
args=p.parse_args()
source=args.project/'source/precise/xuhui-changle-325-garden-courtyard-and-arched-porch'
measure=source/'measurements'
sys.path.insert(0,str(measure))
from register_court import Camera
scene=runpy.run_path(str(args.project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](args.mesh)
camera=Camera('fayhoo')
conduit=measure/'wall-conduit-observations.json'
pole=measure/'courtyard-pole-observations.json'
controls={'conduit':read(conduit)['independent_controls'], 'pole':read(pole)['fayhoo']['material_check_pixels']}
materials={'dark_ring':'dark opening around the sleeve','pale_sleeve':'pale connector sleeve',
           'exposed_bend':'weathered pale wall tubing','visible_soffit_run':'weathered pale wall tubing',
           'occlusion_check':'weathered grey courtyard shaft','shaft':'weathered grey courtyard shaft',
           'plinth':'dark faceted pole footing','binding':'ochre brown pole binding'}
rows={}
for group,features in controls.items():
    hits=[]
    for feature,pixels in features.items():
        for pixel in pixels:
            first=scene.ray(camera.c,camera.ray(pixel),80)
            expected='325 garden | '+materials[feature]
            hits.append({'feature':feature,'original_pixel':pixel,'expected':expected,'observed':first,
                         'exact':bool(first and first['material']==expected)})
    rows[group]={'count':len(hits),'exact_first_hits':sum(v['exact'] for v in hits),'samples':hits}
body={'coordinate_system':'Fayhoo original 2037 × 1358, upper-left pixel centre is (0,0). Rays use the full delivered triangle mesh.',
      'mesh_sha256':digest(args.mesh),'conduit_source_sha256':digest(source/'source/porch_conduit.py'),
      'conduit_observations_sha256':digest(conduit),'pole_observations_sha256':digest(pole),'results':rows}
args.output.write_text(json.dumps(body,ensure_ascii=False,indent=2)+'\n')
print(args.mesh.name,[(k,v['exact_first_hits'],v['count']) for k,v in rows.items()])
