"""Probe the curved windows, open ground-level drive, balconies, outer stairs and lantern of the Green House."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='jingan-woo-tongwen-green-house'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']



def test(scene):
    import math
    rows=[]
    def sample(label,origin,direction,materials,low,high):
        hit=scene.ray(origin,direction,72)
        passed=hit is None if materials is None else hit is not None and hit['material']in materials and low<=hit['distance_m']<=high
        rows.append(dict(label=label,origin=origin,direction=direction,expected_materials=materials,distance_bounds_m=[low,high],actual=hit,passed=passed))
    def xy(u,v):return (u*.0625-21.875,15-v*.0625)
    glass=['curved garden glazing'];street=['grey blue street glazing'];tile=['moss green glazed tesserae','pale green glazed tile joint']
    metal=['painted steel glazing bars'];cream=['pale stone coping','weathered flat roof'];clay=['red clay terrace pavers']
    for direction in (17,41,68,96,119,151):
        # Fire inward from the east, across the front and around the west lip.
        a=math.radians(direction);ux,uy=math.cos(a),-math.sin(a);cx,cy=xy(561,338)
        for z in [5.59,6.95,9.57,12.75,13.80]:
            sample('three curved sun-room window bands',[cx+ux*4.10,cy+uy*4.10,z],[-ux,-uy,0],glass+metal,.92,1.26)
        if direction<126:
            sample('green tile separator between circular window bands',[cx+ux*4.10,cy+uy*4.10,8.46],[-ux,-uy,0],tile,.94,1.19)
    for a in [32,65,98,133,154]:
        x,y=xy(443,118);ux=math.cos(math.radians(a));uy=math.sin(math.radians(a))
        for z in [3.20,6.3,9.40,12.65,15.67]:
            r=3.65
            sample('street stairwell curved glazing',[x+ux*r,y+uy*r,z],[-ux,-uy,0],street+metal,1.06,1.59 if z>=15 else 1.55)
    for x in [-1.4,-.3,2.70,5.85,7.54]:
        # Ground hall and garden rooms leave a real cross-driveway through the
        # building. It is unobstructed at standing height below the floor above.
        sample('drive clear horizontally eastwards',[x,-.65,1.08],[1,0,0],None,0,0)
    for x in [-2.87,-1,2,5.6]:
        sample('front room panes below second-floor garden balcony',[x,-16,1.48],[0,1,0],glass+metal,5,7.6)
    for frac in [.27,.53,.79]:
        # The corrected exterior winding leaves the steel muntins and tiled
        # structural piers visible in front of the recessed ground-floor glass.
        start=1.25*(271-400)+443
        end=1.25*(493-400)+443
        u=start+(end-start)*(.07+.86*frac);x,y=xy(u,118+1.25*(368-149))
        sample('green piers in front of recessed garden glazing',[x,y-1,1.77],[0,1,0],tile,.87,.9)
    for u,v in [(282,242),(346,246),(414,290)]:
        x,y=xy(u,v);sample('curving canopy above the top balcony',[x,y,14.42],[0,0,1],['warm plaster soffit'],.39,.43)
    # Arc measured in the ground-floor plan: twenty-six steps, descending
    # towards the grass. Fire downward locally without looking through upper decks.
    for i in [1,4,7,10,14,17,20,23,25]:
        theta=math.radians(180-112*(i+.5)/26);u=277+55*math.cos(theta);v=366+55*math.sin(theta)
        x,y=xy(u,v);z=4.3*(26-i)/26
        sample('garden spiral tread level',[x,y,z+.17],[0,0,-1],clay,.165,.18)
    for u,v,low,high in [(128,159,14.9,15.2),(176,115,14.9,15.2),(443,119,16.5,16.7),
            (561,338,15.1,15.3),(580,351,15.1,15.3)]:
        x,y=xy(u,v);sample('roof and circular east canopy',[x,y,20],[0,0,-1],cream,20-high,20-low)
    for x,y in [(-23,-12),(23,-15),(22,18),(0,-19),(-7,-18)]:
        sample('preserved garden or open off-site ground',[x,y,22],[0,0,-1],None,0,0)
    return dict(passed=all(r['passed'] for r in rows),samples=rows)

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
