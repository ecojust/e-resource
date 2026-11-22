from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='changning-yuanpei-building-brick-corner'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    rows=[]
    def check(side,kind,u,z,material,depth):
        origin,direction=([u,-.7,z],[0,1,0]) if side=='long' else ([.7,u,z],[-1,0,0])
        hit=scene.ray(origin,direction,1.5)
        rows.append(dict(label=side+' '+kind,origin=origin,direction=direction,expected_material=material,
                         expected_distance_m=.7+depth,observed=hit,passed=bool(hit and hit['material']==material and abs(hit['distance_m']-.7-depth)<.001)))
    for side,centres,xs in [('long',[-3.28,-1.32],[-3.94,-2.55,-.68]),('return',[1.08],[.31,1.81])]:
        for u in xs:
            for z0,z1,depth,mat in [(2.66,2.715,-.08,'cornice shadow'),(2.714,2.881,-.112,'pale masonry'),(2.88,2.953,-.161,'pale masonry'),(2.951,3.095,-.196,'roof fascia'),(3.09,3.13,-.215,'gutter and pipe')]:
                check(side,'stepped cornice',u,(z0+z1)/2,mat,depth)
        for c in centres:
            for z in (.72,1.04,1.44,1.85,2.22,2.36):
                for dx in (-.4,-.21,.19,.39):check(side,'recessed pane',c+dx,z,'window glass',.147)
                check(side,'centre muntin',c,z,'window metal',.092)
                check(side,'light jamb',c+.605,z,'pale masonry',-.018)
            for dx in (-.4,-.205,.17,.376):
                check(side,'transom',c+dx,2.012,'window metal',.080)
                check(side,'stone sill',c+dx,.541,'pale masonry',-.087)
    for side,lo in [('long',-4.28),('return',0)]:
        for j in (1,2,3,4,5):
            for i in (2,4,6):
                start=lo-(.126 if j%2 else 0)+i*.253
                colour=('brick russet','brick burnt','brick ochre')[(i*31+j*17+j//4)%3]
                if side=='return' and abs(start+.12-.475)<.032:
                    check(side,'vertical strip ahead of brick and mortar',start+.12,j*.075+.036,'pale masonry',-.018)
                    check(side,'vertical strip across bed joint',start+.12,j*.075+.0745,'pale masonry',-.018)
                    continue
                check(side,'bonded brick face',start+.12,j*.075+.036,colour,0)
                check(side,'recessed lime bed',start+.12,j*.075+.0745,'lime joint',.013)
    for z in (.22,.76,1.2,1.64,2.4):
        check('long','outside rainwater conductor',-.23,z,'gutter and pipe',-.151)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)

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
