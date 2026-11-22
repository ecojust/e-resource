from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-sanduoli-no53-paired-planter-lintel'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    samples=[]
    def target(label,x,z,expected,depth,tolerance=.007):
        h=scene.ray([x,-.45,z],[0,1,0],1.05)
        samples.append(dict(feature=label,x=x,z=z,expected_material=expected,expected_depth=depth,hit=h,
                            passed=bool(h and h['material'] in (expected if isinstance(expected,list) else [expected]) and abs(h['distance_m']-depth)<tolerance)))
    for sign in (-1,1):
        x=.643*sign
        for u in (-.065,-.033,0,.035,.064):
            target('planter fluted body',x+u,.372,['weathered stone','pot raised ribs'],.355,.019)
            target('planter projecting lip',x+u,.447,'weathered stone',.34,.013)
        from math import pi,sin,cos
        for rib in range(7):
            theta=pi*(rib+.5)/7
            radius=.151+(.373-.348)/(.407-.348)*(.166-.151)
            target('raised flute along the bowl shoulder',x+radius*cos(theta),.373,
                   'pot raised ribs',.45-.032-radius*.46*sin(theta)-.0064,.004)
        for z in (.311,.373,.503,.564):
            target('outer surround of end panel',sign*(1.094+.083),z,'relief crest',.378)
            target('recessed centre of end panel',1.094*sign,z,'weathered stone',.398)
        for z in (.338,.421,.496):
            target('inscription side frame',sign*.411,z,'relief crest',.407)
        for u in (.161,.247,.305):
            target('bearing course',sign*u,.060,'sheltered stone',.415)
            target('continuous lower shelf',sign*u,.128,'relief crest',.35)
            target('worn plaque face',sign*u,.454,'sheltered stone',.432)
    for i in range(32):
        x=(i-15.5)*.079
        target('individual dentil '+str(i+1),x,.782,'relief crest',.38)
    for i in range(19):
        x=(i-9)*.127
        target('lower lip of main cornice',x,.933,'relief crest',.292)
    for i in range(11):
        x=(i-5)*.149
        target('projected cap above top relief',x,1.240,'weathered stone',.335)
    return dict(samples=samples,passed=all(s['passed'] for s in samples))

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
