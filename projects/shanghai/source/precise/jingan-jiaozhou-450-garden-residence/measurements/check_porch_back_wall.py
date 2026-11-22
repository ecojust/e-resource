"""Trace native photo pixels to the closest material on the complete unfiltered garden mesh."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
import numpy as np

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]/'xuhui-pathe-records-office/measurements/city-contact'))
from glb_triangles import SerialScene


def classify(material):
    if not material:
        return 'empty'
    names={'Rear porch | shaded red running bond':'brick',
           'Rear porch | unlit face behind entrance':'door',
           'Rear porch | dark masonry sill edge':'sill',
           'Rear porch | pale ochre closing board':'panel',
           'Rear porch | dark weathered joinery':'wood',
           'Rear porch | worn edge of timber bead':'wood'}
    if material.startswith('Garden arcade |'):
        return 'pier'
    if material.startswith('Rear porch |') and 'glazing' in material:
        return 'glazing'
    return names.get(material,material)


def inspect(mesh):
    reg=json.loads((HERE/'porch-back-wall-registration.json').read_bytes())
    camera_file=HERE/reg['reference_camera']
    assert sha256(camera_file.read_bytes()).hexdigest()==reg['camera_sha256']
    cameras=json.loads(camera_file.read_bytes())
    scene=SerialScene(mesh)
    observations=[]
    for name,groups in reg['probe_pixels'].items():
        camera=np.asarray(cameras[name]['P'])
        inv=np.linalg.inv(camera[:,:3])
        eye=-inv@camera[:,3]
        for group,points in groups.items():
            expected='glazing' if group in ('transom','window') else group
            for u,v in points:
                first=scene.ray(eye,inv@[u,v,1.],50)
                material=first['material'] if first else None
                actual=classify(material)
                observations.append(dict(figure=name,native_pixel=[u,v],element=group,
                                         expected=expected,first_material=material,
                                         observed=actual,direct_match=actual==expected))
    counts=Counter((r['figure'],r['direct_match']) for r in observations)
    return {'asset':scene.asset,'samples':len(observations),'direct':sum(x['direct_match'] for x in observations),
            'by_figure':{k:{'direct':counts[k,True],'total':counts[k,True]+counts[k,False]} for k in reg['probe_pixels']},
            'observations':observations}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    result=inspect(args.glb)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['direct'],result['samples'],result['by_figure'])
