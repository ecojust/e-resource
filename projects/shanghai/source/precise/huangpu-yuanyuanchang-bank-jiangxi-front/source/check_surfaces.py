"""Independently probe the serialized brown-brick east street wall and its door recess measured in metres."""
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
ID='huangpu-yuanyuanchang-bank-jiangxi-front'
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
    brick=['brown firebrick and pale joints']
    cement=['warm pale rendered cement']
    mould=['chalk moulding arrises']
    grey=['shaded warm grey cement']
    for x in [-9.15,-5.77,-3.85,-1.67,1.67,3.85,6.02,8.85]:
        for z in [2.21,6.22,8.34,10.23]:
            face(f'Brick pier {x} z{z}',x,z,brick,.998,1.002)
    for x in [-4.99,4.99]:
        for z in [2.37,3.64,6.72,8.48,10.92]:
            face(f'Pilaster channel {x} z{z}',x,z,grey,.827,.835)
            face(f'Pilaster face {x} z{z}',x+.15,z,cement,.751,.762)
        face(f'Plain square capital tip {x}',x+.64,12.92,cement,.554,.585)
    for x in [-7.42,-2.76,0.,2.76,7.42]:
        face(f'Recessed glass {x}',x+.19,7.17,['smoky recessed glass'],1.33,1.35)
        face(f'Pale sill {x}',x,6.435,['worn plinth stone'],.777,.829)
        face(f'Transom {x}',x,8.873,['pale painted sash'],1.13,1.15)
    for x in [-1.86,-1.45,-1.04,1.04,1.45,1.86]:
        face(f'Wing fluting {x}',x,11.69,grey,.766,.782)
        face(f'Wing raised field {x}',x,11.80,cement,.802,.819)
    face('Circular rim on emblem',.699,11.69,mould,.745,.755)
    face('Circular relief field',.28,11.90,cement,.717,.730)
    face('Medallion centre',.015,11.69,grey,.688,.701)
    for x in [-1.18,1.18]:face(f'Entrance stone reveal {x}',x,2.45,['worn plinth stone'],1.145,1.27)
    face('Gate center kick',0,.55,['deep green entrance iron'],1.43,1.46)
    face('Recessed green gate crossbar',.66,3.77,['pale painted sash'],1.38,1.41)
    for x,top in [(-7.10,11.51),(7.10,11.51),(-4.69,13.02),(4.69,13.02),(-1.77,13.52),(1.77,13.52),(0.,14.17)]:
        cast(f'Visible crest or cap at x{x}',[x,-.04,16.],[0,0,-1],6,mould+cement+['shaded warm grey cement'],16-top-.09,16-top+.08)
    for x in (-9.05,-5.8,-3.9,3.9,6.,8.6):
        face(f'Terracotta street foot {x}',x,.20,['faded terracotta skirting'],.94,.956)
    for x in [-9.,-4.99,0.,4.99,9.]:
        cast(f'Unbuilt space over parapet {x}',[x,-.8,14.45],[0,1,0],2.,None)
    for z in [2.18,7.12,11.2]:
        cast(f'No invented rooms behind facade z{z}',[0,1.1,z],[0,1,0],12.,None)
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
