from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-xinzha-1378-no17-curved-steel-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']





def test(scene,role):
    source=runpy.run_path(str(SOURCE/'curved_sash.py'))
    from math import sin,cos,radians
    rows=[]
    def cast(key,point,normal,material,tol=.032):
        start=[x+v*.55 for x,v in zip(point,normal)]
        hit=scene.ray(start,[-v for v in normal],.65)
        rows.append(dict(feature=key,point=point,normal=normal,expected_material=material,hit=hit,passed=bool(hit and hit['material']==material and abs(hit['distance_m']-.55)<tol)))

    limits=[100,119,164,218,301,379,461,530,558]
    for i,(u,v) in enumerate(zip(limits,limits[1:])):
        l,r=source['theta'](u),source['theta'](v);t=(l+r)/2;out=[sin(t),-cos(t),0.]
        for j,(base,top) in enumerate([(.17,.82),(.99,1.40)]):
            material='light glass' if (i+2*j)%4==0 else 'quiet glass'
            for k in range(4):
                frac=(k+.6)/4.2;z=base+(top-base)*frac
                a,b=[source['section'](angle,z,-.061)for angle in(l,r)]
                cast(f'sash {i+1} row {j+1}',[(x+y)/2 for x,y in zip(a,b)],out,material)
        for z in [.108,.913,1.48]:
            a,b=[source['section'](angle,z,.004)for angle in(l,r)]
            cast('steel rail',[(x+y)/2 for x,y in zip(a,b)],out,'dark steel')
    for u in [123,157,240,296,328,383,445,503]:
        t=source['theta'](u)
        for z,material,d in [(2.,'render',.022),(.05,'coping',.109)]:
            cast('curved '+material,source['section'](t,z,d),[sin(t),-cos(t),0.],material)
    return dict(samples=rows,passed=all(r['passed']for r in rows))
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
