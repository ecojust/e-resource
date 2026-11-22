from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-overseas-chinese-building-arched-tripartite-window'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    from math import cos,sin,pi
    hits=[]
    def ray(label,x,z,mat,face,tol=.008):
        o=[x,-.6,z];v=scene.ray(o,[0,1,0],1.2)
        hits.append(dict(feature=label,origin=o,expected_material=mat,expected_depth=face,observed=v,passed=bool(v and v['material']==mat and abs(v['distance_m']-.6-face)<tol)))
    for x in [-.31,.313]:
        for z in [.13,.25,.45,.60,.72,1.02,1.22,1.39]:ray('stone mullion',x,z,'grey stone',-.003)
    for x in [-.92,-.71,-.53,-.17,-.09,.10,.17,.53,.68,.85]:
        for z in [.19,.59,.75]:ray('glazed lower light',x,z,'window glass',.137)
        ray('intermediate casement rail',x,.891,'crossbar',.085)
    for x in [-.75,-.58,-.10,.14,.64,.76]:
        ray('glazed arched head',x,1.11,'window glass',.137)
    for i in range(1,9):
        t=i*pi/9
        ray('radial joint behind voussoirs',1.02*1.07*cos(t),.81+.72*1.07*sin(t),'fine mortar',.023)
        u=t+.09
        ray('wedge stone face',1.02*1.15*cos(u),.81+.72*1.15*sin(u),'dressed grey facing',-.006)
    for x in [-1.18,1.16]:
        for z in [.11,.31,.51,.73]:ray('return beside the window',x,z,'dressed grey facing',-.006)
        for z in [.21,.402,.600]:ray('horizontal recessed bed',x,z,'fine mortar',.028)
    for x in [-.93,-.69,-.30,.04,.44,.78,.98]:ray('projected sill',x,-.01,'window ledge',-.16)
    return dict(samples=hits,passed=all(v['passed']for v in hits))

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
