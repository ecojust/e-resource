from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-yuyuan-541-no2-gabled-bow-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']





def test(scene,role):
    source=runpy.run_path(str(SOURCE/'gable_and_shutters.py'))
    from math import sin,cos,radians
    rows=[]
    def cast(key,point,normal,material,tol=.032):
        start=[x+v*.55 for x,v in zip(point,normal)]
        hit=scene.ray(start,[-v for v in normal],.65)
        rows.append(dict(feature=key,point=point,normal=normal,expected_material=material,hit=hit,passed=bool(hit and hit['material']==material and abs(hit['distance_m']-.55)<tol)))

    for k,(a,c) in enumerate(zip([-54,-26,1,28],[-26,1,28,55])):
        a,c=radians(a),radians(c);t=(a+c)/2;normal=[sin(t),-cos(t),0.]
        for leaf in range(2):
            nc=11 if role=='lod' else 20
            l=a+(.15+.36*leaf)*(c-a);r=l+.335*(c-a)
            for i in range(nc):
                z=.24+(i+.36)*.94/nc
                x=1.82*(sin(l+.028*(c-a))+sin(r-.028*(c-a)))/2
                y=.96-1.82*(cos(l+.028*(c-a))+cos(r-.028*(c-a)))/2
                t2=(l+r)/2
                cast(f'bay {k+1} leaf {leaf+1} blade {i+1}',[x-.039*sin(t2),y+.039*cos(t2),z],[sin(t2),-cos(t2),0.],'shutter blade')
    for xpix in [305,320,348,365]:
        for row in range(3):
            zpix=153-(xpix-298)*.16+row*31
            x,z=source['plane']((xpix,zpix));cast('attic glass',[x,.105,z],[0,-1,0],'attic glass')
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
