"""Test actual face hits through the stepped courtyard wall in the three issued meshes."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np

AUDIT=Path(__file__).resolve().parent
HELPER=AUDIT.parents[2]/'source/precise/huangpu-wing-on-skybridges/source/check_bridge.py'
spec=importlib.util.spec_from_file_location('rays',HELPER)
rays=importlib.util.module_from_spec(spec)
spec.loader.exec_module(rays)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

# Courtyardward distances are negative. Glazing sits behind actual cut edges.
SAMPLES=[
    ('main door light',-1.35,2.30,'smoky blue grey glazing',.88,.93),
    ('main door timber',-.98,1.45,'dark red joinery',.88,.93),
    ('east upper casement 1',-7.78,4.72,'smoky blue grey glazing',.31,.36),
    ('east upper casement 2',-6.64,4.72,'smoky blue grey glazing',.31,.36),
    ('east upper casement 3',-5.51,4.72,'smoky blue grey glazing',.31,.36),
    ('spiral mullion core',-7.185,4.82,'cool cut lintel stone',-.12,-.06),
    ('glazing over entrance',-1.37,4.4,'smoky blue grey glazing',.83,.87),
    ('central French window',3.05,5.27,'smoky blue grey glazing',.20,.24),
    ('west upper casement',7.85,4.57,'smoky blue grey glazing',.94,.98),
    ('masonry beside east windows',-3.57,4.50,'aged warm white stucco',.0,.04),
    ('bowed balcony handrail',3.125,4.056,'forged balcony and grilles',-1.18,-1.13),
    ('cantilevered balcony slab',3.125,2.99,'cool cut lintel stone',-1.15,-1.09),
    ('barrel-tile entry hood',-1.36,3.18,'curved clay tile rolls',-.75,-.50),
    ('entrance step',-1.35,.21,'grey entrance flags',-.47,-.40),
]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work',required=True,type=Path,help='Working directory retained with verify-placement.py --work')
    parser.add_argument('--report',type=Path,default=AUDIT/'opening-rays.json')
    args=parser.parse_args()
    results=[]
    for variant in json.loads((args.work/'delivered-decode.json').read_bytes()):
        faces=np.fromfile(variant['triangle_file'],np.float64).reshape(-1,3,3)
        faces[:,:,2]*=-1
        mat=np.fromfile(variant['triangle_material_ids_file'],np.uint16)
        names=variant['material_names']
        records=[]
        for label,x,z,wanted,lo,hi in SAMPLES:
            material,y=rays.face_hit(faces,mat,names,x,z)
            assert material==wanted and lo<=y<=hi,(variant['variant'],label,material,y)
            records.append({'feature':label,'x_m':x,'z_m':z,'first_y_m':y,'material':material})
        # The photographed adjacent low roof obscures this wall. The bounded
        # study keeps the lower western area open instead of drawing a new room.
        try:rays.face_hit(faces,mat,names,7.81,1.68)
        except AssertionError:records.append({'feature':'omitted obscured west ground floor','x_m':7.81,'z_m':1.68,'first_y_m':None})
        else:raise AssertionError('Unexpected mesh under west wing')
        results.append({'variant':variant['variant'],'sha256':variant['sha256'],'tests':records})
    args.report.write_text(json.dumps({'id':'changning-zhou-gucheng-courtyard','verifier_sha256':sha(Path(__file__)),'ray_math_sha256':sha(HELPER),'variants':results},ensure_ascii=False,indent=2)+'\n')
    print(sum(len(r['tests'])for r in results),'actual geometry ray checks passed')

if __name__=='__main__':
    main()
