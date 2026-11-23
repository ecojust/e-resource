"""Independently probe the bank window bay, incised double frets, red piers and upper cornice."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-chekiang-industrial-bank-beijing-front'
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
    def front(label, x, z, allowed, depth_min, depth_max):
        probe(label, [x,-3.,z], [0.,1.,0.], allowed, 3-depth_max, 3-depth_min)

    pale=['light stone facing']
    tiled=['weathered red face tile','thin red grey tile joint']
    glass=['smoky green grey glazing']
    metal=['dark steel sash']
    for sign in (-1,1):
        for z in (.60,2.68,4.42,5.88,8.74,10.86,14.84):
            front('red tiled pier above the retained shop',sign*2.79,z,tiled,.447,.465)
        for z in (3.34,6.94,10.0,12.82):
            front('projecting red band on the pier',sign*2.79,z,['dark red pier course'],.470,.483)
    for x in (-2.02,-1.01,0,1.01,2.02):
        front('large lower glass lights',x,1.06,glass,.135,.145)
    for x in (-1.53,-.51,.51,1.53):
        front('four upright bars of lower window',x,1.19,metal,.258,.269)
    front('bottom window transom',.78,2.01,metal,.269,.281)
    for cx in (-1.25,1.25):
        front('upper ledge of fret panel',cx,4.281,['pale narrow ledges'],.554,.566)
        front('interior raised web between carved grooves',cx+.14,3.67,pale,.518,.53)
        for sign in [-1,1]:
            for offset,z in [(.66,3.23),(.35,3.68),(.60,3.82),(.69,3.66),(.47,3.92),(.83,3.72)]:
                front('angular recessed turn in white stone',cx+sign*offset,z,['shadow in cut stone grooves'],.465,.479)
    for i,(z,high) in enumerate([(4.52,2.16),(7.85,1.92),(10.61,1.86),(13.66,1.88)]):
        for x in [-1.72,0,1.72]:
            front('open triple sash in level '+str(i+3),x,z+high*.30,glass,.128,.143)
            front('transom in each of three window frames',x,z+high*.72,metal,.238,.253)
        for x in [-.83,.83]:
            front('solid pale pier between triple openings',x,z+high*.41,pale,.414,.426)
    for x in (-2.2,0,2.2):
        front('continuous top cornice cap',x,16.16,['weathered grey cornice'],.684,.696)
    for sign in [-1,1]:
        probe('no intrusion into next bank window bay',[sign*3.3,-3,8],[0,1,0],None,0,0)
    probe('no lower shop opening added',[0,-3,-.2],[0,1,0],None,0,0)
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
