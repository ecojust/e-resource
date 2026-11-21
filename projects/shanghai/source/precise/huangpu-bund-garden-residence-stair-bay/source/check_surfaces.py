"""Independently probe the eight staggered steel windows, brick returns, pale quoins and head coping."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-bund-garden-residence-stair-bay'
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

    brick=['burgundy face brick','warm grey brick joint']
    stone=['cream stair bay dressing']
    steel=['painted dark steel']
    glass=['grey olive glazing']
    cap=['weathered stone cap']
    datum=2.75
    # These centres and elevations were digitised from the registered field image.
    axes=[-.80,-.26,.26,.78]
    widths=[.403,.390,.403,.409]
    heights=[1.70,1.68,1.67,1.64]
    for row,heads in [('upper',[9.08,8.80,8.50,8.17]),('lower',[5.61,5.34,5.07,4.79])]:
        for axis,width,h,head in zip(axes,widths,heights,heads):
            base=head-h-datum
            for side in [-1,1]:
                for fraction in [.14,.32,.52,.72,.90]:
                    front(row+' recessed glass',axis+side*width*.25,base+h*fraction,glass,.135,.145)
            front(row+' vertical steel member',axis,base+h*.51,steel,.178,.190)
            for fraction in [.21,.42,.61,.80]:
                front(row+' steel rail',axis+.095,base+h*fraction,steel,.178,.190)
            front(row+' integral sill',axis,base-.019,cap,.334,.345)
            front(row+' dressed jamb',axis+width/2+.035,base+h*.33,stone,.291,.306)
    for z in [3.05,4.40,5.45,6.49,7.53]:
        for side in [-1,1]:
            front('retained brick shoulder',side*1.61,z-datum,brick,.215,.230)
    for z in [3.01,3.79,4.58,5.37,6.13,6.93,7.72]:
        for side in [-1,1]:
            front('projecting quoin',side*1.30,z-datum,stone,.293,.305)
    for x in [-.80,-.31,.14,.78]:
        front('continuous stone cap',x,9.50-datum,cap,.360,.370)
    front('central wall between window flights',.01,6.57-datum,stone,.293,.305)
    for z in [-.16,6.99]:
        probe('retained floor or roof', [0,-3,z], [0,1,0],None,0,0)
    for x in [-1.91,1.91]:
        probe('retained other side of wall', [x,-3,4], [0,1,0],None,0,0)
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
