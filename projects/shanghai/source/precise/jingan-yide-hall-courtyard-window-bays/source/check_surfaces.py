"""Verify the six-pane glass, set-back, sills, face brick, pipe and section limits in all three delivered meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-yide-hall-courtyard-window-bays'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def cast(label,start,direction,maxlen,materials,interval):
        hit=scene.ray(start,direction,maxlen)
        if materials:
            ok=bool(hit and hit['material'] in materials and interval[0] <= hit['distance_m'] <= interval[1])
        else:
            ok=hit is None
        samples.append(dict(check=label,start=start,direction=direction,maxlen=maxlen,
                            expected_materials=materials,expected_distance_m=interval,actual=hit,passed=ok))
    mineral=['ochre facing brick','cream facing brick','weathered facing brick','light mortar']
    for sill in (.94,4.88):
        for x in (-2.15,2.15):
            for dx in (-.36,-.16,.16,.36):
                for dz in (.26,.53,1.05,1.23,1.73):
                    cast('glass set back behind the exterior plane',[x+dx,-.7,sill+dz],[0,1,0],1.05,['dark glass','sky glass'],[.939,.958])
            cast('central metal mullion',[x,-.70,sill+.56],[0,1,0],1.02,['dark metal frame'],[.827,.884])
            for dz in (.34,.74):
                cast('horizontal sash rail',[x+.22,-.70,sill+1.99*dz],[0,1,0],1.01,['dark metal frame','concrete sill edge'],[.824,.885])
            cast('stone sill projects beyond the glass',[x+.18,-.70,sill-.037],[0,1,0],1.,['concrete sill edge'],[.54,.67])
        for x in (-3.87,-3.62,-1.44,-.11,.57,1.39,3.24,3.62):
            for dz in (.48,1.31):
                cast('light brick or visible mortar between windows',[x,-.72,sill+dz],[0,1,0],1.,mineral,[.69,.744])
    for x in [-3.88,-2.09,-1.52,.42,2.15,3.78]:
        cast('unpainted horizontal cement between facing courses',[x,-.70,3.75],[0,1,0],1.,['grey cement'],[.70,.744])
    for z in (.52,2.12,3.69,5.36,7.37):
        cast('continuous narrow rainwater pipe',[-.87,-.7,z],[0,1,0],1.,['weathered downpipe'],[.59,.64])
    for x in [-4.35,4.35]:
        cast('adjacent frontage remains outside modeled bounds',[x,-.80,3.75],[0,1,0],1.5,[],[0,0])
    return dict(passed=all(s['passed']for s in samples),samples=samples)

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
