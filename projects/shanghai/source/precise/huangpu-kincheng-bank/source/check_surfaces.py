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
ID='huangpu-kincheng-bank'
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
    from_street('portal recessed back',.25,1.6,'dark plaque',1.69)
    from_street('upper entrance glazing',.23,7.70,'bank glazing',.43)
    from_street('central semi-circular glazing',.23,16.34,'bank glazing',.43)
    from_street('bowed balcony parapet',.15,18.06,'Jinshan granite',-.70)
    for sign in (-1,1):
        for x in (5.27,8.37,11.47):
            from_street('first raised storey window',sign*(x+.17),7.75,'bank glazing',.90)
            from_street('blind arched stone tympanum',sign*(x+.10),10.28,'dressed granite',.67)
            from_street('tall rectangular third storey',sign*(x+.17),14.25,'bank glazing',.90)
        for z,y in [(10.29,.47),(24.42,.73)]:
            from_street('outer glazed arch including attic',sign*15.62,z,'bank glazing',y)
        for x in (14.45,16.29):
            from_street('paired upper end windows',sign*(x+.13),14.45,'bank glazing',.47)
        check('actual roof surface',[sign*10,9.5,34],[0,0,-1],'roof',4.52)
        check('separate adjacent block',[sign*20,9.5,34],[0,0,-1],None)
    check('rear outside project bounds',[0,21.6,34],[0,0,-1],None)
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
