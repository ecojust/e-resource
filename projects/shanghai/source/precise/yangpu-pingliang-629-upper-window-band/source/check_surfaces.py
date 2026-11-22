from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='yangpu-pingliang-629-upper-window-band'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    import json
    t=json.loads((SOURCE/'window-measurement.json').read_bytes())
    zero=(t['posts'][0]['sill'][0]+t['posts'][-1]['sill'][0])/2
    corners=[p['sill'][0]-zero for p in t['posts']]
    z=[.24]+[r-2.255+.24 for r in sorted(t['transom_z_over_camera_m'])]+[1.50]
    rows=[]
    def sample(label,x,v,materials,front,y=-.80,tol=.007):
        hit=scene.ray([x,y,v],[0,1,0],2.4)
        ok=bool(hit and hit['material'] in materials and abs(hit['distance_m']-(front-y))<tol)
        rows.append(dict(feature=label,x=x,z=v,expected_front_y=front,hit=hit,passed=ok))
    for i,group in enumerate(t['secondary_mullion_x_m']):
        xs=[corners[i]]+[x-zero for x in group]+[corners[i+1]]
        for x in xs[1:-1]:
            for pz in (.48,.92,1.32):sample('five intermediate steel mullions per bay',x,pz,['dark blue black frame'],-.0405)
        for idx,(x1,x2) in enumerate(zip(xs,xs[1:])):
            x=x1+.44*(x2-x1)
            for zi,(za,zb) in enumerate(zip(z,z[1:])):
                sample('visible divided glazing',x,(za+zb)/2,['lower curtain glass'] if zi==0 else ['glazed sky'],.046)
            for r in z[1:-1]:sample('continuous horizontal steel glazing bars',x,r,['dark blue black frame'],-.042)
    for x in (-1.80,-1.30,-.80,-.30,.20,.70,1.20,1.70):
        sample('projecting brown sill cover',x,.086,['rust brown sill'],-.163)
        sample('red-brown eaves fascia',x,2.0,['soffit brown'],-.312)
        sample('projection on the upper green coping',x,2.39,['cornice green'],-.389)
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
