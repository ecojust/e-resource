"""Check arched halls, diamond brickwork, twin wings, retroceding court and roofs on serialized meshes."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-foreign-ymca'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def probe(label,origin,direction,material,distance,tolerance=.045):
        hit=scene.ray(origin,direction,53)
        ok=hit is None if material is None else bool(hit and hit['material']==material and abs(hit['distance_m']-distance)<=tolerance)
        rows.append({'label':label,'origin':origin,'direction':direction,'expected_material':material,
                     'distance_m':distance,'tolerance_m':tolerance,'hit':hit,'passed':ok})
    def front(label,x,z,material,plane):
        probe(label,[x,-3,z],[0,1,0],material,plane+3)
    for x in [-3.14,0,3.14]:
        front('recessed street door',x+.23,1.25,'smoky window glass',.76)
        front('arcade lower lights',x+.23,6.08,'smoky window glass',.78)
        front('arcade opaque window skirt',x+.23,8.23,'weathered canopy iron',.58)
        front('arcade upper glazing',x+.20,11.65,'smoky window glass',.78)
    for x in [-1.76,-1.38,1.38,1.76]:
        front('paired cylindrical stone supports',x,7.40,'cream architectural stone',-.147)
    for sign in [-1,1]:
        for off in [-.55,.55]:
            front('paired lateral hall windows',sign*8.93+off+.16,9.62,'smoky window glass',.63)
        for column in [-1,0,1]:
            center=sign*8.995+.01246+2.97*column
            for height in [15.00,17.95,20.90,23.85,26.80]:
                front('recessed tower sash',center+.10,height,'smoky window glass',1.02)
            front('profiled tower window head',center+.11,24.94,'dark window joinery',.926)
            for dx in [-.35,.35]:
                front('paired arched tower heads',center+dx+.10,29.55,'smoky window glass',1.02)
    front('raised brown chequer brick',5.55,6.73,'brown diaper brick',.09)
    front('buff field between diaper bricks',5.28,6.73,'pale buff brick',.12)
    front('long inner court to central back facade',.69,22.43,'smoky window glass',24.20)
    for x,y,top in [(-9,10,32.63),(9,10,32.63),(0,12,13.55),(0,28,31.56)]:
        probe('wing, terrace or rear roof',[x,y,40],[0,0,-1],'roof membrane',40-top)
    for x in [-17,17]:
        probe('independent neighboring property',[x,12,40],[0,0,-1],None,None)
    return {'triangles':len(scene.tri),'samples':rows,'passed':all(r['passed'] for r in rows)}


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
