from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-fushi-garden-faceted-loggia'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from garden_loggia import WIDTH,ARCH,CENTRES
    rows=[]
    def check(label,x,z,mat,y):
        h=scene.ray([x,-.62,z],[0,1,0],2.9)
        rows.append(dict(label=label,origin=[x,-.62,z],direction=[0,1,0],expected_material=mat,expected_distance_m=.62+y,observed=h,passed=bool(h and h['material']==mat and abs(h['distance_m']-(.62+y))<.002)))
    for x in [-1.64,-1.34,-1.03,-.56,-.24,.19,.47,.96,1.31,1.62]:
        check('upper plaster face',x,2.626,'roughcast',0)
        check('projecting gallery threshold',x,.107,'cast sill',-.055)
        check('handrail front',x,1.092,'rail iron',.076)
    for c in CENTRES:
        check('slender iron upright',c,.526,'rail iron',.093)
        for sign in (-1,1):
            check('lower frond',c+sign*.0035,.958,'rail iron',.093)
    for x in (-.845,.875):
        for u in (-.44,-.146,.145,.435):
            for z in (1.26,1.43,1.73,1.89):
                check('glass beyond guard and gallery',x+u,z,'shadowed glass',1.413)
        for z in (1.24,1.41,1.80):
            for dx in (-.281,0,.281):check('rear sash upright',x+dx,z,'sash joinery',1.323)
    for x,z in ((-.061,1.4),(.032,1.78),(.073,2.19),(-1.6,2.12)):
        check('recessed rear wall',x,z,'window render',1.302)
    for (x0,z0),(x1,z1) in zip(ARCH,ARCH[1:]):
        x=(x0+x1)/2;z=(z0+z1)/2;check('actual polygonal arch over opening',x,z+.02,'roughcast',0)
    return dict(passed=all(row['passed'] for row in rows),samples=rows)

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
