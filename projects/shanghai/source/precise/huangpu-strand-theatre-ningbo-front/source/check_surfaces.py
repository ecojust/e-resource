"""Test real first-hit materials and outward faces on the Ningbo Road elevation and street chamfer; no builder objects are consulted."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
import numpy as np

SOURCE=Path(__file__).resolve().parent
PROJECT=SOURCE.parents[3]
ID='huangpu-strand-theatre-ningbo-front'
READER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
Scene=runpy.run_path(str(READER))['SerialScene']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def probes(scene):
    out=[]
    def cast(name,eye,vector,length,expected,lo=0,hi=50):
        hit=scene.ray(eye,vector,length)
        front=None
        if hit:
            t=scene.tri[hit['triangle_index']]
            normal=np.cross(t[1]-t[0],t[2]-t[0])
            front=float(np.asarray(vector)@normal)<-1.e-11
        ok=(not hit) if expected is None else bool(hit and hit['material'] in expected and lo<=hit['distance_m']<=hi and front)
        out.append(dict(name=name,eye=eye,direction=vector,length=length,expected=expected,interval=[lo,hi],hit=hit,single_sided_front=front,passed=ok))
    from math import cos,sin,pi
    def front(name,x,z,material,d,tolerance=.008,origin_d=1.8):
        cast(name,[x,-origin_d,z],[0,1,0],origin_d+.8,[material],
             origin_d-d-tolerance,origin_d-d+tolerance)
    def top(name,x,y,z,material):
        cast(name,[x,y,z+.39],[0,0,-1],.8,[material],.38,.40)
    brick='Strand cream and red diaper brick'
    dark='Near black window joinery'
    stone='Warm grey moulded stone'
    pale='Light carved stone'
    glass='Grey blue glass'
    golden='Muted gold letters and handles'
    L=20.8106033132;C=L/2
    ux=3.1498624137/4.5614791303;uy=3.2993118421/4.5614791303
    def chamfer(name,u,z,material,d,tol=.012,eye=1.30):
        x=L+ux*u;y=uy*u;nx=uy;ny=-ux
        cast(name,[x+nx*eye,y+ny*eye,z],[-nx,-ny,0],eye+1.2,[material],eye-d-tol,eye-d+tol)
    for u in (3.76,17.05):
        for shift in (-.87,.87):
            for z in (7.34,8.58,9.39):
                front(f'Paired flank glazing {u} {shift} {z}',u+shift+.15,z,glass,-.232)
            front(f'Flank transom {u} {shift}',u+shift+.08,9.06,dark,-.141)
        for shift in (-1.12,0,1.12):
            for z in (12.14,12.76):
                front(f'Three upper lights {u} {shift} {z}',u+shift+.12,z,glass,-.232)
        front(f'Cartouche face {u}',u,10.57,pale,.108)
        front(f'Central upper sash {u}',u,12.27,dark,-.141)
    for off in (-1.32,0,1.32):
        for z in (7.1,8.41,9.70,10.17):
            front(f'Three tall central lights {off} {z}',C+off+.12,z,glass,-.232)
    for dx in (-1.03,-.48,.64,1.09):
        front(f'Recessed arch glazing {dx}',C+dx,13.15,glass,-.232)
    for dx in (-.52,.62):
        front(f'Central stone spandrel beneath loggia {dx}',C+dx,11.10,stone,.096)
    for u in (.47,2.17,4.82,6.15,14.48,15.34,18.30,19.18):
        for z in (7.04,10.18,11.21,15.27):
            if 2.17<u<5.55 and z==7.04:continue
            if 15.34<u<18.56 and z==7.04:continue
            front(f'Coloured brick field {u} {z}',u,z,brick,0.)
    for u in (1.05,7.02,13.78,19.83):
        for z in (7.57,10.42,13.03,15.49):
            front(f'Glazed vine panel margin {u} {z}',u+.215,z,'Dark green tile recess',.166)
        front(f'White shoulders of relief tile {u}',u+.288,11.49,pale,.105)
    for u in (1.47,3.42,5.20,8.34,10.97,14.87,17.20,19.11):
        for z,d,m in [(5.96,.238,'Recessed moulding shadow'),(6.44,.370,pale),(16.23,.317,pale),(16.84,.537,stone),(17.33,.546,stone)]:
            front(f'Tiered cornices {u} {z}',u,z,m,d,.042)
    for u in (3.65,C,17.12):
        for z in (19.62,20.33,21.03):
            front(f'Setback attic glazing {u} {z}',u+.24,z,glass,-.71,.015)
        front(f'High inner mullion {u}',u+.46,20.14,dark,-.61,.015)
    for u in (1.32,6.25,13.17,18.94):
        front(f'Attic brick {u}',u,22.08,brick,-.59)
    for u in (16.84,17.59):
        front(f'Hotel entrance glass {u}',u,2.19,'Warm ground floor glazing',-.232)
    for u in (14.61,19.73):
        front(f'Side light in burgundy wall {u}',u,2.59,'Warm ground floor glazing',-.232)
    for u in (13.74,15.50,18.98):
        front(f'Burgundy ground wall {u}',u,2.15,'Burgundy hotel wall finish',.015)
    for u in (.65,1.24,3.60):
        for z in (7.83,10.11,12.79,15.22):
            chamfer(f'Angled patterned face {u} {z}',u,z,brick,0.)
    # Three fixed points on separate photographed golden strokes per character.
    inscriptions={
        '新': [(1.866,14.695),(2.866,14.945),(2.516,14.970)],
        '光': [(2.016,13.150),(2.291,13.225),(1.966,12.800)],
        '影': [(1.871,11.703),(2.071,11.478),(2.271,11.303)],
        '艺': [(2.396,9.683),(2.071,9.983),(2.496,9.983)],
        '苑': [(2.471,8.288),(2.096,8.288),(2.121,7.763)],
    }
    for character,points in inscriptions.items():
        for u,z in points:
            chamfer(f'Raised cinema letter {character} at {u},{z}',u,z,'Gilded cinema inscription',.203)
    for u,z in ((.63,18.90),(2.24,20.32),(3.53,22.12)):
        chamfer(f'Unpatterned buff corner above cornice {u}',u,z,'Plain buff attic brick',-.59)
    for u in (1.84,2.77):
        chamfer(f'Angled double door glass {u}',u,2.27,'Warm ground floor glazing',-.232)
    for u in (.79,3.68):
        chamfer(f'Street corner hotel finish {u}',u,1.64,'Burgundy hotel wall finish',-.006)
    for u in (.74,2.21,3.74):
        chamfer(f'Street moulding around chamfer {u}',u,16.85,stone,.537,.03)
    for x in (1.43,6.24,11.62,15.79,19.17):
        top(f'Flat coping weather surface {x}',x,.65,23.585,stone)
    cast('Clear above street outline',[9,-1.,23.98],[0,1,0],2,None)
    return dict(passed=all(a['passed']for a in out),count=len(out),samples=out)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--pilot-dir',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args()
    results={}
    if a.pilot_dir:
        assets={r:a.pilot_dir/(r+'.glb') for r in ('near','far')}
    else:
        assert a.manifest
        manifest=json.loads(a.manifest.read_bytes())
        assert manifest['id']==ID
        assets={}
        for role in ('raw','full','lod'):
            desc=manifest['assets'][role]
            src=a.manifest.parent/desc['file']
            assert src.stat().st_size==desc['bytes'] and digest(src)==desc['sha256']
            assets[role]=src
    sample=runpy.run_path(str(PROJECT/'data/audit/strand-theatre-ningbo-front-v1/check-brick-sampling.py'))['sample']
    with tempfile.TemporaryDirectory() as work:
        for role,asset in assets.items():
            path=asset
            if role in ('full','lod'):
                path=Path(work)/'decoded.glb'
                subprocess.run(['node',UNPACK,asset,path,DECODER],check=True,stdout=subprocess.DEVNULL)
            result=probes(Scene(path))
            result['decoded_sha256']=digest(path)
            result['brick_uv']=sample(path)
            results[role]=result
            print(role,result['count'],[s['name'] for s in result['samples'] if not s['passed']][:12],flush=True)
    answer=dict(id=ID,checker_sha256=digest(Path(__file__)),source_reader_sha256=digest(READER),results=results)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    return all(c['passed']for c in results.values())
if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
