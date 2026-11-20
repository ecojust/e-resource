"""Ray-test the shutters, gable oculus, tiled roof and street-side arcade of the north book repository."""
from argparse import ArgumentParser
from hashlib import sha256
import json
import numpy as np
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-zikawei-north-library'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    results=[]
    def probe(name,origin,delta,length,mat,depth,tol=.04):
        hit=scene.ray(origin,delta,length)
        ok=hit is None if mat is None else bool(hit and hit['material']==mat and abs(hit['distance_m']-depth)<tol)
        results.append(dict(label=name,origin=origin,direction=delta,length=length,expected_material=mat,depth_m=depth,hit=hit,passed=ok))
    # Full-height longitudinal movement from the south arch to the north arch.
    for u in [10.67,11.60,12.43]:
        for z in [.30,1.28,1.84,2.13]:
            probe('clear southern to northern arcade', [u,-1,z],[0,1,0],15.5,None,None)
    for v in [3.19,6.65,10.11]:
        for z in [.19,1.23,1.82,2.29]:
            probe('east roadside arch to hall back wall',[16.1,v,z],[-1,0,0],9.0,'hall interior plaster',16.1-9.69)
    for v in [1.23,4.94,8.38,12.40]:
        probe('solid street pier at chest height',[16.1,v,1.65],[-1,0,0],8,'warm ivory render',16.1-14.04)
        probe('real grey base at each street pier',[16.1,v,.62],[-1,0,0],8,'deep grey plinth',16.1-14.04-.047)
    for u in [0,3.2,-4.5]:
        probe('blank upper east gable',[17.1,6.65+u,6.9],[-1,0,0],8,'warm ivory render',17.1-14.04)
    for y in [.16,13.14]:
        for z,material in [(.75,'deep grey plinth'),(3.70,'warm ivory render'),(6.74,'warm ivory render')]:
            probe('continuous east corner skin',[17.1,y,z],[-1,0,0],8,material,17.1-14.124,.006)
    for x in [-13.87,13.87]:
        probe('continuous courtyard corner skin',[x,-1,6.74],[0,1,0],5,'warm ivory render',.916,.006)
    for height,material,depth in [(9.57,'grey shutter slats',.10),(9.62,'dark vent metal',.19)]:
        probe('round ventilator slats and cavity',[16.1,6.69,height],[-1,0,0],5,material,16.1-14.04+depth)
    for bay in [1,3,4]:
        x=-14.04+(bay+.5)*4.68
        probe('opened courtyard shutter and glass',[x+.20,-1.8,6.06],[0,1,0],4,'deep set glass',2.07)
    for bay in [0,2,5]:
        x=-14.04+(bay+.5)*4.68
        probe('arched courtyard shutter surround',[x+.42,-1.8,5.07],[0,1,0],4,'limestone trim',1.8-.2625)
    for x,y in [(-3.33,2.73),(-3.33,9.42),(4.32,4.62),(4.32,7.70)]:
        peak=6.65;top=8.805+(11.78-8.77+.03)*(1-abs((y-peak)/(peak+.22)))+.015
        probe('sloping roof plane',[x,y,18],[0,0,-1],18,'terracotta roof',18-top)
    for x,y in [(0,-3),(0,16),(17,10),(-17,4)]:
        probe('independent garden, road or existing south building',[x,y,20],[0,0,-1],25,None,None)
    room=scene.tri[scene.mi==scene.materials.index('hall interior plaster')]
    caps=room[(room[:,:,2].min(axis=1)<.02)&(np.ptp(room[:,:,1],axis=1)<.001)]
    ends=[round(float(y),3) for y in np.unique(np.round(caps[:,:,1].mean(axis=1),3))]
    return dict(triangles=len(scene.tri),samples=results,partition_end_planes_m=ends,
                passed=ends==[.13,13.17] and all(r['passed']for r in results))


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
