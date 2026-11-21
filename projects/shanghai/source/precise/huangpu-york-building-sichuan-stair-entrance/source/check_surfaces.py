"""Independently probe the three staircase window strips, readable title, number plate and recessed gate."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-york-building-sichuan-stair-entrance'
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

    for v in [-.94,0.0,.94]:
        for px in [36.,84.,128.,173.,213.,260.,302.,346.,392.,442.,487.,539.,579.,626.,678.,722.]:
            z=23.65-px/740*(23.65-6.50)
            for direction in [-1.,1.]:
                front('stair glazing',v+direction*.172,z,['cool grey stair glass','black staircase steel'] if v==-.94 else ['cool grey stair glass'],-.145,.26 if v==-.94 else -.135)
            front('central vertical steel',v,z,['black staircase steel'],-.107,-.055)
        for px in [16,59,103,147,191,241,281,326,374,418,464,510,557,603,650,699]:
            front('black horizontal transom',v+.142,23.65-px/740*17.15,['black staircase steel'],-.097,-.05)
    for v in [-.47,.47]:
        for z in [7.1,11.3,16.1,21.9,23.71]:
            front('cream piers',v,z,['pale cornice'],.105,.118)
    for x in [-1.48,-.74,0.,.74,1.48]:
        front('iron frame in the deep closed doorway',x,2.39,['green painted gate'],-.444,-.422)
    for x in [-1.38,-.64,.10,.84]:
        front('dark closure behind the vertical bars',x,1.32,['dark inner door'],-.494,-.482)
    for x in [-1.25,-.85,-.51,-.19,.20,.57,.91,1.30]:
        front('eight entrance transom lights',x,4.56,['cool grey stair glass'],-.229,-.214)
    for x in [-1.06,-.70,-.34,.015,.38,.74,1.10]:
        front('overlight upright',x,4.52,['black staircase steel'],-.180,-.165)
    for x in [-2.69,2.54]:
        for z in [1.32,3.82,5.48]:
            front('scored outer stone doorframe',x,z,['ivory grooved render','pale cornice'],.069,.111)
    front('green 29 plate',1.62,3.20,['green address enamel'],.107,.118)
    front('ivory title-panel background',0.,3.93,['pale cornice'],.095,.108)
    for x in [-2.66,-1.31,0.,1.31,2.66]:
        front('portal head',x,6.25,['pale cornice'],.167,.180)
    for x,z in [(-3.15,1.83),(3.15,1.83),(-1.85,13.),(1.85,13.),(0.,24.2)]:
        probe('boundary of photographed facade portion',[x,-3,z],[0,1,0],None,0,0)
    # The first-hit shape and relative position must independently recover each gold
    # character and both white address digits. No letters are inferred from mesh names.
    glyphs=[('金',-1.115,-.63,3.42,3.72),('陵',-.57,-.09,3.42,3.72),('大',.03,.50,3.42,3.72),('樓',.63,1.115,3.42,3.72),
            ('2',1.66,1.75,3.16,3.259),('9',1.76,1.849,3.16,3.259)]
    for label,x0,x1,z0,z1 in glyphs:
        expected='old gold letters' if x0<1.5 else 'white enamel numerals'
        found=[]
        for iz in range(7):
            for ix in range(9):
                x=x0+(x1-x0)*(ix+.5)/9
                z=z0+(z1-z0)*(iz+.5)/7
                hit=scene.ray([x,-3.,z],[0.,1.,0.],5.)
                if hit and hit['material']==expected:found.append([x,z])
        samples.append(dict(label='raised glyph '+label,sampled=63,hits=len(found),first_hits=found,passed=len(found)>=3))
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
