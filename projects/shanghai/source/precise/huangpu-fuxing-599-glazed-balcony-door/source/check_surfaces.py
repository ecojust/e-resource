from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-fuxing-599-glazed-balcony-door'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    hits=[]
    def ray(name,x,z,mat,face,tol=.004):
        start=-.45
        hit=scene.ray([x,start,z],[0,1,0],1.1)
        hits.append(dict(feature=name,x=x,z=z,material=mat,expected_distance=face-start,observed=hit,passed=bool(hit and hit['material']==mat and abs(hit['distance_m']-(face-start))<tol)))
    for x in [-.82,-.68,.69,.84]:
        for z in [.38,.85,1.21,1.65,2.18,2.72]:ray('rendered wall',x,z,'cement render',0)
    for x in [-.467,.467]:
        for z in [.45,.92,1.2,1.63,2.36,2.69]:ray('recessed door jamb',x,z,'painted leaf',.126)
    for x in [-.329,-.136,.136,.329]:
        for z in [1.46,1.66,1.90]:ray('lower glazed lights',x,z,'door glass',.201)
        for z in [2.19,2.46,2.73]:ray('upper glazed lights',x,z,'upper glass',.201)
    for x in [-.217,.217]:
        for z in [1.48,1.67,1.91,2.19,2.48,2.73]:ray('fine vertical glazing bars',x,z,'painted leaf',.163)
    for x in [-.23,.23]:
        for z in [.43,.57,.94,1.08]:ray('recessed lower panel',x,z,'panel field',.163)
    for x in [-.3,-.11,.13,.33]:
        ray('broad transom rail',x,2.049,'painted leaf',.135)
        ray('waist rail',x,1.34,'painted leaf',.142)
    for i in range(12):
        x=-1.205+2.271*i/11;r=.014 if i in [0,11] else .0088
        for z in [.41,.68]:
            v=scene.ray([x,-1,z],[0,1,0],.55);hits.append(dict(feature='separate balcony standard',i=i,z=z,observed=v,passed=bool(v and v['material']=='iron' and abs(v['distance_m']-(1-.733-r))<.004)))
        if i<11:
            x+=2.271/22
            v=scene.ray([x,-1,.59],[0,1,0],.53);hits.append(dict(feature='open space between standards',i=i,observed=v,passed=v is None))
    return dict(samples=hits,passed=all(s['passed']for s in hits))

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
