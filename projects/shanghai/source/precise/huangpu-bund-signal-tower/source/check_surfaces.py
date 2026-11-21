"""Check observable station fabric, signal bands and mast fittings on each delivered mesh."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-bund-signal-tower'
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
    for z,r,finish in [(12.1,1.51,'cream mineral render'),(17.38,1.42,'red brown brick'),(21,1.36,'cream mineral render'),(24.45,1.32,'red brown brick'),(28,1.25,'cream mineral render'),(32.02,1.2,'red brown brick')]:
        probe('shaft at '+str(z)+' metres',[0,12,z],[0,-1,0],[finish],5.65-r-.045,5.65-r+.045)
    for i,z in enumerate([34.08,35.02]):
        probe('signal crown course '+str(i+1),[0,12,z],[0,-1,0],['red brown brick'],4.05,4.44)
    probe('station entrance left glazed leaf',[-.46,-14,1.80],[0,1,0],['smoky window glass'],4.12,4.27)
    probe('register beside doorway',[-1.54,-14,2.76],[0,1,0],['pale register plaque'],3.83,4.03)
    probe('doorway arched fanlight',[.12,-14,3.60],[0,1,0],['smoky window glass'],4.15,4.29)
    probe('station red band',[-2.74,-14,1.30],[0,1,0],['red brown brick'],3.98,4.05)
    probe('station cream stripe',[-2.74,-14,1.63],[0,1,0],['cream mineral render'],3.97,4.07)
    probe('upper station window',[.28,-14,6.06],[0,1,0],['smoky window glass'],4.13,4.38)
    probe('two storey cornice',[1.41,-14,4.44],[0,1,0],['pale dressed stone'],3.25,3.97)
    probe('south plinth',[2.65,-14,.19],[0,1,0],['grey granite'],3.72,4.13)
    probe('station roof',[.78,-4.40,13.2],[0,0,-1],['weathered terrace'],3.23,3.30)
    probe('round lower deck edge',[0,12,10.80],[0,-1,0],['pale dressed stone'],1.70,1.78)
    probe('deck rail',[0,12,11.93],[0,-1,0],['black painted iron'],1.80,1.91)
    probe('signal pole',[0,7.7,42.10],[0,-1,0],['black painted iron'],1.15,1.25)
    probe('rigging before signal pole',[0,10,42.10],[0,-1,0],['black painted iron'],.66,.75)
    probe('transverse yardarm',[2.08,10,44.54],[0,-1,0],['black painted iron'],3.53,3.65)
    probe('mast bracket',[1.26,10,40.38],[0,-1,0],['black painted iron'],3.55,3.67)
    for x,y,z in [(4.62,-3,8),(0,-11.4,6),(4.7,6.35,10.3),(2.9,0,27.10)]:
        probe('open space at '+str((x,y,z)),[x,y,z],[0,0,1],None,0,0,6)
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
