from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-fair-building-dianchi-fluted-capitals'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import pi,sin,cos
    hits=[]
    def cast(label,origin,direction,distance,mat,tol=.005):
        out=scene.ray(origin,direction,1.2)
        hits.append(dict(feature=label,origin=origin,direction=direction,expected_material=mat,expected_distance=distance,observed=out,passed=bool(out and out['material']==mat and abs(out['distance_m']-distance)<tol)))
    for x in [-.89,.89]:
        for i in range(5,16):
            for frac in [.014,.50]:
                a=(i+frac)*2*pi/20
                for z,r,cut,mat in [(.40,.271,.020,'limestone shaft'),(1.005,.275,.0165,'column collar')]:
                    rr=r-cut*sin(pi*frac)**.75
                    cast('fluted surface or ridge',[x+.64*sin(a),-.64*cos(a),z],[-sin(a),cos(a),0],.64-rr,mat)
        for a in [-.49,-.16,.16,.49]:
            cast('round capital',[x+.60*sin(a),-.60*cos(a),1.14],[-sin(a),cos(a),0],.60-.307,'capital stone')
            cast('square abacus',[x+a*.57,-.72,1.29],[0,1,0],.355,'square abacus')
    for x in [-.89,0,.89]:
        for dx in [-.072,0,.072]:
            cast('short recessed channel',[x+dx,-.72,1.67],[0,1,0],.397,'cut channel')
        for dx in [-.142,-.035,.033,.142]:
            cast('frieze face',[x+dx,-.72,1.65],[0,1,0],.370,'frieze face')
    for x in [-1.17,-.66,-.29,.22,.57,1.12]:
        for z,d,mat in [(1.40,-.357,'architrave'),(1.885,-.397,'recessed bed'),(1.985,-.486,'cornice edge')]:
            cast('moulded projection',[x,-.72,z],[0,1,0],.72+d,mat)
    return dict(samples=hits,passed=all(r['passed'] for r in hits))

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
