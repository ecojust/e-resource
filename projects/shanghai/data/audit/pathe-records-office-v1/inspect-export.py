"""Render the four photographed elevations, northern entrance and garden colonnade from the decoded exterior."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-pathe-records-office/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],rows[0]['width'],rows[0]['height'])
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'pathe-red-brick.png').read_bytes()).hexdigest()
    prominent = {
        'north-front': ('Pathe red stretchers','Warm dressed stone','Daylit glazing'),
        'garden-elevation': ('Pathe red stretchers','Warm white enamel','Daylit glazing'),
        'curved-canopy': ('Panelled entrance doors','Warm white enamel','Green enamel plaque'),
        'stair-light': ('Stair flight behind the light','Dark window frames','Daylit glazing'),
        'eastern-arches': ('Pathe red stretchers','Warm dressed stone','Daylit glazing'),
        'garden-colonnade': ('Warm white enamel','Daylit glazing','Pathe red stretchers'),
        'oblique-roofs': ('Old roof clay','Weathered tile troughs','Pathe red stretchers'),
    }
    for view in report['views']:
        name=view['view']
        counts=view['material_pixels']
        for material in prominent[name]:
            assert counts.get(material,0)>32,(name,material,counts)
        if name in ('north-front','garden-elevation','oblique-roofs'):
            pixels=np.asarray(Image.open(args.output/view['image']).convert('RGB'),dtype=float)
            background=np.array([238,235,226])
            border=np.concatenate([pixels[:4].reshape(-1,3),pixels[-4:].reshape(-1,3),
                                   pixels[:,:4].reshape(-1,3),pixels[:,-4:].reshape(-1,3)])
            assert (abs(border-background).max(axis=1)>40).mean()<.001,name
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
