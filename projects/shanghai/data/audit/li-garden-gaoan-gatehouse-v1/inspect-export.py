"""Render the gatehouse, its double brick archivolt and the unobstructed carriage passage."""
from pathlib import Path
import argparse,hashlib,json,runpy
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
SOURCE=HERE.parents[2]/'source/precise/xuhui-li-garden-gaoan-gatehouse/source'
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();cameras=SOURCE/'cameras.json';rows=json.loads(cameras.read_bytes())
    method=HERE.parent/'fifth-textile-warehouse-river-front-v1/inspect-export.py'
    report=runpy.run_path(method)['render'](args.mesh,args.output,[(r['name'],r['eye'],r['target'],r['width_m'])for r in rows],rows[0]['width'],rows[0]['height'])
    assert len(report['views'])==7 and report['embedded_textures'][0]['embedded_sha256']==hashlib.sha256((SOURCE/'ivory-roughcast.png').read_bytes()).hexdigest()
    prominent = {
        'street-gable':('Ivory roughcast stucco','Burnished red arch brick','Smoke blue window glass'),
        'court-gable':('Ivory roughcast stucco','Deep red arch brick','Grey dressed pier base'),
        'brick-arch':('Muted russet arch brick','Silver grey lime joint','Fired tile cut edge'),
        'passage':('Charcoal paving','Deep red plinth brick','Warm lime plaster'),
        'upper-window':('Ivory roughcast stucco','Smoke blue window glass','Grey green steel window'),
        'open-gates':('Black green wrought iron','Deep red plinth brick','Charcoal paving'),
        'roof-and-tiles':('Ivory roughcast stucco','Russet clay cover tile','Green rainwater fittings'),
    }
    for view in report['views']:
        name=view['view']
        counts=view['material_pixels']
        for material in prominent[name]:
            assert counts.get(material,0)>32,(name,material,counts)
        if name in ('street-gable','court-gable'):
            pixels=np.asarray(Image.open(args.output/view['image']).convert('RGB'),dtype=float)
            background=np.array([238,235,226])
            border=np.concatenate([pixels[:4].reshape(-1,3),pixels[-4:].reshape(-1,3),
                                   pixels[:,:4].reshape(-1,3),pixels[:,-4:].reshape(-1,3)])
            assert (abs(border-background).max(axis=1)>40).mean()<.001,name
    report['camera_source_sha256']=hashlib.sha256(cameras.read_bytes()).hexdigest()
    (args.output/'views.json').write_text(json.dumps(report,indent=2)+'\n')
