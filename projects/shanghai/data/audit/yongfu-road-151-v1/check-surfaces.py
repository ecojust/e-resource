"""Check the three deep bays, spiral shafts, six arcade windows, balcony edges and terrace stairs."""
from argparse import ArgumentParser
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

ROOT=Path(__file__).resolve().parent
first_contact=runpy.run_path(str(ROOT.parent/'xiaotaoyuan-prayer-hall-v1/check-openings.py'))['first_contact']
SAMPLES = [
    ('curved west lower casement', 'south', -5.57, 2.19, 'shaded courtyard glazing', 0.358, 0.388),
    ('curved west middle casement', 'south', -5.68, 6.13, 'shaded courtyard glazing', 0.358, 0.388),
    ('upper recessed loggia glass', 'south', -5.68, 9.23, 'shaded courtyard glazing', 3.08, 3.11),
    ('west lower spiral column', 'south', -5.05, 2.32, 'carved pale plaster', 0.1, 0.13),
    ('west middle spiral column', 'south', -5.06, 5.91, 'carved pale plaster', 0.101, 0.132),
    ('west upper spiral column', 'south', -5.06, 9.17, 'carved pale plaster', 0.1, 0.131),
    ('curved floor moulding', 'south', -6.16, 4.095, 'carved pale plaster', -0.068, -0.035),
    ('center lower door', 'south', -0.51, 2.11, 'shaded courtyard glazing', 2.295, 2.325),
    ('center middle window', 'south', 0.73, 5.92, 'shaded courtyard glazing', 2.295, 2.325),
    ('upper west central opening', 'south', -0.55, 9.04, 'shaded courtyard glazing', 2.275, 2.305),
    ('upper east central opening', 'south', 1.12, 9.02, 'shaded courtyard glazing', 2.275, 2.305),
    ('center parapet', 'south', 0.18, 11.69, 'warm ivory roughcast', 2.175, 2.205),
    ('sky above crest', 'south', 0.18, 12.08, None, 0, 0),
    ('first terrace riser', 'south', 0.22, 0.08, 'dressed buff terrace stone', -0.845, -0.815),
    ('second terrace riser', 'south', 0.22, 0.19, 'dressed buff terrace stone', -0.6, -0.57),
    ('third terrace riser', 'south', 0.22, 0.34, 'dressed buff terrace stone', -0.355, -0.325),
    ('lower balcony fascia', 'south', -0.21, 3.9, 'warm ivory roughcast', 0.575, 0.605),
    ('upper balcony fascia', 'south', 0.33, 7.5, 'warm ivory roughcast', 0.575, 0.605),
    ('west central bay parapet shoulder', 'south', -2.82, 11.15, 'warm ivory roughcast', 2.175, 2.205),
    ('first lower arch', 'south', 4.91, 2.11, 'shaded courtyard glazing', 1.26, 1.29),
    ('second lower arch', 'south', 6.42, 2.17, 'shaded courtyard glazing', 1.26, 1.29),
    ('third lower arch', 'south', 7.94, 2.13, 'shaded courtyard glazing', 1.26, 1.29),
    ('first upper arch', 'south', 4.91, 5.43, 'shaded courtyard glazing', 1.26, 1.29),
    ('second upper arch', 'south', 6.42, 5.47, 'shaded courtyard glazing', 1.26, 1.29),
    ('third upper arch', 'south', 7.94, 5.41, 'shaded courtyard glazing', 1.26, 1.29),
    ('east arcade spiral jamb', 'south', 5.42, 1.95, 'carved pale plaster', 1.017, 1.047),
    ('upper arcade spiral jamb', 'south', 6.97, 5.8, 'carved pale plaster', 1.019, 1.05),
    ('diamond relief', 'south', 6.19, 7.717, 'dressed buff terrace stone', 1.082, 1.112),
    ('first lower arch archivolt at its shoulder', 'south', 5.77, 3.05, 'carved pale plaster', 1.07, 1.1),
    ('sky above eastern roof', 'south', 7.65, 8.46, None, 0, 0),
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
            assert mat==expected and (mat is None or (low<=depth<=high and normal>.01)),(r['variant'],name,mat,depth,normal)
            results.append(dict(feature=name,view=view,coordinates_m=[x,z],first_depth_m=depth,material=mat,outward_normal_dot=normal))
        variants.append(dict(variant=r['variant'],sha256=r['sha256'],rays=results))
    a.report.write_text(json.dumps({'model_id':'xuhui-yongfu-road-151-south-front','checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants},indent=2)+'\n')
    print(len(variants)*len(SAMPLES),'south-elevation material, depth, outward facing and open skyline checks')

if __name__=='__main__':main()
