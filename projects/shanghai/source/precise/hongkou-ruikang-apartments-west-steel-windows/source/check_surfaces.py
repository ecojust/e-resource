from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-ruikang-apartments-west-steel-windows'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    samples=[]
    def ray(label,x,z,materials,y):
        origin=[x,-1.,z];hit=scene.ray(origin,[0,1,0],1.6)
        expected=[1+y-.004,1+y+.004] if materials else []
        ok=bool(hit and hit['material']in materials and expected[0]<=hit['distance_m']<=expected[1]) if materials else hit is None
        samples.append(dict(check=label,origin=origin,direction=[0,1,0],max_length=1.6,expected_materials=materials,expected_distance=expected,hit=hit,passed=ok))
    for idx,(centre,width) in enumerate([(-1.48,.76),(0.,1.2),(1.48,.76)]):
        x0=centre-width/2; x1=centre+width/2
        xa=x0+.032; xb=x1-.032; za=1.07; zb=2.678;count=6 if idx==1 else 3
        for k in range(count):
            for j in range(6):
                x=xa+(xb-xa)*(k+.52)/count;z=za+(zb-za)*(j+.52)/6
                ray('Recessed rectangular glass light',x,z,['grey blue glass','pale reflected glass'],.150)
        for k in range(1,count):
            for j in (0,2,4):ray('Vertical steel glazing bar',xa+(xb-xa)*k/count,za+(zb-za)*(j+.35)/6,['painted steel'],.089)
        for i in range(1,6):
            ray('Horizontal steel glazing bar',xa+(xb-xa)*.37,za+(zb-za)*i/6,['heavy steel transom' if i==4 else 'painted steel'],.074 if i==4 else .100)
        for x in (x0+.014,x1-.014):ray('Recessed outer jamb',x,1.42,['painted steel'],.067)
        for x in (centre-.093,centre+.12):
            ray('Apparent stone sill',x,1.003,['sill stone'],-.062)
            ray('Painted apron',x,.56,['painted render'],-.009)
            ray('Exposed lower edge of brick hood',x,2.865,['burnt brick'],-.126)
    for x in (-1.95,-.82,.82,1.95):
        for row in (2,7,14,21,32):
            ray('Brick pier face',x,(row+.55)*3.18/36,['burnt brick','red common brick','light fired brick'],-.083)
        for row in (2,7,14,32):
            ray('Recessed horizontal mortar joint',x,row*3.18/36,['brick joint'],-.069)
    for x in (-2.06,2.06):
        for z in (.23,1.17,2.91):ray('Raised outer pilaster band',x,z,['red common brick'],-.112)
    for x in (-2.38,2.38):ray('Beyond the outer brick face',x,1.44,[],0.)
    return dict(samples=samples,passed=all(s['passed']for s in samples))


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
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
