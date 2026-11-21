"""Render the paired balconies, three bands of iron ornaments and raised party wall from each decoded model."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-libo-terrace-one-two-balconies/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],rows[0]['width'],rows[0]['height'])
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'green-grey-roughcast.png').read_bytes()).hexdigest()
    for r in report['views']:
        mat=r['material_pixels']
        if r['view'] in ('south-elevation','lane-oblique'):
            # Both overview plates should include the entire roof crest and the foot of each entrance.
            pixels=np.asarray(Image.open(args.output/r['image']).convert('RGB'),dtype=float)
            background=np.array([238,235,226])
            edge=np.concatenate([pixels[:9].reshape(-1,3),pixels[-9:].reshape(-1,3)])
            assert (abs(edge-background).max(axis=1)>40).mean()<.001,r['view']
            assert mat.get('Green grey roughcast',0)>600 and mat.get('Aged black iron',0)>180,r['view']
        if r['view']=='ironwork':
            assert mat.get('Aged black iron',0)>500 and mat.get('Pale cement balcony edges',0)>160,r['view']
        if r['view']=='entry-arches':
            assert mat.get('Umber entrance doors',0)>160 and mat.get('Light rendered hood and door surround',0)>160,r['view']
        if r['view']=='party-wall':assert mat.get('Pale caps of fire separation',0)>150,r['view']
        if r['view']=='green-canopies':assert mat.get('Green awning cloth',0)>150,r['view']
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
