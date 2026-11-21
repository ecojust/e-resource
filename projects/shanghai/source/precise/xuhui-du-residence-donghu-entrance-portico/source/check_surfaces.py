from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-du-residence-donghu-entrance-portico'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




"""Test the carved address pier, the free passage on its left and the adjoining wall."""
"""Check the real column positions, covered passage, soffit and open stone balustrade."""
def test(scene):
    rows=[]
    def ray(label,start,direction,maximum,material=None,expected=None,tolerance=.035):
        hit=scene.ray(start,direction,maximum)
        passed=(hit is None) if material is None else bool(hit and hit['material'] in material and abs(hit['distance_m']-expected)<=tolerance)
        rows.append(dict(check=label,origin=start,direction=direction,maximum_m=maximum,acceptable_material=material,
                         expected_distance_m=expected,tolerance_m=tolerance,hit=hit,passed=passed))
    for x in [-3.49,3.49]:
        for y in [-7.06,-.58]:
            for z,radius in [(.055,.496),(.138,.470),(.30,.469),(.39,.415),(1.04,.352),(2.71,.343),(4.71,.316),(4.94,.393)]:
                ray('Round column and its moulded foot', [x,y-.83,z],[0,1,0],1.9,['warm limestone'],.83-radius,.05)
                ray('Column shaft from the side', [x-.83,y,z],[1,0,0],1.9,['warm limestone'],.83-radius,.05)
            ray('Square capital above the shaft',[x,y-.85,4.993],[0,1,0],1.8,['light cap stone'],.85-.465)
    for x in [-2.72,-1.48,0,1.48,2.72]:
        for y in [-7.20,-5.2,-3.45,-1.3]:
            ray('Underside of the projecting canopy',[x,y,1.70],[0,0,1],5,['canopy soffit'],5.005-1.70,.015)
        for z in [.13,1.60,2.25,4.65]:
            ray('Walk through between the posts',[x,-8.10,z],[0,1,0],7.98)
    for x in [-3.68,-2.73,0,1.37,3.54]:
        for y in [-7.38,-3.69,-.28]:
            ray('Weathered canopy roof inside the parapet',[x,y,7.5],[0,0,-1],3,['weathered roof'],7.5-5.535,.015)
    for x in [-3.65,0,3.65]:
        ray('Stone cross in parapet',[x,-8.40,6.02],[0,1,0],1.75,['light cap stone'],8.4-7.68-.035,.05)
    for x in [-3.17,-2.49,-1.21,.51,2.08,3.39]:
        ray('Continuous street edge of the upper rail',[x,-8.40,6.416],[0,1,0],1.75,['warm limestone','light cap stone'],8.4-7.68-.061,.055)
    for x in [-4.91,4.91]:
        for z in [.2,2.75,5.01,6.41]:
            ray('Beyond the photographed portico',[x,-8.1,z],[0,1,0],8.2)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)

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
