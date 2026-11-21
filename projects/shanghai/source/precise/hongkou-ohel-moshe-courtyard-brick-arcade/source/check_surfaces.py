from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-ohel-moshe-courtyard-brick-arcade'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import sin,cos,acos
    pitch=3.08;half=(pitch-.762)/2;rise=.36;radius=(half**2+rise**2)/(2*rise);sz=2.53;cz=sz+rise-radius;theta=acos((sz-cz)/radius)
    rows=[]
    def probe(label,x,z,material=None,front=None,reverse=False):
        origin=[x,1.4 if reverse else -1.,z];direction=[0,-1 if reverse else 1,0];hit=scene.ray(origin,direction,2.4)
        ok=hit is None if material is None else bool(hit and hit['material'] in material and (front is None or abs(hit['distance_m']-(1+front))<.025))
        rows.append(dict(check=label,origin=origin,direction=direction,expected_material=material,expected_front=front,hit=hit,passed=ok))
    reds=['red header','orange brick','shadow red'];blues=['blue brick','ash brick','slate brick','buff mortar']
    for i,c in enumerate([-pitch,0.,pitch],1):
        for x in [-.81,-.45,0,.45,.81]:
            for height in [.22,.9,1.7,2.32]:
                probe(f'Bay {i} clear through the front face',c+x,height)
        for a in [-.755,-.55,-.27,.11,.31,.622,.82]:
            t=a*theta
            for offset,depth,label in [(.043,-.022,'inner rowlock'),(.174,-.060,'outer soldiers')]:
                probe(f'Bay {i} {label}',c+(radius+offset)*sin(t),cz+(radius+offset)*cos(t),reds,depth)
        # Both LODs retain the recessed joint at these two radial angles.
        for a in [-.2,.2]:
            t=a*theta
            for offset in [.043,.174]:
                probe(f'Bay {i} recessed mortar joint',c+(radius+offset)*sin(t),cz+(radius+offset)*cos(t),['red mortar'],.018)
        for x in [-.38,.06,.42]:probe(f'Bay {i} open near intrados',c+x,sz+.25)
        probe(f'Bay {i} back of solid ring',c+.06,sz+rise+.14,['red mortar','red header','orange brick','shadow red'],reverse=True)
    for n in range(4):
        c=(n-1.5)*pitch
        for offset in [-.225,.04,.18]:
            for row in [2,4,6,13,15,24]:
                z=.25+(row+.5)*(sz-.25)/32;probe('Blue stretcher face',c+offset,z,blues,0.)
            for row in [8,9,18,19]:probe('Red bonding course',c+offset,.25+(row+.5)*(sz-.25)/32,reds,0.)
            probe('Red-brick impost with projecting lip',c+offset,sz-.069,reds,-.108)
            probe('Raised lower plinth',c+offset,.20,reds,-.100)
    for x in [-4,-3,-2,-1,0,1,2,3,4]:probe('Continuous gallery cap',x,3.607,['cap stone'],-.077)
    return dict(passed=all(x['passed'] for x in rows),samples=rows)


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
