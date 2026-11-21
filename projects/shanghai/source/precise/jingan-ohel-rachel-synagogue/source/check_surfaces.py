"""Check the east portico, Ionic shafts, recessed portal, gable glazing and long side windows on each delivered mesh."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-ohel-rachel-synagogue'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples = []
    def probe(label, origin, direction, material, minimum, maximum, length=30):
        hit = scene.ray(origin,direction,length)
        valid = hit is None if material is None else (hit is not None and
                hit['material'] in material and minimum <= hit['distance_m'] <= maximum)
        samples.append(dict(label=label,origin=origin,direction=direction,allowed=material,
                            expected_distance_m=[minimum,maximum],hit=hit,passed=valid))
    stone='warm weathered ashlar';trim='carved pale stone';glass='smoky glazing'
    def front(label,x,z,materials,a,b):probe(label,[x,-17,z],[0,1,0],materials,a,b)
    def side(label,y,z,materials,a,b):probe(label,[13,y,z],[-1,0,0],materials,a,b)
    for x in [-1.86,1.86]:
        front('free-standing Ionic shaft '+str(x),x,3.35,[trim],3.65,3.86)
        front('flared Ionic base '+str(x),x,.35,[trim],3.54,3.68)
        front('square abacus '+str(x),x,7.27,[trim],3.57,3.78)
    for x in [-5.93,5.93]:
        front('front oculus '+str(x),x,5.94,[glass],3.95,4.08)
        front('oculus surround '+str(x),x+.73,5.94,[trim],3.46,3.76)
        front('front lower glazing '+str(x),x+.23,2.35,[glass],4.03,4.23)
        front('lower window sill '+str(x),x,.70,[trim],3.47,3.66)
    front('timber double door',.24,1.55,['dark timber door'],6.22,6.43)
    front('door fanlight',.26,3.40,[glass],6.22,6.43)
    front('raised stone cartouche',.14,5.20,[trim],5.81,6.03)
    front('parapet rail',0,9.30,[trim],3.46,3.69)
    front('gable fanlight',.39,9.83,[glass],6.80,7.03)
    for y in [-8.13,-4.065,0,4.065,8.13]:
        side('lower side glazing '+str(y),y+.17,1.74,[glass],4.40,4.57)
        side('lower frame transom '+str(y),y+.17,1.47,['charcoal metal tracery'],4.24,4.35)
        side('upper arched side glazing '+str(y),y+.19,5.54,[glass],4.41,4.57)
    for x in [-4.5,4.5]:probe('roof pitch '+str(x),[x,2.13,17],[0,0,-1],['weathered terracotta tile'],6.42,6.61)
    probe('entrance behind the freestanding columns',[.65,-15,2.55],[0,1,0],None,0,0,3.53)
    probe('above low forecourt floor',[0,-12.15,1.65],[0,0,1],None,0,0,3.75)
    probe('clear beside the southern wall',[-10.35,0,.50],[0,0,1],None,0,0,12)
    return dict(passed=all(row['passed'] for row in samples),samples=samples)


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
