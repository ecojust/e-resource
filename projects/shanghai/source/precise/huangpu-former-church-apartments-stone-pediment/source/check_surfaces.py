from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-former-church-apartments-stone-pediment'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    hits=[]
    def probe(name,x,z,material,front,tolerance=.012):
        origin=[x,-.7,z];r=scene.ray(origin,[0,1,0],1.4)
        good=bool(r and r['material']==material and abs(r['distance_m']-.7-front)<tolerance)
        hits.append(dict(feature=name,origin=origin,material=material,depth=front,observed=r,passed=good))
    for sign in [-1,1]:
        for t in [.14,.27,.43,.57,.76,.9]:
            x=sign*t*1.63;base=1.687-.565*abs(x)
            probe('straight outer capping',x,base+.108,'cornice cap',-.214)
            probe('shadow below the cornice',x,base-.11,'soffit',-.081)
            probe('narrow stepped rebate',x,base-.077,'stone fillet',-.143)
            probe('projecting rounded moulding',x,base+.008,'stone roll',-.203,.022)
        for dx in [-.12,-.04,.06,.16]:
            x=sign*1.17+dx
            probe('stone pier upper block',x,.411,'weathered stone',-.14)
            probe('projected lower horizontal roll',x,.604,'stone roll',-.194)
            probe('projected impost cap',x,.658,'cornice cap',-.22)
    for x in [-.78,-.55,-.25,.04,.49,.71]:
        probe('continuous upper door lintel',x,.414,'weathered stone',-.031)
        probe('shadow below triangular field',x,.584,'soffit',-.089)
    for x in [-.18,.10,.2]:
        probe('flat tympanum course',x,.91,'weathered stone',.034)
    return {'samples':hits,'passed':all(row['passed'] for row in hits)}

def digest(p):
    return sha256(p.read_bytes()).hexdigest()


def main():
    ap=ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=PROJECT/'assets/models/candidates'/ID/'manifest.json')
    ap.add_argument('--out',required=True,type=Path)
    args=ap.parse_args()
    m=json.loads(args.manifest.read_bytes())
    assert m['id']==ID
    rows={}
    with tempfile.TemporaryDirectory() as directory:
        for role in ('raw','full','lod'):
            a=m['assets'][role]
            original=args.manifest.parent/a['file']
            assert original.stat().st_size==a['bytes'] and digest(original)==a['sha256']
            mesh=original
            if role!='raw':
                mesh=Path(directory)/(role+'.glb')
                subprocess.run(['node',UNPACK,original,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh)))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
