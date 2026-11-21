"""Test real first-hit materials and outward faces on the three bays of the north elevation; no builder objects are consulted."""
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
ID='huangpu-swire-east-building-bund-front'
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
    axes=[3.22,7.11,10.88,15.34,19.67,23.76,27.65]
    sills=[1.48,6.,10.90,15.40,21.51];tops=[4.87,9.55,14.50,18.47,23.72];widths=[2.21,2.38,2.43,2.45,2.25]
    for i,x in enumerate(axes):
        for floor in range(5):
            paired=i==3 and floor>=3
            doorway=i==3 and floor==0
            bottom=.11 if doorway else sills[floor]
            top_z=14.35 if i==3 and floor==2 else tops[floor]
            centers=[x-.608,x+.608]if paired else [x]
            width=.96 if paired else (2.38 if doorway else widths[floor])
            inset=-.42 if doorway else (-.24 if paired else -.21)
            for j,mid in enumerate(centers):
                for side in [-1,1]:
                    front(f'Bay {i+1}, row {floor+1}, opening {j+1}: glass {side}',mid+side*width*(.08 if doorway else .14),bottom+(top_z-bottom)*.57,'Deep green bronze door glazing'if doorway else 'Blue grey restored window glass',inset-.063)
                front(f'Bay {i+1}, row {floor+1}, opening {j+1}: upright',mid,bottom+(top_z-bottom)*.58,'Black painted metal sash',inset+.009)
                if floor in (1,2,3):
                    front(f'Bay {i+1}, row {floor+1}, opening {j+1}: top railing',mid+width*.27,bottom+.84,'Black balcony rail and door iron',.148,.015)
                if not paired and not doorway:
                    front(f'Bay {i+1}, row {floor+1}: sill',mid+width*.23,bottom-.055,'Weathered ochre sandstone trim',.30 if i==3 and floor==2 else .200)
                if (floor!=2 or i==3)and not (i==3 and floor<2):
                    front(f'Bay {i+1}, row {floor+1}, opening {j+1}: keystone',mid,top_z+.07,'Pale limestone sill and capitals',.182)
    for dx in (-.78,.78):front(f'Portal iron at exposed outer scroll {dx}',axes[3]+dx,1.45,'Black balcony rail and door iron',-.347,.016)
    for u in (.61,5.19,9.03,13.16,17.54,21.72,25.76,30.14):
        for z in (11.91,13.19,16.76,18.63,21.11,23.21):
            front(f'High pilaster {u}/{z}',u,z,'Swire riverfront red brick',.227 if z<20 else .205)
    for x in (.89,5.72,9.52,12.72,17.09,22.16,26.25,29.71):
        for z in (.73,2.18,6.84,8.81):front(f'Rusticated first and second storey {x}/{z}',x,z,'Rust-red cut masonry',0)
    for z in (.73,2.18,6.84,8.81):front(f'Recessed joints in lower blocks {z}',9.44,z,'Shadowed red brick voussoirs',-.046)
    for x in (2.,7.1,11.5,19.66,24.,29.11):
        for z,depth,material in [(5.69,.36,'Pale limestone sill and capitals'),(10.49,.45,'Pale limestone sill and capitals'),(19.53,.45,'Brown moulding and coping'),(19.74,.51,'Pale limestone sill and capitals'),(25.11,.51,'Pale limestone sill and capitals')]:
            front(f'Horizontal sill or cornice {x}/{z}',x,z,material,depth-.05)
    for x in (3.,8.,12.,18.,24.,28.):
        top(f'Visible flat parapet return {x}',x,.89,26.22,'Rust-red cut masonry')
    for level in (10.5,26.15):
        front(f'Central pediment side relief {level}',15.34+.55,level+.35,'Weathered ochre sandstone trim',.30)
    cast('Visible flag mast front',[15.34,-1.,29.71],[0,1,0],2,['Copper coloured flag socket'],1.15,1.22)
    cast('Sky over north side',[27.65,-.7,27.0],[0,1,0],2,None)
    return dict(passed=all(a['passed']for a in out),count=len(out),samples=out)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--pilot-dir',type=Path)
    parser.add_argument('--out',type=Path,required=True)
    a=parser.parse_args();results={};assets={}
    with tempfile.TemporaryDirectory()as work:
        if a.pilot_dir:assets={r:a.pilot_dir/(r+'.glb') for r in ('near','far')}
        else:
            assert a.manifest
            manifest=json.loads(a.manifest.read_bytes());assert manifest['id']==ID
            for role in ('raw','full','lod'):
                desc=manifest['assets'][role];src=a.manifest.parent/desc['file']
                assert src.stat().st_size==desc['bytes']and digest(src)==desc['sha256']
                mesh=src
                if role!='raw':
                    mesh=Path(work)/(role+'.glb');subprocess.run(['node',UNPACK,src,mesh,DECODER],check=True,stdout=subprocess.DEVNULL)
                assets[role]=mesh
        for role,path in assets.items():
            result=probes(Scene(path));result['decoded_sha256']=digest(path)
            result['brick_uv']=runpy.run_path(str(PROJECT/'data/audit/swire-east-building-bund-front-v1/check-brick-sampling.py'))['sample'](path)
            results[role]=result
            print(role,result['count'],[(s['name'],s['hit'])for s in result['samples']if not s['passed']][:8],flush=True)
    answer=dict(id=ID,checker_sha256=digest(Path(__file__)),source_reader_sha256=digest(READER),results=results)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    return all(c['passed']for c in results.values())
if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
