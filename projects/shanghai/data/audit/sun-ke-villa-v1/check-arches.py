"""Ray-test the three open garden arches, glazed upper bays and the drive-through north portico."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

AUDIT = Path(__file__).resolve().parent
PROJECT = AUDIT.parents[2]
RAY = PROJECT / 'source/precise/huangpu-wing-on-skybridges/source/check_bridge.py'
spec = importlib.util.spec_from_file_location('ray', RAY)
ray = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ray)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--work',type=Path,required=True,help='Working directory from verify-placement.py')
parser.add_argument('--report',type=Path,default=AUDIT/'opening-rays.json')
args=parser.parse_args()
source=json.loads((args.work/'delivered-decode.json').read_bytes())
rows=[]
for rec in source:
    tri=np.fromfile(rec['triangle_file'],np.float64).reshape(-1,3,3)
    materials=np.fromfile(rec['triangle_material_ids_file'],np.uint16)
    names=rec['material_names']
    results=[]
    samples=[('south','garden arch '+str(i+1),u+.19,1.67,-5.25,-4.55)for i,u in enumerate((-2.835,-.365,2.105))]
    samples += [('south','masonry pier',-1.59,1.33,-7.13,-7.06),
               ('north','north drive opening',-.10,1.70,5.15,5.90),
               ('north','north outer pier',-2.12,1.40,8.90,9.55)]
    samples += [('south','upper glazed opening '+str(i+1),-.365+u+.19,4.82,-7.03,-6.70)
                for i,u in enumerate((-2.72,-.91,.91,2.72))]
    for side,label,x,height,low,high in samples:
        oriented=tri.copy()
        if side=='south':oriented[:,:,2]*=-1
        material,z=ray.face_hit(oriented,materials,names,x,height)
        y=z if side=='south' else -z
        assert low <= y <= high,(rec['variant'],label,x,material,y)
        if label.startswith('upper glazed'):assert material=='blue grey glazing',(label,material)
        if 'pier' in label:assert material=='warm ochre render'
        results.append({'side':side,'feature':label,'x':x,'height_m':height,'first_y_m':y,'material':material})
    rows.append({'variant':rec['variant'],'sha256':rec['sha256'],'rays':results})
result={'model_id':'changning-sun-ke-villa','script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'ray_math_sha256':hashlib.sha256(RAY.read_bytes()).hexdigest(),'variants':rows,
        'meaning':'Rays pass through the three garden openings to an interior wall more than 1.8 m behind the front, through the north porte-cochere to the main entrance, and hit glazing or masonry at the neighboring controls.'}
args.report.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
print('Checked',sum(len(r['rays']) for r in rows),'rays in three decoded issued models.')
