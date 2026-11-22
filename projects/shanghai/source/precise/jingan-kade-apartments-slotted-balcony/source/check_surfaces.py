from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).absolute().parent
PROJECT=SOURCE.parents[3]
ID='jingan-kade-apartments-slotted-balcony'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']








def test(scene,role):
    rows=[]
    def cast(kind,x,z,options,lo,hi):
        hit=scene.ray([x,-.5,z],[0,1,0],1.11)
        ok=hit is not None and hit['material'] in options and lo<=hit['distance_m']<=hi
        rows.append(dict(feature=kind,x=x,z=z,expected_material=sorted(options),depth_interval_m=[lo,hi],hit=hit,passed=ok))
    front=[(.47,1.42),(2.50,3.37),(3.56,4.30),(4.49,5.34)]
    rows_z=[(.408,.470),(.543,.605),(.677,.739),(.810,.872)]
    # Each complete aperture is tested at three independent horizontal positions.
    for l,r in front:
        for low,high in rows_z:
            for t in (.15,.49,.84):
                x=l+t*(r-l);z=(low+high)/2;hit=scene.ray([x,-.5,z],[0,1,0],.88)
                rows.append(dict(feature='clear front slot',point=[x,z],hit=hit,passed=hit is None))
            cast('upper rendered bar',(l+r)/2,high+.021,{'cream render'},.498,.502)
    for x in (.20,1.80,3.45,4.39,5.42):
        for low,high in rows_z:
            cast('solid pier between openings',x,(low+high)/2,{'cream render'},.498,.502)
    for x in (.12,.72,1.24,2.05,2.70,3.18,3.66,4.67,5.12):
        cast('projecting top edge',x,.967,{'coping'},.486,.490)
        hit=scene.ray([x,-.5,1.175],[0,1,0],.82)
        rows.append(dict(feature='open air between iron rails',x=x,hit=hit,passed=hit is None))
    for z0,z1 in rows_z:
        for y in (.31,.55,.79):
            hit=scene.ray([-.55,y,(z0+z1)/2],[1,0,0],.85)
            rows.append(dict(feature='clear opening in side return',y=y,z=(z0+z1)/2,hit=hit,passed=hit is None))
        for y in (.16,.96,1.26):
            hit=scene.ray([-.55,y,(z0+z1)/2],[1,0,0],.85)
            rows.append(dict(feature='side masonry between openings',y=y,z=(z0+z1)/2,hit=hit,passed=hit is not None and hit['material']=='cream render' and .439<hit['distance_m']<.446))
    for x in (.46,1.44,2.45,3.46,4.41,5.44):
        cast('slender steel post',x,1.171,{'iron'},.540,.554)
        cast('handrail',x+.028,1.275,{'iron'},.538,.551)
    return dict(samples=rows,passed=all(x['passed'] for x in rows))

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
            rows[role]=dict(sha256=a['sha256'],**test(SerialScene(mesh),role))
            if role!='raw':mesh.unlink()
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
