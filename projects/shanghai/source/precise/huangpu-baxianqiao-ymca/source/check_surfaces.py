"""Sample the actual serialized street frontage; render geometry is never reconstructed."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-baxianqiao-ymca'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def check(label,origin,direction,material,distance=None):
        hit=scene.ray(origin,direction,42)
        ok=hit is None if material is None else (
            hit is not None and hit['material']==material and abs(hit['distance_m']-distance)<.04)
        rows.append(dict(label=label,origin=origin,direction=direction,expected=material,
                         expected_distance_m=distance,hit=hit,passed=ok))
    def from_street(label,x,z,material,y):
        check(label,[x,-3,z],[0,1,0],material,3+y)
    # Isolated probes derive from the dated street/portal photographs and the
    # root footprint; expected front is y=.14 in author coordinates.
    for sign in (-1,1):
        from_street('outer granite window',sign*16.32+.21,9.07,'window glazing',.43)
        from_street('portal flanking door',sign*4.08+.16,1.24,'window glazing',.62)
        for z in [12.10,15.25,18.40,21.55,24.70]:
            from_street('single brick light',sign*4.08+.13,z,'window glazing',.43)
            from_street('paired brick light',sign*(8.16+.72)+.13,z,'window glazing',.43)
            from_street('wall between paired lights',sign*8.16,z,'brown brick',.14)
        from_street('painted red gallery pier',sign*6.12,30.02,'vermilion',-.018)
    from_street('cut-corner entrance glazing',.21,1.40,'window glazing',.88)
    from_street('portal frieze above canopy',.16,7.91,'pale carved stone',-.10)
    from_street('upper portal opening',.19,6.17,'window glazing',.81)
    from_street('outer hotel canopy',.31,4.94,'dark sash',-1.6275)
    from_street('gallery central glazed bay',.19,29.94,'window glazing',.43)
    check('flat roof behind tile ridge',[0,5.3,40],[0,0,-1],'flat upper roof',6.525)
    for height,near,far in [(30,1.12,2.04),(35,2.29,3.39)]:
        for x in (-12.60,.13,11.80):
            origin=[x,-.67,height]
            hit=scene.ray(origin,[0,0,-1],6)
            rows.append(dict(label='blue tile roof at the street eave',origin=origin,direction=[0,0,-1],
                             expected=['blue glazed tile','glazed tile rib'],expected_distance_range_m=[near,far],
                             hit=hit,passed=hit is not None and hit['material'] in ['blue glazed tile','glazed tile rib']
                             and near < hit['distance_m'] < far))
    for x in (-21,21):
        check('adjacent ground outside wing',[x,6,40],[0,0,-1],None)
    check('south courtyard/other wing excluded',[10,14.2,40],[0,0,-1],None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(r['passed'] for r in rows))


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
