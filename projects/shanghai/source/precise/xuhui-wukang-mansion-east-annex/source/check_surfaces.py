"""Check the brick shopfront, curved three-storey window ribbons, louvres and civic number on each delivered GLB."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-wukang-mansion-east-annex'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    import math
    rows=[]
    def shoot(label, position, direction, materials, low, high, limit=23):
        hit=scene.ray(position,direction,limit)
        passed=hit is None if materials is None else hit is not None and hit['material'] in materials and low<=hit['distance_m']<=high
        rows.append(dict(label=label,origin=position,direction=direction,expected_materials=materials,distance_bounds_m=[low,high],actual=hit,passed=passed))
    glass=['dark painted window steel','blue-grey window glass']
    shop=['shop display glass','dark painted window steel']
    render=['off-white render','pale concrete edge']
    for idx,(z,band,cap,positions) in enumerate([
            (8.18,6.50,7.395,[-4.83,-3.64,4.06]),
            (12.08,10.18,11.405,[-4.69,-3.47,4.55,5.71]),
            (16.15,14.12,15.425,[-7.31,-4.68,-3.49,-.36,6.12])]):
        for x in (-8.17,-6.62,-4.13,-.31,2.91,5.35,8.34):
            shoot('steel ribbon window of floor '+str(idx+3),[x,-2,z],[0,1,0],glass,1.69,1.85)
            shoot('pale continuous spandrel',[x,-2,band],[0,1,0],render,1.58,1.65)
        for side in [-1,1]:
            d=(side*math.sqrt(.5),-math.sqrt(.5))
            shoot('curved glazed return',[side*9.71+2.92*d[0],.53+2.92*d[1],z],[-d[0],-d[1],0],glass,2.08,2.25)
        for x in positions:
            shoot('projecting equipment hood',[x,-2,cap],[0,1,0],['ochre louvres'],1.02,1.2)
    for x in (-11.35,-10.16,-6.12,.20,2.29,5.32,9.65):
        shoot('glazing of a separate shop or service opening',[x,-2,1.33],[0,1,0],shop,2.25,2.42)
    for x in (-3.56,-2.78,-1.98):
        shoot('open bookshop entry before the rear cut',[x,-2,1.33],[0,1,0],None,0,0,3.48)
        shoot('neutral recess beyond the visible entrance',[x,-2,1.33],[0,1,0],['cut surface'],3.69,3.76)
    for x in (-9.16,-5.23,-.64,3.82,8.97):
        shoot('windows within the brick second floor',[x,-2,5.32],[0,1,0],glass,2.18,2.37)
    for x in (-11.95,-7.34,-3.12,1.37,6.07,10.19):
        shoot('red brick below the horizontal ribbons',[x,-2,3.988],[0,1,0],['russet face brick','brick bed and perp joints'],2.14,2.17)
    for x in (-3.25,-2.2,.28):
        shoot('brick sill or opening head at the shop',[x,-2,2.89],[0,1,0],['russet face brick','brick bed and perp joints'],2.13,2.18)
    shoot('civic sign green field',[-1.45,-2,2.986],[0,1,0],['green civic enamel'],2.08,2.11)
    shoot('painted shop placard below street number',[-1.64,-2,2.665],[0,1,0],['ivory lettering'],2.07,2.12)
    shoot('projecting metal shop canopy',[-6.82,-2,3.16],[0,1,0],['dark painted window steel'],1.20,1.28)
    for x,z in [(-9.09,4.085),(-4.14,5.54),(.77,5.55),(7.10,5.59),(10.96,4.97)]:
        shoot('red equipment hood on brick plinth',[x,-2,z],[0,1,0],['brick red louvres'],1.59,1.64)
    for x in (-11.28,11.28):
        shoot('flat end pier outside curved glazing',[x,-2,12.32],[0,1,0],render,2.15,2.24)
    for x in (-9.0,-3.8,2.0,8.7):
        shoot('bounded roof at back of parapet',[x,2.3,20.],[0,0,-1],['lead grey roof'],1.65,1.77)
    for x,y in [(0.,-1.5),(-15.,2.),(14.6,1.2),(.5,6.9)]:
        shoot('street, old main building or unmodeled rear',[x,y,20],[0,0,-1],None,0,0,21)
    return dict(passed=all(p['passed'] for p in rows),samples=rows)

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
