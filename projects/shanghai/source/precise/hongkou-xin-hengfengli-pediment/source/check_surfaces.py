from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-xin-hengfengli-pediment'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import hypot
    rows=[]
    def shoot(label,x,z,mats,depth,tol=.013):
        origin=[x,-1,z];direction=[0,1,0];hit=scene.ray(origin,direction,2)
        rows.append(dict(check=label,origin=origin,direction=direction,expected_material=mats,expected_depth=depth,hit=hit,passed=bool(hit and hit['material'] in mats and abs(hit['distance_m']-(1+depth))<tol)))
    for i in range(18):
        x=-2.18+i*.244
        for title,z,material,depth in [('Bottom soffit bead',.040,'light stone',-.092),('Shaded step between bottom bands',.113,'shaded aggregate',-.042),('Lower drip mould',.169,'light stone',-.087),('Pediment lower bed',1.17,'light stone',-.088),('Dark cornice edge',1.213,'edge in shade',-.104),('Outer projecting bed',1.265,'light stone',-.157)]:
            shoot(title,x,z,[material],depth)
    for sign in (-1,1):
        for t in [.10,.23,.35,.48,.62,.77,.88]:
            x=sign*2.255*t;z=2.437+(1.297-2.437)*t
            shoot('Raking outer cornice',x,z,['light stone'],-.127)
            x=sign*1.99*t;z=2.25+(1.297-2.25)*t
            shoot('Inner stone mould',x,z,['light stone'],-.075)
        for x,z in [(.22,1.975),(.87,1.65),(1.23,1.51),(1.53,1.41)]:
            shoot('Exposed tympanum',sign*x,z,['grained stone'],-.018)
    for x,z in [(0,1.72),(.08,1.78),(-.08,1.77),(0,1.83)]:shoot('Projecting uninscribed shield',x,z,['light stone'],-.154)
    for x in (-1.05,-.9,-.76,-.57,-.4,-.2,.17,.39,.56,.75,.91,1.05):
        shoot('Inscription tablet upper line',x,.975,['light stone'],-.045)
    for x,z in [(-.65,.444+.67*.405),(-.65,.444+.43*.405),(.0,.444+.665*.405),(.0,.444+.29*.405),(.65+(.19-.5)*.41,.444+.51*.405),(.65+(.74-.5)*.41,.444+.84*.405)]:
        shoot('Three raised inscription strokes',x,z,['letter face'],-.064,.025)
    return dict(passed=all(row['passed']for row in rows),samples=rows)


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
