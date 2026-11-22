from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-guangxie-curved-balcony-ironwork'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from iron_circles import xyz,SPACING,HALF,CENTRE,RING,RADIUS,BAYS
    from math import sin,cos,pi
    samples=[]
    def hit(name,s,z,materials=None):
        origin=xyz(s,-.50,z);a=s/RADIUS;direction=[-sin(a),cos(a),0]
        r=scene.ray(origin,direction,1.1)
        samples.append(dict(feature=name,origin=origin,expected=materials or 'open air',observed=r,passed=bool(r and r['material']in materials)if materials else r is None))
    for i in range(BAYS):
        c=-HALF+(i+.5)*SPACING
        for k in range(8):
            a=(k+.5)*pi/4;hit('rolled circular ring',c+RING*cos(a),CENTRE+RING*sin(a),['outer rolled iron'])
        sub=.25*RING+.5*.038
        for q in range(4):
            a=q*pi/2;hit('concave side of iron diamond',c+sub*cos(a)-sub*sin(a),CENTRE+sub*sin(a)+sub*cos(a),['concave iron ornament'])
        for sign in (-1,1):
            hit('square side',c+sign*.049,CENTRE+.018,['cross ties'])
            hit('open between ring and curl',c+sign*.115,CENTRE+.109)
            hit('open inside square',c+sign*.020,CENTRE+.020)
        hit('slender cross tie',c+.122,CENTRE,['cross ties'])
        hit('second top rail',c,.728,['painted iron frame']);hit('top handrail',c,.844,['painted iron frame'])
        hit('ledge front',c,.189,['cast stone coping']);hit('balcony band',c,.061,['edge of balcony slab'])
    for i in range(BAYS+1):hit('upright against open air',-HALF+i*SPACING,.771,['painted iron frame'])
    return dict(passed=all(t['passed']for t in samples),samples=samples)

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
