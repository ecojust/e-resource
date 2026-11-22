from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-jingcun-lane-36-east-scroll-gate'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def face(label,x,z,materials,y0=-.48,depth=None):
        v=scene.ray([x,y0,z],[0,1,0],.8)
        ok=bool(v and v['material'] in materials) if materials else not v
        if depth is not None:ok=ok and abs(v['distance_m']-(depth-y0))<.003
        samples.append(dict(feature=label,x=x,z=z,expected=list(materials),observed=v,passed=bool(ok)))
    for x in [-.8,.8]:
        for z in [.12,.37,.73,1.22,1.53,1.96,2.28]:face('one full-height stile',x,z,{'black painted frame'},depth=-.045)
    for z in [.055,.272,1.155,1.292,1.431,2.078,2.302]:
        for x in [-.68,-.34,0,.34,.68]:face('through horizontal',x,z,{'black painted frame'},depth=-.032)
    for i in range(4):
        x=-.59+.392*i
        for z in [.37,.68,.92,1.54,1.86]:
            for s in [-1,1]: face('border of scroll insert',x+s*.107,z,{'dark iron strip'},depth=-.019)
        for za,zb,n in [(.29,1.14,4),(1.453,2.052,3)]:
            for j in range(n):
                z=za+(j+.52)*(zb-za)/n
                face('open centre of eye',x,z,set());face('bronze ring side',x+.045,z,{'bronze scroll'})
    for x in [-.6375+.255*i for i in range(6)]:
        face('top ring open centre',x,2.19,set());face('gilded top rail',x+.075,2.19,{'aged gilding'})
    for i in range(7):
        x=-.654+i*.218
        face('open point on top',x,2.403,{'dark iron strip'})
        face('daylight between spearheads',x+.06,2.403,set())
    return dict(passed=all(q['passed'] for q in samples),samples=samples)

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
