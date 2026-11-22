from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='pudong-sanlin-academy-east-triple-arched-windows'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene, role):
    samples=[]
    def forward(x,z,materials,low,high,part):
        origin=(x,-1,z)
        hit=scene.ray(origin,(0,1,0),3.)
        passed=bool(hit and hit['material'] in materials and low<=hit['distance_m']<=high)
        samples.append(dict(feature=part,origin=origin,direction=[0,1,0],expected_material=materials,distance_bounds_m=[low,high],hit=hit,passed=passed))
    for c in (-2.12,0,2.12):
        for x in (-.365,-.129,.131,.363):
            for z in (.28,.60,.91,1.26):
                forward(c+x,z,['window glass','shaded glass'],1.143,1.146,'one of sixteen individually framed lower lights')
        for z in (.29,.61,.92,1.26):
            forward(c,z,['sash edge'],1.062,1.066,'central meeting stile')
            for dx in (-.246,.246):
                forward(c+dx,z,['muntin'],1.062,1.066,'thin lower muntin')
        for x in (-.39,.39):
            for z in (.434,.755,1.080):
                forward(c+x,z,['muntin'],1.077,1.081,'three lower transverse rails')
        for dx,z in ((-.106,1.710),(.106,1.710),(-.106,1.609),(.106,1.609)):
            forward(c+dx,z,['muntin'],1.071,1.075,'transom diamond')
        for dx,z in ((-.32,1.76),(.32,1.76),(-.12,1.79),(.12,1.79),(0,1.66)):
            forward(c+dx,z,['window glass'],1.141,1.147,'clear glass around and inside the diamond')
        for dx in (-.675,.675):
            for z in (1.20,1.38,1.53):
                forward(c+dx,z,['red brick','lighter red brick','russet bedding'],.980,.991,'shoulder courses')
        for sign in (-1,1):
            for dx,z in ((.12,2.19),(.38,2.095),(.64,1.80)):
                forward(c+sign*dx,z,['red brick','dark red brick','lighter red brick','russet bedding'],.980,.990,'red brick arch following measured pointed profile')
        for dx in (-.20,.20):
            forward(c+dx,.064,['pale sill'],.923,.927,'projecting stone sill')
    return dict(samples=samples,passed=all(s['passed']for s in samples))

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
