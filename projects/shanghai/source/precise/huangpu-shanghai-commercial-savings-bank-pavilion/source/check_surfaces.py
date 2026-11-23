"""Probe the individual tile roofs, returned eaves, glass lights, frames and ridge openings."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-shanghai-commercial-savings-bank-pavilion'
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

    glass=['recessed blue grey glazing']; frame=['brown red sash'];red=['deep red timber'];ridge=['warm grey ridge relief']
    tiled=['weathered green glazed pans','blue-green glazed roll caps','warm grey ridge relief']
    def street(label,x,z,materials,lower,upper):
        probe(label,[x,-12.,z],[0.,1.,0.],materials,lower,upper)
    for cx in (-4.18,-1.39,1.39,4.18):
        for x in [cx-.81,cx-.39,cx+.39,cx+.81]:
            for z in (3.31,3.84):
                street('front paired glazing lights',x,z,glass,9.449,9.463)
        for x in (cx-1.14,cx+1.14):
            street('fixed side frames of sash',x,3.33,frame,9.402,9.416)
    for x in (-5.57,-2.79,0,2.79,5.57):street('structural front upright',x,3.50,red,9.326,9.345)
    for x in (-5.8,-3.2,-1.3,1.3,3.2,5.8):
        for y in (-3.08,3.08,-1.25,1.25):
            probe('upper roof ceramic surfaces',[x,y,12],[0,0,-1],tiled,5.40,7.74)
    for x in (-5.8,-2.0,2.0,5.8):
        for y in (-4.25,4.25):
            probe('separate lower eaves',[x,y,12],[0,0,-1],tiled,9.40,10.84)
    for x in (-7.8,7.8):probe('lower end hip roof',[x,0.,12.],[0,0,-1],tiled,9.25,10.95)
    for x in [-.93,.93,3.5,-3.5]:
        street('pale decorated main ridge',x,6.90,ridge,11.82,11.90)
    for x in [-2.05,2.05]:street('diagonal member in open ridge',x,6.86,['dark rafters and soffit'],11.944,11.975)
    for x in [-1.88,1.88]:street('actual light through neighboring opening',x,6.86,None,0,0)
    for x,y in [(9,0),(-9,0),(0,4.9),(0,-4.9)]:
        probe('outside entire pavilion',[x,y,9],[0,0,-1],None,0,0)
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
