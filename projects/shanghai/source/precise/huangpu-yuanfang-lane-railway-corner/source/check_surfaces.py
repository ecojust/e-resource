"""Check the two occupied tower faces, blank chamfer, balconies, deep arch openings and upper lights."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-yuanfang-lane-railway-corner'
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
    import math
    for side in ['south','east']:
        def outward(name,u,z,expected,lo,hi):
            ray=([-2.17+u,-2,z],[0,1,0]) if side=='south' else ([2,2.17+u,z],[-1,0,0])
            probe(side+' '+name,*ray,expected,lo,hi)
        for u in [-.42,-.12,.18,.42]:
            for z in [1.27,1.62,2.08]:
                outward('recessed arch passage',u,z,['deep opening shadow'],2.38,2.43)
        for sign in [-1,1]:
            outward('brick archivolt side',sign*.756,1.63,['red arch voussoirs'],1.91,1.96)
            outward('flanking fired brick',sign*1.027,1.34,['red stock brick','brick course shadow'],1.98,2.02)
            outward('balcony corbel',sign*.58,.36,['weathered projecting brick cornice'],1.53,1.59)
            outward('rail end return',sign*.84,.92,['dark wrought iron'],1.35,1.98)
            outward('slender outside railing',sign*.63,.92,['dark wrought iron'],1.36,1.42)
            u=sign*.415+.10
            outward('upper glazed pane',u,3.96,['old blue grey glazing'],2.27,2.34)
            outward('upper horizontal sash',u,4.18,['painted deep red sash'],2.225,2.28)
        outward('upper archivolt head',.15,2.83,['red arch voussoirs','brick course shadow'],1.91,1.96)
        outward('front rail handhold',.10,1.10,['dark wrought iron'],1.35,1.43)
        outward('balcony slab',.10,.62,['weathered projecting brick cornice'],1.33,1.40)
        outward('low belt below lantern',.40,3.29,['weathered projecting brick cornice'],1.79,1.85)
        outward('continuous upper belt cap',.33,3.415,['dark roof coping'],1.72,1.79)
        outward('lantern coping',.40,5.68,['dark roof coping'],1.95,2.03)
    normal=2**-.5
    for z,mats,lo,hi in [(1.48,['red stock brick','brick course shadow'],1.98,2.02),
                         (1.86,['weathered projecting brick cornice'],1.92,1.99),
                         (3.31,['weathered projecting brick cornice'],1.79,1.85),
                         (3.41,['dark roof coping'],1.72,1.79),
                         (4.65,['red arch voussoirs'],2.055,2.12),
                         (5.68,['dark roof coping'],1.95,2.03)]:
        probe('tower flat southeast facet at '+str(z),[-.47+2*normal,.47-2*normal,z],[-normal,normal,0],mats,lo,hi)
    for x,y in [(-1.5,1.5),(-2.3,2.5),(-2.1,1.4)]:
        probe('upper cap from above',[x,y,8],[0,0,-1],['dark roof coping'],2.22,2.26)
    for x,y in [(1.,1.8),(-1.8,-1.),(.25,-.25)]:probe('beyond the upper study',[x,y,8],[0,0,-1],None,0,0)
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
