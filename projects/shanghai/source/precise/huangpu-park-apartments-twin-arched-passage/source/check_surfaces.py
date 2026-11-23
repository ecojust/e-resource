"""Check the two segmental openings, right gate, four-character inscription, brick jambs and balcony rail."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-park-apartments-twin-arched-passage'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    results=[]
    def cast(label,x,z,materials=(),min_distance=0,max_distance=0,origin=None,direction=(0,1,0),length=4.0):
        start=origin or [x,-1.5,z]
        hit=scene.ray(start,list(direction),length)
        passed=hit is None if not materials else bool(hit and hit['material'] in materials and min_distance<=hit['distance_m']<=max_distance)
        results.append(dict(check=label,origin=start,direction=direction,materials=materials,metres=[min_distance,max_distance],hit=hit,passed=passed))
    for x in [-2.93,-2.49,-2.03,-1.68,-1.32,-.93]:
        for z in [.14,.48,1.13,1.65,2.22,2.58]:
            cast('open left street threshold',x,z)
        for y in [.08,.45,.92,1.12]:
            dx=x+1.91;r=2.72**2/(8*.57)+.57/2
            z=3.27-r+(r*r-dx*dx)**.5
            cast('interpolated segmental left soffit',x,z,['soffit plaster'],z-1.35-.045,z-1.35+.018,origin=[x,y,1.35],direction=(0,0,1))
    for x in [1.73+2.61*i/11 for i in [-5,-4,-2,0,2,4,5]]:
        for z in [.39,.71,1.22,1.62,1.98,2.35]:
            cast('recessed iron bars in the right arch',x,z,['painted iron'],1.803,1.879)
    for x in [-3.61,-3.35,-.36,.11,3.38,3.87]:
        cast('granite foot',x,.17,['granite plinth'],1.458,1.484)
        for z in [.52,.83,1.28,1.63,2.08]:
            cast('street red brick piers',x,z,['burnt red brick','dark red brick','brick bed joints'],1.47,1.511)
    for x in [-3.5,-2.81,-2.12,-.42,.48,1.61,2.6,3.70]:
        cast('stone spandrel below the lower inscription ledge',x,3.325,['grey limestone'],1.477,1.500)
        cast('projecting lower inscription ledge',x,3.370,['limestone drip'],1.368,1.379)
        cast('horizontal limestone coping',x,3.97,['limestone drip'],1.251,1.300)
    for side in [-1,1]:
        lo,hi=sorted((side*.59,side*3.48))
        for i in range(7):
            x=lo+(hi-lo)*i/6
            cast('separate balcony iron uprights',x,4.29,['painted iron'],1.558,1.65)
        cast('open gap behind central solid railing break',0,4.27)
    for i,(px,pz) in enumerate([(.34,.87),(.10,.68),(.29,.70),(.50,.61)]):
        x=(i-1.5)*1.13+(px-.5)*.43;z=3.695+(pz-.5)*.405
        cast('raised character '+str(i+1),x,z,['raised inscription'],1.444,1.47)
    cast('455 lane sign enamel backing',.22,2.79,['green lane sign'],1.438,1.46)
    for x in [-4.19,4.19]:
        for z in [.20,1.6,2.8,3.60,4.4]:
            cast('adjacent wall beyond this model',x,z)
    return dict(passed=all(row['passed']for row in results),samples=results)


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
