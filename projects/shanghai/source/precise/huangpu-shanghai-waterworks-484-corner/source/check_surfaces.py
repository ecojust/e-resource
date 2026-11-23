"""Independently probe the filled cartouche borders, its empty centre, recessed sash and sloping roof."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-shanghai-waterworks-484-corner'
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

    stucco=['light grey ruled stucco','recessed grey joint']
    stone=['pale carved stone']
    strip=['shadowed stone moulding']
    for x in (-2.62,-2.11,2.11,2.62):
        for z in (1.85,3.76,5.77,8.83,10.12):
            front('horizontal ruled wall beyond decoration',x,z,stucco,.415,.432)
    for x in (-.98,-.43,0,.43,.98):
        front('blank inset central field',x,2.3,['light grey ruled stucco'],.454,.463)
        front('top and bottom square bead',x,.912,stone,.543,.555)
    for sign in (-1,1):
        front('upright of rectangular field',sign*1.37,2.35,stone,.543,.556)
        front('flared horn binding',sign*1.11,6.02,strip,.619,.637)
        front('bottom horn curls',sign*.66,4.86,stone,.522,.688)
        front('dark outside window frame',sign*.986,8.67,['dark green grey sash'],.26,.276)
        for x in (.25,.74):
            front('real inset glass behind rectangular opening',sign*x,8.6,['smoky recessed glazing'],.137,.151)
        front('vertical window bars',sign*.52,8.89,['dark green grey sash'],.245,.255)
        front('window moulded surround',sign*1.078,8.55,stone,.464,.478)
        front('projecting stone sill',sign*.61,7.42,stone,.605,.619)
        front('roof-edge projecting flashing',sign*2.13,11.25,['dark weathered flashing'],.765,.775)
    front('cartouche lower stone knot',0,4.89,stone,.620,.638)
    front('hollow inside of carved stone loop',0,5.91,stucco,.417,.425)
    front('crowned flower centre',0,6.94,strip,.678,.695)
    front('central upright of sash',0,8.8,['dark green grey sash'],.245,.255)
    front('cornice front material',0,11.1,['dark weathered flashing'],.694,.705)
    roof=['warm red roof tile','terracotta tile bead']
    for x in (-1.6,-.8,0,.8,1.6):
        probe('red tile face from overhead',[x,-.25,15],[0,0,-1],roof,3.05,3.17)
        probe('upper roof face from overhead',[x,.29,15],[0,0,-1],roof,2.30,2.46)
    for sign in (-1,1):
        probe('cut face ends before next window',[sign*3.50,-3,7.8],[0,1,0],None,0,0)
    probe('building ground floor beyond scope',[0,-3,-.35],[0,1,0],None,0,0)
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
