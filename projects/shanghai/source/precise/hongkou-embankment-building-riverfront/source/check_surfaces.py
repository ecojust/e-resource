"""Measure the glazed river walls, four stair bays, curved corner ribbons and open rooftop belvedere on all three actual GLBs."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-embankment-building-riverfront'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']




def test(scene):
    import math
    rows=[]
    def shoot(label,position,dir,mats,low,high,limit=25):
        result=scene.ray(position,dir,limit)
        valid=(result is None if mats is None else result is not None and result['material'] in mats and low<=result['distance_m']<=high)
        rows.append(dict(label=label,origin=position,direction=dir,expected_materials=mats,distance_bounds_m=[low,high],actual=result,passed=valid))
    metal=['dark steel casement','smoky blue-grey glass','infilled balcony glazing'];brick=['brown face brick'];stone=['light buff bands','warm exposed aggregate'];roof=['grey roof']
    for row in range(9):
        z=3.02+row*3.2
        for x in [-46.15,-24.13,8.65,36.18]:
            y=-.65*(x+47.8)/108.6
            shoot('residential stair window between brick piers',[x,y-1.8,z+1.4],[0,1,0],metal,1.91,2.10)
            shoot('brown facing on four staircase bays',[x+.87,y-1.8,z+1.4],[0,1,0],brick,1.63,1.78)
    # Sample one measured chord in each of the three rounded river fronts.
    for cx,cy,ra,lo,hi,n,index in [(-47.8,8.4,8.4,155,270,9,4),(60.8,9.4,10.05,270,348,8,4),(100.35,3.73,10.8,177,345,12,5)]:
        a=math.radians(lo+(hi-lo)*(index+.5)/n);v=(math.cos(a),math.sin(a));r=ra*math.cos(math.radians((hi-lo)/n/2))
        x=cx+(r+1.5)*v[0];y=cy+(r+1.5)*v[1]
        for level in range(9):
            z=3.02+level*3.2
            shoot('turning strip windows',[x,y,z+1.45],[-v[0],-v[1],0],metal,1.63,1.84)
            shoot('continuous concrete band under strip windows',[x,y,z+.32],[-v[0],-v[1],0],stone,1.19,1.34)
    for j in range(6):
        a=math.tau*(j+.5)/6;v=(math.cos(a),math.sin(a))
        shoot('open wall of rooftop pavilion',[60.3+6*v[0],7.27+6*v[1],34.74],[-v[0],-v[1],0],None,0,0,5.6)
    for j in range(6):
        a=math.tau*j/6;x=60.30+4.55*math.cos(a);y=7.27+4.12*math.sin(a)
        shoot('solid pier between open crown bays',[x+1.0,y,34.74],[-1,0,0],stone,.79,.85)
    for x,y in [(-35,2.6),(10,2.),(55,2.2),(94,0)]:
        shoot('flat roof on riverfront strip',[x,y,40],[0,0,-1],roof,8.12,8.29)
    for x,y in [(20,-6),(83,9),(84,22),(-62,15),(118,-10)]:
        shoot('riverfront pavement or clear entrance courtyard',[x,y,40],[0,0,-1],None,0,0,42)
    for a,c in [((70.63,7.31),(78.30,38.50)),((78.30,38.50),(98.10,34.09)),((98.10,34.09),(89.56,4.30))]:
        vx=c[0]-a[0];vy=c[1]-a[1];l=math.hypot(vx,vy);tx,ty=vx/l,vy/l;nx,ny=ty,-tx
        n=max(1,round(l/(5.1 if a==(78.30,38.50)else 4.67)));u=.5*l/n
        x=a[0]+u*tx+1.8*nx;y=a[1]+u*ty+1.8*ny
        for z in [4.37,10.77,17.17,23.57,29.97]:
            shoot('three enclosing sides of the entrance courtyard',[x,y,z],[-nx,-ny,0],metal,1.74,2.24)
    return dict(passed=all(q['passed']for q in rows),samples=rows)

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
