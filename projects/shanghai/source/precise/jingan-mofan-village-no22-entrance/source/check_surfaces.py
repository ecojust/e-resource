"""Probe the real openings, window, ironwork and address plate in the three published meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-mofan-village-no22-entrance'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,start,direction,length,materials,span=None):
        hit=scene.ray(start,direction,length)
        ok=hit is None if not materials else bool(hit and hit['material']in materials and (not span or span[0]<=hit['distance_m']<=span[1]))
        rows.append(dict(test=label,origin=start,direction=direction,maximum_m=length,
                         expected_materials=materials,expected_distance_m=span,hit=hit,passed=ok))
    front=lambda label,x,z,mat,span:ray(label,[x,-.75,z],[0,1,0],1.7,mat,span)
    for x in [.795,1.04,1.29,1.445]:
        for z in [.20,.88,1.64,1.97]:
            front('walk through the open entrance',x,z,[],None)
        ray('light doorstep in the recessed passage',[x,.44,1],[0,0,-1],1.3,['light buff entrance terrazzo'],[.92,.93])
    for x in [-1.72,.19,.55,1.78]:
        for z in [.205,1.34,2.90]:
            front('solid wall above or below openings',x,z,['grey painted plinth' if z<.25 else 'warm white lime render'],[.70,.756])
    for x in [-1.37,-.87,-.32]:
        front('recessed window pane between bars',x,1.407,['window glass in shadow'],[.89,.925])
    for x in [-1.33156,-.85023,-.36889]:
        front('projecting red guard in front of the glass',x,1.407,['dark red painted wood'],[.777,.808])
    for x in [.305,.393]:
        front('cream raised numeral on the green plate',x,1.955,['cream numerals'],[.715,.73])
    ray('letter slot on the side return',[1.20,.43,1.312],[-1,0,0],.6,['patinated iron'],[.46,.49])
    for x in [-1.033333,-.506667]:
        front('recessed red sash junction',x,1.407,['dark red painted wood'],[.81,.84])
    for x in [-1.3,-.70,-.14]:
        front('stone sill projects in front of the wall',x,.809,['light buff entrance terrazzo'],[.64,.68])
    for z in [1.903,2.028]:
        front('green enamel border',.37,z,['green enamel address plate'],[.717,.735])
    for x in [1.115,.906,1.324]:
        front('physical iron transom or oval',x,2.435 if x==1.115 else 2.628,['patinated iron'],[.738,.824])
    for x,z in [(.750,2.437),(1.003,2.457),(1.230,2.441),(1.460,2.456)]:
        front('open space in the diamond and oval transom',x,z,[],None)
    front('right jamb separates gate from adjoining unit',1.544,1.60,['patinated iron'],[.71,.76])
    for x,z in [(-1.96,2),(.38,3.20),(1.98,1.8)]:
        front('adjacent units and upper floor are outside this bounded model',x,z,[],None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed']for r in rows))


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
