from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-bank-of-china-warehouse-stepped-gate'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from stepped_gate import CENTRES
    rows=[]
    def front(label,x,z,y,materials):
        pos=[x,-.25,z];h=scene.ray(pos,[0,1,0],.5)
        ok=(h is None if y is None else bool(h and h['material'] in materials and abs(h['distance_m']-(y+.25))<.004))
        rows.append(dict(feature=label,origin=pos,expected_y=y,expected_materials=materials,observed=h,passed=ok))
    for cx in (-.505,.505):
        for i,z in enumerate(CENTRES):
            for x in (-.23,-.07,.05,.26):front('recessed panel',cx+x,z,-.035,['plate face'])
            for x in (-.22,0,.22):front('pressed return near top',cx+x,z+.105,-.047,['rolled panel edge'])
            for sign in (-1,1):front('projecting stud',cx+sign*.313,z+.075,-.039,['edge fastening'])
            if i<3:
                for d in (.213,.305):
                    front('flat steel lattice',cx+.08,z+d,-.004,['graphite web'])
                for x in (-.26,-.09,.07,.27):front('opening between two rails',cx+x,z+.260,None,[])
                for x in (-.182,.182):front('vertical joint',cx+x,z+.260,-.004,['graphite web'])
                for x in (-.347,.347):front('short stepped return',cx+x,z+.17,-.003,['graphite web'])
        front('bottom rail',cx,.108,-.018,['blackened leaf frame'])
    for z in (.29,.71,1.20,1.91):front('recess between leaves',0,z,.043,['dark interlock'])
    return dict(passed=all(r['passed']for r in rows),samples=rows)

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
