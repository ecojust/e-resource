"""Check the glazed projecting room, sheltered porch and stepped red roof pitches on all three delivered meshes."""
from argparse import ArgumentParser
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

ROOT=Path(__file__).resolve().parent
first_contact=runpy.run_path(str(ROOT.parent/'xiaotaoyuan-prayer-hall-v1/check-openings.py'))['first_contact']
SAMPLES = [
    ('projecting room, west light', 'south', -3.0, 5.21, ('shaded multi-light glass',), 0.153, 0.185),
    ('projecting room, centre light', 'south', 0.53, 5.85, ('shaded multi-light glass',), 0.153, 0.185),
    ('projecting room, east light', 'south', 2.98, 6.42, ('shaded multi-light glass',), 0.153, 0.185),
    ('cream sill of long window', 'south', 0.37, 4.755, ('warm limestone moulding',), -0.131, -0.099),
    ('central casement bottom rail', 'south', -0.61, 4.816, ('dark stained casement frames',), 0.054, 0.086),
    ('cream above central window', 'south', 0.73, 6.87, ('butter cream roughcast',), -0.016, 0.016),
    ('dark central front door', 'south', -0.63, 1.61, ('dark stained casement frames',), 1.651, 1.683),
    ('right door wood panel', 'south', 0.63, 1.68, ('dark stained casement frames',), 1.651, 1.683),
    ('left light beside porch door', 'south', -2.05, 1.74, ('shaded multi-light glass',), 1.843, 1.875),
    ('eastern side light', 'south', 2.11, 1.86, ('dark stained casement frames',), 1.744, 1.776),
    ('left square pier', 'south', -3.82, 2.4, ('butter cream roughcast',), 0.014, 0.046),
    ('right square pier', 'south', 4.04, 2.36, ('butter cream roughcast',), 0.014, 0.046),
    ('porch main girder front', 'south', -1.56, 3.94, ('warm limestone moulding',), -0.896, -0.864),
    ('exposed garden end rafter', 'south', 0.15, 3.75, ('butter cream roughcast',), 1.674, 1.706),
    ('first red tread riser', 'south', 0.4, 0.084, ('red brown garden steps',), -1.416, -1.384),
    ('second red tread riser', 'south', 0.4, 0.19, ('red brown garden steps',), -1.126, -1.094),
    ('third red tread riser', 'south', 0.4, 0.34, ('red brown garden steps',), -0.836, -0.804),
    ('fourth red tread riser', 'south', 0.4, 0.477, ('red brown garden steps',), -0.546, -0.514),
    ('left garden casement', 'south', -5.82, 2.19, ('shaded multi-light glass',), 2.133, 2.165),
    ('west balcony baluster', 'south', -8.14, 4.43, ('warm limestone moulding',), 0.994, 1.026),
    ('view through western railing', 'south', -7.92, 4.43, ('butter cream roughcast',), 1.964, 1.996),
    ('balcony coping', 'south', -6.15, 4.87, ('butter cream roughcast',), 0.959, 0.991),
    ('east lower garden window', 'south', 6.63, 1.87, ('shaded multi-light glass',), 2.163, 2.195),
    ('east upper garden window', 'south', 6.58, 5.77, ('shaded multi-light glass',), 2.163, 2.195),
    ('east cream floor course', 'south', 7.45, 3.93, ('warm limestone moulding',), 1.789, 1.821),
    ('west roof tiling', 'top', -6.11, 2.77, ('weathered vermilion pantiles',), 7.452, 7.484),
    ('centre pitched roof', 'top', -0.58, 1.67, ('faded orange tile courses',), 7.946, 7.986),
    ('east hip tiling', 'top', 6.98, 3.28, ('faded orange tile courses', 'weathered vermilion pantiles'), 7.865, 7.919),
    ('left chimney crown', 'top', -1.29, 3.36, ('warm limestone moulding',), 9.239, 9.271),
    ('right chimney crown', 'top', 7.95, 4.56, ('warm limestone moulding',), 9.139, 9.171),
    ('open sky between chimneys', 'south', 3.12, 9.2, (None,), 0, 0),
]


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--work',required=True,type=Path)
    parser.add_argument('--report',default=ROOT/'visible-surfaces.json',type=Path)
    a=parser.parse_args();variants=[]
    for r in json.loads((a.work/'delivered-decode.json').read_bytes()):
        triangles=np.fromfile(r['triangle_file'],np.float64).reshape(-1,3,3)[:,:,[0,2,1]]*[1,-1,1]
        tags=np.fromfile(r['triangle_material_ids_file'],np.uint16);results=[]
        for name,view,x,z,expected,low,high in SAMPLES:
            mat,depth,normal=first_contact(triangles,tags,r['material_names'],view,x,z)
            assert mat in expected and (mat is None or (low<=depth<=high and normal>.01)),(r['variant'],name,mat,depth,normal)
            results.append(dict(feature=name,view=view,coordinates_m=[x,z],first_depth_m=depth,material=mat,outward_normal_dot=normal))
        variants.append(dict(variant=r['variant'],sha256=r['sha256'],rays=results))
    a.report.write_text(json.dumps({'model_id':'xuhui-yueyang-road-110-residence','checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants},indent=2)+'\n')
    print(len(variants)*len(SAMPLES),'south-elevation material, depth, outward facing and open skyline checks')

if __name__=='__main__':main()
