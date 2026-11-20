"""Verify the open passage, arch, leaf scrolls, bunches of grapes, tiles and street-side enclosure in every GLB."""
from argparse import ArgumentParser
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np

ROOT=Path(__file__).resolve().parent
first_contact=runpy.run_path(str(ROOT.parent/'xiaotaoyuan-prayer-hall-v1/check-openings.py'))['first_contact']
SAMPLES=[
    ('clear central aperture', 'south', 0, 2.0, None, 0, 0),
    ('room below arch crown', 'south', 0.05, 4.37, None, 0, 0),
    ('west lane opening', 'south', -1.68, 2.75, None, 0, 0),
    ('east lane opening', 'south', 1.68, 2.75, None, 0, 0),
    ('left pier masonry', 'south', -2.38, 1.62, 'pale pebbled roughcast', -0.008, 0.01),
    ('right pier masonry', 'south', 2.39, 1.45, 'pale pebbled roughcast', -0.008, 0.01),
    ('left stone plinth', 'south', -2.5, 0.35, 'dusky rose plinth stone', -0.072, -0.05),
    ('right stone plinth', 'south', 2.52, 0.35, 'dusky rose plinth stone', -0.075, -0.05),
    ('left spring molding', 'south', -2.55, 2.745, 'fired red terracotta', -0.17, -0.105),
    ('right spring molding', 'south', 2.51, 2.745, 'fired red terracotta', -0.17, -0.105),
    ('green 120 plaque', 'south', 4.13, 2.408, 'green enamel address sign', -0.005, 0.006),
    ('digit 1', 'south', 3.8, 2.44, 'cream enamel letters', -0.016, -0.003),
    ('digit 2', 'south', 3.911, 2.486, 'cream enamel letters', -0.02, 0),
    ('digit 0', 'south', 4.043, 2.447, 'cream enamel letters', -0.02, 0),
    ('mid arch ceramic ring', 'south', 0, 4.705, 'fired red terracotta', -0.09, -0.07),
    ('west roughcast shoulder', 'south', -2.65, 5.89, 'pale pebbled roughcast', -0.008, 0.008),
    ('open flat sky beyond center tiles', 'south', 0.11, 6.17, None, 0, 0),
    ('right top shoulder', 'top', 2.67, 0.15, 'pale pebbled roughcast', 6.38, 6.42),
    ('central roof tile', 'top', -0.118, 0.1, 'glazed red barrel tile', 5.84, 5.94),
    ('left side wall panel', 'south', -5.49, 1.43, 'pale pebbled roughcast', 0.052, 0.072),
    ('right side wall curve above dip', 'south', 7.96, 2.66, None, 0, 0),
    ('upper curved wall below coping', 'south', 7.9, 2.28, 'pale pebbled roughcast', 0.052, 0.071),
    ('folded east leaf', 'east', 1.01, 0.307, 'dark entrance ironwork', 2.105, 2.132),
    ('gold east iron gate ring', 'east', 1.18, 1.3, 'weathered brass fittings', 2.066, 2.102),
    ('dark western leaf', 'west', 0.88, 2.24, 'dark entrance ironwork', -2.13, -2.102),
    ('left pendant grape', 'south', -2.711, 2.276, 'fired red terracotta', -0.19, -0.095),
    ('right pendant grape', 'south', 2.745, 2.275, 'fired red terracotta', -0.19, -0.095),
    ('west grape tassel', 'south', -2.73, 1.116, 'fired red terracotta', -0.152, -0.1),
    ('right pendant relief pin', 'south', 2.73, 1.115, 'fired red terracotta', -0.152, -0.1),
    ('central scallop fluting', 'south', 0.0, 5.12, 'orange relief highlights', -0.24, -0.17),
    ('raised rib on the west acanthus leaf', 'south', -2.84, 4.46, 'orange relief highlights', -0.15, -0.12),
    ('pier notice', 'south', 2.35, 2.24, 'dusky rose plinth stone', -0.085, -0.035),
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
    a.report.write_text(json.dumps({'model_id':'changning-weile-garden-taian-gate','checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'variants':variants},indent=2)+'\n')
    print(len(variants)*len(SAMPLES),'visible surfaces or empty passages checked')

if __name__=='__main__':main()
