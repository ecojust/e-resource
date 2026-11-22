from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-hongyu-textile-no443-brass-fan-gate'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    g=runpy.run_path(str(SOURCE/'brass_fan_gate.py'));shapes=json.loads((SOURCE/'ornament-outlines.json').read_bytes());samples=[]
    def t(label,x,z,d,materials):
        hit=scene.ray([x,-1,z],[0,1,0],1.5)
        samples.append(dict(feature=label,x=x,z=z,expected_materials=materials,expected_distance=1+d,actual=hit,passed=bool(hit and hit['material'] in materials and abs(hit['distance_m']-1-d)<.0035)))
    # A reproducible sample of the larger exposed full/LOD face overlaps avoids relying on sub-pixel holes.
    for name,versions in shapes.items():
        full=versions['full'];low=versions['lod'];front=.064 if name=='fan centre' else .070
        def inside(p,t):
            signs=[(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])for a,b in zip(t,[t[1],t[2],t[0]])];return min(signs)>.000001
        lo_tri=[[low['xz'][i]for i in f]for f in low['front']]
        options=[]
        for f in full['front']:
            pts=[full['xz'][i]for i in f];cen=[sum(p[i]for p in pts)/3 for i in range(2)];a,b,c=pts;area=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
            if any(inside(cen,u)for u in lo_tri):options.append((area,cen))
        for _,(x,z) in sorted(options,reverse=True)[:22]:t(name+' raised brass',x,z,front,['antique brass'])
    for a in g['RAYS']:
        for f in [.46,.72]:x,z=g['ellipse'](a,f);t('fan spoke',x,z,.082,['fan iron'])
    for z in [.62,1.16,1.52]:
        for x in [-1.073,-.021,.021,1.073]:t('door frame',x,z,.084,['leaf moulding'])
    for z in [1.74,1.80,2.07]:
        for x in [-.89,-.35,.32,.85]:t('raised door moulding',x,z,.085,['leaf moulding'])
    x,z=g['loc']((205,74));t('wedged arch keystone',x,z,-.135,['lit stone'])
    for uv in [(320,198),(338,201),(321,217)]:x,z=g['loc'](uv);t('green numbered plate',x,z,-.022,['number enamel'])
    return dict(samples=samples,passed=all(item['passed']for item in samples))

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
