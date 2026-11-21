"""Independently probe the chamfer windows, both balustrades, the bowed balcony and its roof dormer."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-hardoon-building-chamfer'
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

    for side in [-1,1]:
        front('lower arch recessed glazing', side*.61, 1.37, ['recessed grey glass'], .065,.085)
        front('lower broad white surround', side*1.68, 1.67, ['weathered pale masonry'], .435,.458)
        front('lower iron outer rail', side*1.15, .97, ['dark balcony iron'], .65,.69)
        front('middle balcony door glass', side*.39, 4.20, ['recessed grey glass'], .065,.085)
        front('middle balcony door transom', side*.43, 4.69, ['deep red painted window joinery'], .12,.145)
        front('paired stone brackets beneath balcony', side*.91, 2.4, ['stone ledges and shade'], .69,.73)
        front('upper arch at spring', side*.91, 7.89, ['ochre red dormer and arch'], .44,.48)
        front('upper arched glass', side*.34, 7.44, ['recessed grey glass'], .065,.085)
        front('dormer recessed paired sash', side*.28,10.68, ['recessed grey glass'], -.23,-.19)
        front('tall pale dormer pilaster',side*1.22,11.28,['weathered pale masonry'],.28,.32)
        front('dormer pilaster capital',side*1.22,12.13,['stone ledges and shade'], .35,.385)
        front('moulded pediment shoulder',side*1.49,12.31,['ochre red dormer and arch'], .375,.407)
        for z in [2.43,5.55,7.63,8.65]:
            front('grey end pier',side*2.15,z,['grey pressed brick','light grey bed joint'],.383,.408)
    for z in [1.38,4.15,7.30]:
        front('mullion through a real wall opening',0,z,['deep red painted window joinery'],.12,.145)
    front('wide opening arch crown',0,2.17,['stone ledges and shade','weathered pale masonry'],.43,.51)
    front('middle square-headed brick eye',.4,5.49,['grey pressed brick','light grey bed joint'],.383,.408)
    front('arch crown, upper red band',0,8.83,['ochre red dormer and arch'],.44,.48)
    front('crowning stone rim on the arch',0,8.92,['weathered pale masonry'],.477,.51)
    for z in [2.78,2.95,3.08,3.64]:
        front('outer edge of convex balcony',0,z,['weathered pale masonry','stone ledges and shade'],.985,1.125)
    for x in [-.54,.54]:
        front('upper low balustrade',x,6.80,['weathered pale masonry'],.71,.76)
    front('roof cornice capping',0,9.49,['dark roofing edge'],.62,.66)
    front('dormer central opening mullion',0,10.70,['deep red painted window joinery'],-.12,-.09)
    front('splayed center rib at top of dormer',0,12.0,['weathered pale masonry'],.25,.28)
    front('curved pediment at crown',0,13.02,['weathered pale masonry'],.28,.325)
    for x in [-1.15,0,1.15]:
        probe('physical top lip from above', [x,0.,15], [0,0,-1], ['roof ridge lip','stone ledges and shade','weathered pale masonry'], 1.76,2.35)
    for sign in (-1, 1):
        # A normal through each junction must meet masonry all the way from
        # the second storey to the dentilled cornice, with no open sky slit.
        normal=[sign*.382683,-.923880,0.]
        for z in (1.37,4.48,7.67,9.48):
            vertex=[sign*2.51157,0,z]
            origin=[vertex[i]+2*normal[i] for i in range(3)]
            materials=['dark roofing edge'] if z>9.4 else ['grey pressed brick','light grey bed joint']
            interval=[1.23,1.39] if z>9.4 else [1.48,1.65]
            probe('mitred return through the outer turn',origin,[-t for t in normal],materials,*interval)
    for x in [-4.8,4.8]:
        probe('outside both short returns',[x,-3.,6.3],[0,1,0],None,0,0)
    probe('ground-floor retail stays below the study',[0,-3.,-.40],[0,1,0],None,0,0)
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
