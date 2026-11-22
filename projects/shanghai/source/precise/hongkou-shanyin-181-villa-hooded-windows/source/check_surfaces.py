from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-shanyin-181-villa-hooded-windows'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    records=[]
    def target(feature,x,z,mat,front,tol=.005):
        hit=scene.ray([x,-.5,z],[0,1,0],1)
        records.append(dict(feature=feature,x=x,z=z,expected_materials=mat,expected_depth=.5+front,hit=hit,
                            passed=bool(hit and hit['material'] in mat and abs(hit['distance_m']-.5-front)<tol)))
    for x in (-1.075,1.075):
        for u in (-.345,-.09,.088,.342):
            for z in (.55,.76,1.06):target('lower clear panes',x+u,z,['clear pane'],.157)
            for z in (1.262,1.479):target('recessed transom panes',x+u,z,['shaded transom'],.145)
        for u in (-.198,0,.198):
            for z in (.48,.83,1.07):
                target('lower narrow glazing bars',x+u,z,['painted joinery'],.09 if u==0 else .102)
        for sign in (-1,1):
            for z in (.57,.84,1.154,1.429):
                target('stone surround in front of sash',x+sign*.464,z,['hood stone'],-.066)
            for z,y in [(.18,-.066),(.211,-.084),(.239,-.102)]:
                target('each stepped sill bracket',x+sign*.355,z,['hood stone'],y)
            for z,y in [(1.481,-.101),(1.517,-.126),(1.564,-.137),(1.611,-.157)]:
                target('hood end stop',x+sign*.473,z,['hood stone'],y)
        for z,y,mat in [(1.651,-.112,'hood stone'),(1.699,-.130,'stone edging'),
                        (1.733,-.168,'hood stone'),(1.774,-.170,'hood stone'),(1.806,-.200,'stone edging')]:
            for u in (-.31,.105,.278):target('hood moulding courses',x+u,z,[mat,'stone grain'],y)
        for u in (-.32,-.092,.179,.328):
            target('projecting sill',x+u,.316,['stone edging','stone grain'],-.135)
    for x in (-1.62,-.928,-.56,-.31,-.10,.21,.488,.712,1.22,1.711):
        target('lower eave fascia',x,2.10,['stone shadow'],-.097)
        target('eave overhang',x,2.16,['eave underside'],-.197)
        target('front tile lip',x,2.197,['roof edge'],-.221)
    return dict(samples=records,passed=all(r['passed']for r in records))

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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
