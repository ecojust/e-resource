from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-ramos-apartments-twin-arches'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import pi,sin,cos
    rows=[]
    def shoot(name,x,z,mat,depth,tol=.013):
        eye=[x,-1,z];dr=[0,1,0];hit=scene.ray(eye,dr,1.8)
        rows.append(dict(check=name,origin=eye,direction=dr,expected=mat,expected_depth=depth,hit=hit,passed=bool(hit and hit['material']in mat and abs(hit['distance_m']-(depth+1))<tol)))
    for i in range(18):
        t=pi*(i+.52)/18
        shoot('Lip around the recessed outer arch',.916*cos(t),5.48+.986*sin(t),['raised limewash'],-.021)
        for cx in (-.447,.447):
            shoot('Raised ring of paired lunette',cx+.437*cos(t),5.51+.429*sin(t),['raised limewash'],.009)
            shoot('Inner frame of paired lunette',cx+.396*cos(t),5.51+.388*sin(t),['dark frame'],.074)
    for i in range(16):
        t=2*pi*(i+.49)/16
        shoot('Raised outer edge of the medallion',.18*cos(t),6.069+.18*sin(t),['raised limewash'],.006)
        shoot('Ring on medallion face',.132*cos(t),6.069+.132*sin(t),['outer ledge'],.044)
    shoot('Plain centre of round medallion',0,6.084,['pale stucco'],.057)
    for x in (-.69,-.35,.35,.69):
        for z,c in ((.95,'dim reflection'),(1.62,'dim reflection'),(3.76,'deep window'),(4.54,'deep window')):
            shoot('Paired recessed rectangular casements',x,z,[c],.134)
        for z in (.63,3.34):
            shoot('Sill projecting in front of the frame',x,z,['outer ledge'],-.094)
    for x in (-.56,-.32,.32,.56):
        shoot('Recessed semicircular glazing',x,5.68,['arched glass'],.111)
    for z in (1.32,1.98,3.67,4.92):
        shoot('Central plaster mullion',0,z,['pale stucco'],-.018)
    for i in range(5):
        x=-.87+i*.348
        for dx,z in ((.13,.472),(.288,.34),(.083,.316),(.173,.388)):
            shoot('Rectangular meander forming the lower frieze',x+dx,z,['incised fret'],-.058)
        shoot('Open field between successive spirals',x+.326,.42,['pale stucco'],-.039)
    for x in (-.52,-.18,.18,.52):
        shoot('Raised edge of the recessed middle panel',x,3.064,['outer ledge'],-.033)
        shoot('Set-back face inside middle label',x,2.82,['pale stucco'],.008)
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
