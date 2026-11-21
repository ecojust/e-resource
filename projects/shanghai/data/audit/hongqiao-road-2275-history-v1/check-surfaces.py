"""Check all three released meshes against named elements in the publisher's attributed drawing."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import runpy
import subprocess
import sys

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
IDENT="changning-hongqiao-road-2275-historic-front"
RAYS=[
    ('central gable upper plaster', 'south', 0.0, 3.68, ('pale gable plaster',), -0.954, -0.886),
    ('west gable window light', 'south', -0.62, 1.55, ('tonal grey window lights',), -0.634, -0.566),
    ('east gable window light', 'south', 0.62, 1.55, ('tonal grey window lights',), -0.634, -0.566),
    ('central window mullion', 'south', 0.0, 1.55, ('weathered sash frames',), -0.794, -0.726),
    ('projecting window lintel', 'south', 0.32, 2.1, ('dark bargeboards',), -1.129, -1.061),
    ('sill below grouped window', 'south', 0.24, 0.99, ('carved pale stone',), -1.354, -1.286),
    ('eastern gable surround', 'south', 1.3, 1.12, ('pale gable plaster',), -0.954, -0.886),
    ('western gable surround', 'south', -1.4, 1.72, ('pale gable plaster',), -0.954, -0.886),
    ('west outer eave board', 'south', -6.37, 0.74, ('dark bargeboards',), -0.209, -0.141),
    ('east outer eave board', 'south', 6.35, 0.74, ('dark bargeboards',), -0.209, -0.141),
    ('narrow strip below west eave', 'south', -6.16, 0.31, ('pale gable plaster',), -0.034, 0.034),
    ('narrow strip below east eave', 'south', 7.61, 0.31, ('pale gable plaster',), -0.034, 0.034),
    ('west long roof surface', 'top', -5.33, 1.33, ('grey roof in pen drawing',), 1.74, 1.808),
    ('east long roof surface', 'top', 5.61, 1.27, ('grey roof in pen drawing',), 1.693, 1.761),
    ('west gable surface', 'top', -1.43, -0.68, ('grey roof in pen drawing',), 3.149, 3.217),
    ('east gable surface', 'top', 1.43, -0.66, ('grey roof in pen drawing',), 3.149, 3.217),
    ('gable ridge coping', 'top', 0.0, 0.94, ('raised grey roof courses',), 5.216, 5.284),
    ('west valley seam', 'top', -2.262, 1.65, ('dark bargeboards',), 2.036, 2.104),
    ('east valley seam', 'top', 2.262, 1.65, ('dark bargeboards',), 2.036, 2.104),
    ('west chimney cap', 'top', -2.68, 1.42, ('pale chimney stone',), 4.431, 4.499),
    ('east chimney cap', 'top', 1.66, 2.17, ('pale chimney stone',), 4.941, 5.009),
    ('west chimney stone shaft', 'south', -2.68, 3.95, ('pale chimney stone',), 1.156, 1.224),
    ('east chimney stone shaft', 'south', 1.66, 4.46, ('pale chimney stone',), 1.906, 1.974),
    ('sky over western roof', 'south', -6.2, 4.05, (), None, None),
    ('sky below gable apex beside steep slope', 'south', 2.06, 4.7, (), None, None),
    ('sky between chimneys to left of gable', 'south', -1.63, 4.8, (), None, None),
    ('sky over east roof', 'south', 5.82, 4.28, (), None, None),
]


def check():
    load=runpy.run_path(str(AUDIT.parent/'postal-office-v1/independent-glb-review-helpers.py'))['load_triangles']
    contact=runpy.run_path(str(AUDIT.parent/'xiaotaoyuan-prayer-hall-v1/check-openings.py'))['first_contact']
    folder=PROJECT/'assets/models/candidates'/IDENT
    manifest=json.loads((folder/'manifest.json').read_bytes())
    result=[]
    decoder=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
    codec=PROJECT/'vendor/meshopt_decoder.module.js'
    with TemporaryDirectory() as temporary:
        for role in ('raw','full','lod'):
            asset=manifest['assets'][role]
            path=folder/asset['file']
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            assert digest==asset['sha256']
            if role!='raw':
                decoded=Path(temporary)/(role+'.glb')
                subprocess.run(['node',decoder,path,decoded,codec],check=True)
                path=decoded
            triangles,ids,names,_=load(path)
            samples=[]
            for name,view,x,y,materials,low,high in RAYS:
                mat,depth,normal=contact(triangles,ids,names,view,x,y)
                if materials:
                    assert mat in materials and low<=depth<=high and normal>.2,(role,name,mat,depth,normal)
                else:
                    assert mat is None and depth is None,(role,name)
                samples.append({'feature':name,'view':view,'sample':[x,y],'material':mat,'depth_m':depth,'normal_dot':normal})
            result.append({'variant':role,'asset_sha256':digest,'rays':samples})
    return {'model':IDENT,'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'checks':len(RAYS)*len(result),'variants':result}


if __name__=='__main__':
    path=Path(sys.argv[1]) if len(sys.argv)>1 else AUDIT/'surface-checks.json'
    report=check()
    path.write_text(json.dumps(report,indent=2)+'\n')
    print(report['checks'],'geometry and opening checks')
