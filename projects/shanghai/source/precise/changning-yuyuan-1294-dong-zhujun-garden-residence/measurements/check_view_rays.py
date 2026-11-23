"""Intersect the two surveyed photograph stations with each physically decoded model."""
import argparse
import json
from pathlib import Path
import runpy

import numpy as np

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
reader=runpy.run_path(str(PROJECT/'source/precise/changning-xinhuacun-12-numbered-gable/measurements/photo_ray_mesh.py'))
cli=argparse.ArgumentParser(description=__doc__)
cli.add_argument('models',type=Path,help='Package directory holding decoded-full.glb and decoded-lod.glb')
cli.add_argument('output',type=Path)
args=cli.parse_args()
stations=json.loads((HERE/'two-stations.json').read_bytes())
observed=json.loads((HERE/'held-photo-observations.json').read_bytes())['observations']
report={'coordinate_system':'Original uncropped source pixels, upper left origin. First visible model surface at each ray. Outside-stair camera relative to the façade is conditional.','assets':{}}
for label in ['full','lod']:
    triangles,index,names,model=reader['load_triangles'](args.models/f'decoded-{label}.glb')
    model['stations']={}
    for fixed,num in [('numbered-gable',0),('outside-stair',2)]:
        cam=stations[fixed]
        center=np.array(cam['C'])
        matrix=np.array(cam['K'])@np.array(cam['R'])
        points=observed[num]['observed'].copy()
        if fixed=='numbered-gable':
            points.update(skirt_west_visible=[85,128],skirt_mid=[144,117],skirt_east_visible=[192,110],
                          attic_window_center=[164,96],second_story_window_center=[140,159],
                          circular_enamel_plate=[143,266],west_gallery_arcade=[57,247])
        result={}
        for name,xy in points.items():
            direction=np.linalg.solve(matrix,[*xy,1])
            item,distance,xyz=reader['first_hit'](triangles,center,direction)
            result[name]={'source_pixel':xy,'first_material':names[index[item]] if np.isfinite(distance) else None,'distance_m':round(distance,4) if np.isfinite(distance) else None,'xyz_m':xyz.round(4).tolist() if np.isfinite(distance) else None}
        model['stations'][fixed]=result
    report['assets'][label]=model
args.output.write_text(json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
