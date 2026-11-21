"""Measure the stepped street front, arcades, roof lanterns and open portico on all three Gaoyang meshes."""
from argparse import ArgumentParser
import numpy as np
from hashlib import sha256
import json
from pathlib import Path
import runpy
import subprocess
import tempfile

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='hongkou-gaoyang-building-south-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
SerialScene=runpy.run_path(str(READER))['SerialScene']


def test(scene,role):
    rows=[]
    def ray(label,point,direction,length,wanted,lo=0,hi=20):
        hit=scene.ray(point,direction,length)
        ok=hit is None if wanted is None else bool(hit and hit['material']==wanted and lo<=hit['distance_m']<=hi)
        rows.append(dict(test=label,origin=list(map(float,point)),direction=list(map(float,direction)),length_m=length,expected_material=wanted,range_m=[lo,hi],hit=hit,passed=ok))
    # Street width and recess were measured from the registered owner's three outside lines.
    # These coordinates are independent of the mesh construction objects.
    west,wi,ei,east=-25.44,-10.57,13.38,25.44
    mid=(wi+ei)/2
    def street(label,x,z,material,limits):
        ray(label,[x,-2.7,z],[0,1,0],10,material,*limits)
    for side,(start,end,pad)in enumerate([(west,wi,2.13),(ei,east-1.65,1.75)]):
        for i in range(4):
            x=start+pad+(end-start-2*pad)*i/3
            for z in [6.04,10.84,15.63,20.47]:
                street(f'tower wing {side+1} bay {i+1} glass at {z}',x+.19,z,'recessed grey glazing',(3.16,3.24))
            if role!='lod':
                street(f'tower wing {side+1} bay {i+1} metal frame',x,6.29,'dark window joinery',(3.01,3.07))
        street(f'tower wing {side+1} stone between bays',start+pad+(end-start-2*pad)/6,16.0,'weathered grey render',(2.86,2.90))
    for i,(a,b) in enumerate([((23.79,.18),(24.96,.66)),((24.96,.66),(25.44,1.83))]):
        ux,uy=b[0]-a[0],b[1]-a[1];span=(ux*ux+uy*uy)**.5
        nx,ny=uy/span,-ux/span
        x,y=(a[0]+b[0])/2+ux/span*.12,(a[1]+b[1])/2+uy/span*.12
        for z in [1.13,6.09,10.84,15.69,20.48]:
            ray(f'east corner pane {i+1} at {z}',[x+nx*.78,y+ny*.78,z],[-nx,-ny,0],2,
                'recessed grey glazing',1.07,1.13)
    for group in range(5):
        center=wi+2.40+(ei-wi-4.80)*group/4
        for j in [-1,0,1]:
            for floor in [6.09,10.89,15.69]:
                street(f'central group {group+1} sash {j+2} level {floor}',center+j*1.23+.18,floor,'recessed grey glazing',(7.16,7.22))
    for i in range(15):
        x=wi+.78+(ei-wi-1.56)*i/14
        street(f'central arcade window {i+1}',x+.16,20.48,'recessed grey glazing',(7.16,7.22))
    for dx in [-9.71,-8.15,8.15,9.71]:
        street('portico column '+str(dx),mid+dx,2,'pale cast stone',(3.26,3.45))
    ray('clear between paired eastern columns',[mid+8.87,-.64,1.24],[0,1,0],3.25,None)
    ray('clear between paired western columns',[mid-8.87,-.64,1.24],[0,1,0],3.25,None)
    ray('open porch floor',[mid,1.68,2.03],[0,0,-1],2.0,'pale cast stone',1.82,1.91)
    ray('canopy underside',[mid,1.87,3.13],[0,0,1],2,'weathered grey render',.98,1.10)
    for x in [(west+wi)/2,(ei+east)/2]:
        street('lantern glazing '+str(x),x+.19,31.37,'recessed grey glazing',(6.60,6.77))
        street('dormer grille '+str(x),x+.20,26.05,'painted metal grille',(3.05,3.36))
        ray('tower shoulder '+str(x),[x+3.65,5.22,32],[0,0,-1],10,'weathered grey render',4.2,5.9)
        ray('flagstaff top '+str(x),[x,5.22,42],[0,0,-1],3.,'dull metal finials',1.42,1.55)
    ray('roof between towers',[mid,7.3,28],[0,0,-1],8,'grey roof flashing',4.91,5.03)
    return dict(passed=all(x['passed']for x in rows),samples=rows)


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
    result=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),
                reader_sha256=digest(READER),decoder_sha256=digest(DECODER),results=rows)
    args.out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for role,r in rows.items():print(role,'pass' if r['passed'] else [q for q in r['samples'] if not q['passed']])
    return all(r['passed'] for r in rows.values())


if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
