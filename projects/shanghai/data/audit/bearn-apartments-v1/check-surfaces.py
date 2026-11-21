"""Check all three released meshes against the photographed bays, curved windows, roofline, and original shop lettering."""
from pathlib import Path
from tempfile import TemporaryDirectory
import hashlib
import json
import runpy
import subprocess
import sys

AUDIT=Path(__file__).resolve().parent
PROJECT=AUDIT.parents[2]
IDENT="huangpu-bearn-apartments"
RAYS=[
    ('Apartment window 2 central glazing', 'south', -52.78, 11.69, ('blue grey upper glazing',), 8.971, 9.039),
    ('Brick or rendered spandrel at bay 2', 'south', -52.215, 10.23, ('warm brown small facing tiles',), 7.611, 7.679),
    ('Storefront glazing 2', 'south', -52.013, 2.0, ('street shop glazing',), 8.731, 8.799),
    ('Apartment window 4 central glazing', 'south', -45.587, 11.69, ('blue grey upper glazing',), 2.858, 2.926),
    ('Brick or rendered spandrel at bay 4', 'south', -45.854, 10.23, ('warm brown small facing tiles',), 2.622, 2.69),
    ('Apartment window 6 central glazing', 'south', -38.869, 11.69, ('blue grey upper glazing',), 0.537, 0.605),
    ('Brick or rendered spandrel at bay 6', 'south', -39.084, 10.23, ('warm brown small facing tiles',), 0.253, 0.321),
    ('Storefront glazing 6', 'south', -38.869, 2.0, ('street shop glazing',), 1.035, 1.103),
    ('Apartment window 8 central glazing', 'south', -32.182, 11.69, ('blue grey upper glazing',), 0.303, 0.371),
    ('Brick or rendered spandrel at bay 8', 'south', -32.522, 10.23, ('ivory rendered wall',), -0.018, 0.05),
    ('Apartment window 9 central glazing', 'south', -27.64, 11.69, ('blue grey upper glazing',), 0.336, 0.404),
    ('Brick or rendered spandrel at bay 9', 'south', -27.981, 10.23, ('warm brown small facing tiles',), 0.015, 0.083),
    ('Apartment window 10 central glazing', 'south', -23.098, 11.69, ('blue grey upper glazing',), -0.121, -0.053),
    ('Brick or rendered spandrel at bay 10', 'south', -23.439, 10.23, ('warm brown small facing tiles',), -0.442, -0.374),
    ('Storefront glazing 10', 'south', -23.098, 2.0, ('street shop glazing',), 0.369, 0.437),
    ('Apartment window 11 central glazing', 'south', -18.556, 11.69, ('blue grey upper glazing',), 0.402, 0.47),
    ('Brick or rendered spandrel at bay 11', 'south', -18.897, 10.23, ('ivory rendered wall',), 0.081, 0.149),
    ('Apartment window 13 central glazing', 'south', -9.473, 11.69, ('blue grey upper glazing',), -0.022, 0.046),
    ('Brick or rendered spandrel at bay 13', 'south', -9.813, 10.23, ('warm brown small facing tiles',), -0.343, -0.275),
    ('Apartment window 14 central glazing', 'south', -4.931, 11.69, ('blue grey upper glazing',), 0.501, 0.569),
    ('Brick or rendered spandrel at bay 14', 'south', -5.272, 10.23, ('ivory rendered wall',), 0.18, 0.248),
    ('Storefront glazing 14', 'south', -4.931, 2.0, ('street shop glazing',), 0.501, 0.569),
    ('Apartment window 15 central glazing', 'south', -0.389, 11.69, ('blue grey upper glazing',), 0.044, 0.112),
    ('Brick or rendered spandrel at bay 15', 'south', -0.73, 10.23, ('warm brown small facing tiles',), -0.277, -0.209),
    ('Apartment window 17 central glazing', 'south', 8.694, 11.69, ('blue grey upper glazing',), 0.11, 0.178),
    ('Brick or rendered spandrel at bay 17', 'south', 8.354, 10.23, ('warm brown small facing tiles',), -0.211, -0.143),
    ('Apartment window 19 central glazing', 'south', 17.988, 11.69, ('blue grey upper glazing',), 0.594, 0.662),
    ('Brick or rendered spandrel at bay 19', 'south', 17.62, 10.23, ('ivory rendered wall',), 0.283, 0.351),
    ('Storefront glazing 19', 'south', 17.988, 2.0, ('street shop glazing',), 0.594, 0.662),
    ('Apartment window 20 central glazing', 'south', 22.894, 11.69, ('blue grey upper glazing',), 0.014, 0.082),
    ('Brick or rendered spandrel at bay 20', 'south', 22.526, 10.23, ('warm brown small facing tiles',), -0.298, -0.23),
    ('Apartment window 22 central glazing', 'south', 32.708, 11.69, ('blue grey upper glazing',), -0.168, -0.1),
    ('Brick or rendered spandrel at bay 22', 'south', 32.34, 10.23, ('warm brown small facing tiles',), -0.479, -0.411),
    ('Storefront glazing 22', 'south', 32.708, 2.0, ('street shop glazing',), 0.323, 0.391),
    ('Main curved cornice over east windows', 'south', -45.3, 19.94, ('grey concrete ledges',), 2.498, 2.566),
    ('Curved top-storey band window', 'south', -45.86, 21.41, ('blue grey upper glazing',), 4.497, 4.565),
    ('Projecting rounded upper ledge', 'south', -46.6, 22.97, ('grey concrete ledges',), 4.106, 4.174),
    ('Lower stepped roof', 'top', 21, 7.6, ('flat roof surface',), 20.056, 20.124),
    ('East end flat roof behind the curve', 'top', -46.03, 13.9, ('flat roof surface',), 23.296, 23.364),
    ('Upper terrace below central cap', 'top', -16.2, 5.4, ('flat roof surface',), 29.686, 29.754),
    ('Top of central stepped cap', 'top', -5.5, 5.7, ('grey concrete ledges',), 31.926, 31.994),
    ('Open skyline over lower west wing', 'south', 26.7, 25.0, (), None, None),
    ('Open skyline above east curve', 'south', -47.3, 25.95, (), None, None),
    ('Open skyline outside west cut', 'south', 38.9, 10.0, (), None, None),
    ('White sign fascia', 'south', -5.0, 28.82, ('ivory rendered wall',), 2.052, 2.12),
    ('Red rooftop shop lettering', 'south', -7.048, 28.84, ('red shop lettering',), 1.987, 2.055),
    ('Central pyramidal finial', 'south', -5.58, 32.17, ('grey concrete ledges',), 3.512, 3.58),
    ('Side finial of central cap', 'south', -6.66, 32.17, ('grey concrete ledges',), 3.823, 3.891),
    ('Main canopy edge', 'south', 10.7, 3.67, ('grey concrete ledges',), -0.334, -0.266),
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
