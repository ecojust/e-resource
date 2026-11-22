from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-zhonghe-cun-no14-channelled-window-pier'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    hits=[]
    def trace(name,origin,direction,material,length,tol=.004):
        hit=scene.ray(origin,direction,length+.08)
        hits.append(dict(feature=name,origin=origin,direction=direction,expected=material,expected_distance=length,observed=hit,passed=bool(hit and hit['material']==material and abs(hit['distance_m']-length)<tol)))
    for i in range(7):
        z=i*.388+.19;mat='warm cement'if i%3==2 else'granite render'
        for x in [-1.21,-1.03,-.84,-.65,-.45]:
            yy=-.387;v=scene.ray([x,-.8,z],[0,1,0],.48)
            hits.append(dict(feature='front face of course',row=i,x=x,observed=v,passed=bool(v and v['material'] in [mat,'weathered grain'] and abs(v['distance_m']-(.8+yy))<.005)))
        for y in [-.27,-.17,-.065,.054]:trace('side face of same course',[.13,y,z],[-1,0,0],mat,.13+.263)
        if i<6:
            zz=(i+1)*.388-.002
            for x in [-1.16,-.77,-.43]:trace('open shadow line in front',[x,-.8,zz],[0,1,0],'recessed joint',.8-.339)
            for y in [-.22,-.076]:trace('joint turns around corner',[.10,y,zz],[-1,0,0],'recessed joint',.10+.312)
    for i in range(3):
        x=.05+i*.671
        for z in [1.22,1.54,2.09,2.33]:trace('upper glazing',[x,-.6,z],[0,1,0],'window glass',.788)
        for z in [.64,.85]:trace('lower glazing',[x,-.6,z],[0,1,0],'translucent lower glass',.786)
        for z in [.984,1.855]:trace('horizontal glazing rail',[x,-.6,z],[0,1,0],'wood muntin',.74)
        for z,y,mat in [(.321,-.005,'lower lip'),(.37,-.031,'cement sill'),(.416,.004,'lower lip'),(.46,-.068,'cement sill')]:trace('projecting sill moulding',[x,-.6,z],[0,1,0],mat,.60+y)
    return dict(samples=hits,passed=all(a['passed']for a in hits))

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
