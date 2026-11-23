"""Verify the nine rows, paired crown vents, stone frame and Art Deco ironwork from the serialized mesh."""
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
ID='huangpu-zhongken-bank-239-corner'
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
    glass=['recessed blue grey window'];sill=['upper stone sills'];stone=['pale grey stone facing']
    for j,z in enumerate((11.53,15.12,18.73,22.35,25.94,29.55,33.13,36.73,40.31),1):
        for x in (-1.64,0,1.64):
            face(f'Row {j} window {x}, recessed light',x+.20,z+.09,glass,1.305,1.315)
            face(f'Row {j} window {x}, transom',x+.149,z+.503,['dark window frames'],1.184,1.195)
            face(f'Row {j} window {x}, projecting sill',x+.16,z-1.215,sill,.769,.785)
        for x in (-.835,.835):
            face(f'Row {j} continuous pier at {x}',x,z,['pale stone at the arris'],.842,.858)
    for x in (-.54,.54):face(f'Crown vent at {x}',x,42.92,['entrance recess shadow'],1.252,1.269)
    for x,z in ((0,44.67),(.54,44.58),(1.12,44.43),(1.83,44.24),(2.21,43.96),(2.53,43.51),(2.81,42.78),(3.0,41.67),(3.17,39.32),(3.33,34.52),(3.49,32.1)):
        cast(f'Tower shoulder at {x}',[x,.40,47.],[0,0,-1],18.,stone,47.-z-.08,47.-z+.08)
    for side in (-1,1):
        x=side*1.015
        face(f'Circular door medallion {side}',x+.14,3.17,['black iron entrance rail'],1.137,1.153)
        face(f'Circular medallion raised edge {side}',x+.437,3.12,['weathered raised iron'],1.090,1.126)
        for z in (1.37,4.87):
            face(f'Diamond grille outer tip {side} at {z}',x+.37,z,['weathered raised iron'],1.143,1.199)
        face(f'Upper grille frame {side}',side*1.007,8.44,['black iron entrance rail'],1.15,1.18)
        face(f'Stone door jamb {side}',side*2.17,4.18,['weathered stone relief'],.756,.775)
        face(f'Plain granite block {side}',side*2.51,2.78,['warm ashlar entrance granite'],.865,.880)
        face(f'Lintel diamond {side}',side*2.77,9.98,['weathered stone relief'],.767,.826)
    for j in range(6):
        x=(j-2.5)*.696
        face(f'Former sign bed {j+1}',x,9.82,['old sign plate beds'],.84,.858)
    for x in (-2.8,-1.0,0,1.0,2.8):
        cast(f'Open sky above tower at {x}',[x,-1,44.85],[0,1,0],4,None)
        cast(f'No rooms behind entrance at {x}',[x,1.01,3.42],[0,1,0],3,None)
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
