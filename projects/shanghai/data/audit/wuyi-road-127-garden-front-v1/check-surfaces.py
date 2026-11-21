"""Check all three released meshes against named elements on the published garden elevation."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import runpy
import subprocess
import sys

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
IDENT="changning-wuyi-road-127-garden-front"
RAYS=[
    ('glass gallery light -3.04', 'south', -2.77, 1.8, ('blue grey glazing',), -2.264, -2.196),
    ('glazing mullion -3.04', 'south', -3.04, 2.6, ('ivory painted mullions',), -2.424, -2.356),
    ('glass gallery light 0', 'south', 0.27, 1.8, ('blue grey glazing',), -2.264, -2.196),
    ('glazing mullion 0', 'south', 0, 2.6, ('ivory painted mullions',), -2.424, -2.356),
    ('glass gallery light 3.04', 'south', 3.31, 1.8, ('blue grey glazing',), -2.264, -2.196),
    ('glazing mullion 3.04', 'south', 3.04, 2.6, ('ivory painted mullions',), -2.424, -2.356),
    ('second gallery pier', 'south', -1.52, 2.17, ('cream roughcast plaster',), -2.584, -2.516),
    ('terrace string course', 'south', 0.73, 3.87, ('carved pale stone',), -2.724, -2.656),
    ('terrace rail', 'south', 0.45, 4.72, ('carved pale stone',), -2.704, -2.636),
    ('turned baluster', 'south', -0.253, 4.4, ('carved pale stone',), -2.696, -2.628),
    ('opening between balusters', 'south', 0.03, 4.39, ('cream roughcast plaster',), -0.034, 0.034),
    ('left wall end window', 'south', -6.43, 2.15, ('blue grey glazing',), 0.286, 0.354),
    ('right wall end window', 'south', 6.56, 1.68, ('blue grey glazing',), 0.286, 0.354),
    ('garden room upper sash', 'south', 2.23, 5.65, ('blue grey glazing',), 0.286, 0.354),
    ('left upper end window', 'south', -6.36, 5.75, ('blue grey glazing',), 0.286, 0.354),
    ('hang of window head', 'south', 6.43, 3.35, ('carved pale stone',), -0.209, -0.141),
    ('eaves bracket', 'south', 0, 6.73, ('carved pale stone',), -0.344, -0.276),
    ('open between two eaves brackets', 'south', 0.24, 6.73, ('cream roughcast plaster',), -0.034, 0.034),
    ('lower mansard tile band', 'south', 2.45, 7.51, ('charcoal ceramic tile',), -0.087, -0.019),
    ('west shed dormer pane', 'south', -4.69, 8.3, ('blue grey glazing',), 0.204, 0.272),
    ('east shed dormer pane', 'south', 5.03, 8.28, ('blue grey glazing',), 0.204, 0.272),
    ('pediment dormer pane', 'south', 0.32, 8.3, ('blue grey glazing',), 0.204, 0.272),
    ('central dormer stone triangle', 'south', 0.036, 9.27, ('carved pale stone',), -0.151, -0.083),
    ('pediment roof slope', 'top', 0.78, 0.36, ('charcoal ceramic tile',), 9.46, 9.528),
    ('upper mansard roof', 'top', 2.18, 2.13, ('charcoal ceramic tile', 'grey tile laps'), 9.867, 9.963),
    ('west chimney coping', 'top', -5.69, 2.69, ('carved pale stone',), 10.831, 10.899),
    ('east chimney coping', 'top', 5.65, 2.69, ('carved pale stone',), 10.831, 10.899),
    ('open skyline between chimneys', 'south', -0.65, 10.75, (), None, None),
    ('west roof hip surface', 'top', -7.93, 2.35, ('charcoal ceramic tile',), 7.84, 7.908),
    ('east roof hip surface', 'top', 7.93, 2.35, ('charcoal ceramic tile',), 7.84, 7.908),
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
