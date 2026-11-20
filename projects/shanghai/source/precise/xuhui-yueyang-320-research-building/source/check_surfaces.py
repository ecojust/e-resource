"""Test seven public arcade bays, paired windows, masonry ribs, stepped crowns and two open courts."""
from argparse import ArgumentParser
from hashlib import sha256
import json
from math import sin,cos,pi,hypot
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='xuhui-yueyang-320-research-building'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene):
    rows=[]
    def ray(name,o,v,material,distance,tolerance=.046):
        h=scene.ray(o,v,120)
        ok=h is None if material is None else h is not None and h['material']==material and abs(h['distance_m']-distance)<tolerance
        rows.append(dict(label=name,origin=o,direction=v,expected_material=material,expected_distance=distance,actual=h,passed=ok))
    def down(name,x,y,z,material,hit):
        ray(name,[x,y,z],[0,0,-1],material,None if hit is None else z-hit)
    def front(name,x,z,material,y,start=-12):
        ray(name,[x,start,z],[0,1,0],material,None if y is None else y-start)
    glass='grey window glass';sash='dark window sash';stone='ochre portico stone'
    center=.716;span=17.69/7;front_y=-6.02
    for i in range(7):
        x=center+(i-3)*span
        # A horizontal ray from the front through every air gap reaches the back wall.
        ray('air through flat center of arch '+str(i+1),[x+0.12,front_y+.73,2.1],[0,-1,0],None,None)
        front('spandrel above semicircular arch '+str(i+1),x,4.82,stone,front_y)
        down('portal roof above open arch '+str(i+1),x,-4.65,12,'brown stone sill',6.19)
        down('walkable arcade landing '+str(i+1),x,-4.57,3.45,'grey granite step',.54)
        down('outer entry step '+str(i+1),x,-7.65,2.,'grey granite step',.135)
    for i in range(1,7):
        x=center+(i-3.5)*span
        front('stone pier below capital '+str(i),x,2.01,stone,front_y-.045)
        front('capital above square pier '+str(i),x,3.31,stone,front_y-.18)
    for x in [-3.88,0,3.88]:
        for z in [6.02,10.08,14.07,18.18]:
            front('paired central window light',x+.48,z,glass,-.82+.241,start=-.91)
        front('blind round arch at center bay crown',x,21.705,'light ochre rib stone',-.94,start=-2.02)
    for x in [-3.88,0,3.88]:
        front('stone key inside upper blind arch',x,20.57,'light ochre rib stone',-.966,start=-1.6)
    for x in [-1.94,1.94]:
        front('raised tapered ornament on central stone pier',x,14.31,'light ochre rib stone',-1.167,start=-1.8)
    for left,right in [(-39.43,-10.48),(10.48,39.43)]:
        step=(right-left)/8
        for i in range(8):
            x=left+(i+.5)*step
            for z in [6.20,10.12]:
                front('paired window on long wing',x+.46,z,glass,1.04+.241)
            front('iron crossbar on paired wing window',x+.46,6.772,sash,1.04+.174)
        for i in (1,3,6):
            x=left+i*step+.071
            front('raised ochre masonry blade on wing',x,7.05,'brown stone sill',1.04-.29)
    for (x,y) in [(-21.0,22.8),(22.1,23.0),(-20,18.5),(25.0,25.7)]:
        down('open historical court remains sky-to-ground',x,y,32,None,None)
    for x,y in [(-37.4,23.3),(37.4,23.3),(21.1,40.5),(-21.8,41.5),(0,24.6)]:
        down('historic flat roof around two courts',x,y,32,'weathered roof finish',14.87)
    down('narrow roof lantern above center tower',.35,9.6,32,'brown stone sill',25.99)
    for x in [-43.7,43.7]:
        down('rounded end pavilion roof',x,4.3,25,'weathered roof finish',16.18)
        down('raised rear pavilion roof',x,41.4,25,'brown stone sill',17.8)
    for x,y in [(-50.7,20.0),(50.78,20),(0,48.8),(0,-10.2)]:
        down('outside the historic hall',x,y,32,None,None)
    return dict(triangles=len(scene.tri),samples=rows,passed=all(row['passed']for row in rows))


def digest(file):
    return sha256(file.read_bytes()).hexdigest()


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
