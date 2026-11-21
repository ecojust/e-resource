"""Independently probe serialized south gallery surfaces and passages measured in metres."""
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
ID='huangpu-qiuxin-shipyard-office-south-veranda'
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
    def face(name,x,z,m,a,b,eye_y=-1):
        cast(name,[x,eye_y,z],[0,1,0],b+.10,m,a,b)
    stations=[-10.24+4.096*i for i in range(6)]
    for i,station in enumerate(stations):
        posts=[station]if i in(0,5)else[station-.172,station+.172]
        for j,x in enumerate(posts):
            for z in [1.9,6.0]:
                face(f'Cast shaft {i+1}/{j+1} z{z}',x,z,['graphite cast iron'],.96,1.04)
        if len(posts)>1:
            for z in [2.5,6.6]:
                cast(f'Open gap inside paired shafts {i+1} z{z}',[station,-1,z],[0,1,0],1.5,None)
    for i,x in enumerate([-8.66,-6.25,-3.83,-1.45,.96,3.38,5.84,8.58]):
        for z in [2.0,6.1]:
            face(f'Recessed division {i+1} z{z}',x,z,['deep red sash'],1.94,2.05,.48)
            face(f'Clear pane {i+1} z{z}',x+.22,z,['recessed smoky glass'],2.07,2.13,.48)
    for i in range(5):
        x=(stations[i]+stations[i+1])/2
        for z in [4.26,8.59]:
            face(f'Under gallery head {i+1} z{z}',x,z-.057,['graphite cast iron'],.026,.040,.0)
        for z in [2.03,6.95]:
            cast(f'Clear public porch span {i+1} z{z}',[x,-1.05,z],[0,1,0],2.0,None)
        cast(f'Wood boards bay {i+1}',[x,1.17,6.18],[0,0,-1],2.5,['warm gallery boards'],1.62,1.66)
        cast(f'Pale upper soffit {i+1}',[x,1.21,7.5],[0,0,1],1.7,['pale gallery ceiling'],1.06,1.12)
        cast(f'Ground veranda paving {i+1}',[x,1.1,1.91],[0,0,-1],1.9,['weathered grey stone'],1.70,1.74)
        y=.079
        for z in [5.45]:
            face(f'Upper handrail bay {i+1}',x,z,['oxblood eave timber'],1.02,1.08)
    for y in [1.65,3.3,6.9,12.9,16.6]:
        for x in [-6.4,0,7.6]:
            cast(f'Roof surface {x}/{y}',[x,y,14],[0,0,-1],7,['brown clay roof'],2.,6.)
    for x in [-4.92,3.67]:
        cast(f'Chimney top {x}',[x,5.2,13.5],[0,0,-1],3,['weathered grey stone'],1.79,1.83)
    for x in [-8.5,1.2,7.8]:
        cast(f'Above roof {x}',[x,-.5,12.25],[0,1,0],20,None)
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
            result=probes(Scene(path));result['decoded_sha256']=digest(path);results[role]=result
            print(role,result['count'],[(s['name'],s['hit'])for s in result['samples']if not s['passed']][:8],flush=True)
    answer=dict(id=ID,checker_sha256=digest(Path(__file__)),source_reader_sha256=digest(READER),results=results)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    return all(c['passed']for c in results.values())
if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
