"""Render the west entrance, folded metal canopy and carved stone landing from the decoded meshes."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-jianguo-602-west-canopy/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],rows[0]['width'],rows[0]['height'])
    expected={hashlib.sha256((SOURCE/name).read_bytes()).hexdigest() for name in ('ochre-dragged-render.png','dressed-grey-granite.png')}
    assert len(report['views'])==7 and {item['embedded_sha256'] for item in report['embedded_textures']}==expected
    prominent = {
        'west-entrance':('Pale ochre cement render','Green painted sheet metal','Grey dressed granite'),
        'oblique-entrance':('Pale ochre cement render','Green painted sheet metal','Grey dressed granite'),
        'folded-roof':('Green painted sheet metal','Dark green folded steel','Green enamel edges'),
        'radial-landing':('Grey dressed granite','Cut stone grooves','Dark steel hardware'),
        'scalloped-valance':('Green enamel edges','Green painted sheet metal','Dark green folded steel'),
        'open-vestibule':('Cream moulded portal','Deep green iron gate','Old square clay tiles'),
        'stone-surround':('Cream moulded portal','Deep green iron gate','Pale ochre cement render'),
    }
    for view in report['views']:
        name=view['view']
        counts=view['material_pixels']
        for material in prominent[name]:
            assert counts.get(material,0)>32,(name,material,counts)
        if name in ('west-entrance','oblique-entrance'):
            pixels=np.asarray(Image.open(args.output/view['image']).convert('RGB'),dtype=float)
            background=np.array([238,235,226])
            border=np.concatenate([pixels[:4].reshape(-1,3),pixels[-4:].reshape(-1,3),
                                   pixels[:,:4].reshape(-1,3),pixels[:,-4:].reshape(-1,3)])
            assert (abs(border-background).max(axis=1)>40).mean()<.001,name
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
