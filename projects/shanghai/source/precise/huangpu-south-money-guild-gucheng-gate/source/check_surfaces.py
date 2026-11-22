"""Check the south front, three doors, stone sign, steps and tiled hoods in each independently decoded mesh."""
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
ID='huangpu-south-money-guild-gucheng-gate'
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
    def front(name,x,z,mat,d,eps=.012):
        cast(name,[x,-2.0,z],[0.,1.,0.],2.9,[mat],2.-d-eps,2.-d+eps)
    stone='Worn grey granite steps'; arch='Green grey arch stones';wood='Nearly black timber leaves'
    for i,x in enumerate((-3.99,0.,3.99)):
        half=1.31 if i==1 else 1.
        for dx in (-.46,-.30,.30,.46):
            for z in (1.27,2.10,2.60):
                front(f'Inset closed timber leaf {x}/{dx}/{z}',x+dx,z,wood,-.187)
        for side in (-1,1):
            for z in (1.41,2.01,2.54):
                front(f'Arch stone jamb {x}/{side}/{z}',x+side*(half-.085),z,arch,.049)
        for h,y in [(.145,-1.10),(.290,-.83),(.435,-.55)]:
            cast(f'Threshold riser {x}/{y}',[x,y,.75],[0,0,-1],.72,[stone],.75-h-.005,.75-h+.005)
        z=.48 if i==1 else .42
        cast(f'Door back surface {x}',[x+.35,.49,2.06],[0,-1,0],.57,[wood],.22,.25)
        for side in (-1,1):
            front(f'Iron ring {x}/{side}',x+side*.19,(1.91 if i==1 else 1.79)-.159,'Dark iron ring and bosses',-.098,.05)
    for x in (-9.22,-7.35,-5.85,-2.65,2.63,5.81,7.30,9.19):
        front(f'Lime washed masonry at {x}',x,3.74,'Pale limewashed masonry',0)
        front(f'Blue-grey stone plinth at {x}',x,.75,'Bluish grey stone plinth',.028)
    import sys,shapely
    sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
    from sign_lettering import lettering_shapes
    from shapely.ops import polylabel
    font=SOURCE/'fonts/SouthGuildhallSign.otf'
    for char,poly in lettering_shapes('所公業錢南滬',3.13,.415,font=font):
        parts=sorted(shapely.get_parts(poly.buffer(-.002)),key=lambda g:-g.area)
        for k,part in enumerate(parts[:3]):
            at=polylabel(part,tolerance=.001)
            front(f'Right to left brick letter {char}, stroke {k}',at.x,6.09+at.y,'Raised pale inscription strokes',.226,.006)
    for x in (-2.19,2.19):
        front(f'Small plaque {x}',x,2.425,'Grey carved inscription stone',.073,.015)
        front(f'Plaque upper trim {x}',x,2.615,'Green grey arch stones',.092,.010)
    for x in (-1.82,-1.38,-.63,.08,.79,1.49,1.85):
        if any(abs(x-(-1.70+i*.34))<.085 for i in range(11)):
            front(f'Lower foliage band {x}',x,5.46,'Weathered brick relief',.248,.012)
    for axis,z in [(-6.05,6.48),(0.,7.56),(6.05,6.48)]:
        for offset in (-.34,-.17,0.,.17,.34):
            cast(f'South slope clay tile {axis}/{offset}',[axis+offset,-.23,9.45],[0,0,-1],3.35,['Grey fired pan tiles','Weathered cylindrical cover tiles'],.7,3.2)
            cast(f'North slope clay tile {axis}/{offset}',[axis+offset,1.04,9.45],[0,0,-1],3.35,['Grey fired pan tiles','Weathered cylindrical cover tiles'],.7,3.2)
        cast(f'Caulked ridge {axis}',[axis,.43,10.],[0,0,-1],4.5,['Pale grey raised tile coping'],.45,3.0)
        cast(f'Underside shade {axis}',[axis,-.45,z-.38],[0,0,1],1.4,['Dark timber soffit'],.15,1.1)
    for x in [-9.,-6.95,-.35,6.97,9.]:
        cast(f'Park pavement in front of the stairs {x}',[x,-1.68,7.1],[0,0,-1],7.0,None)
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
            results[role]=result
            print(role,result['count'],[(s['name'],s['hit'])for s in result['samples']if not s['passed']][:8],flush=True)
    answer=dict(id=ID,checker_sha256=digest(Path(__file__)),source_reader_sha256=digest(READER),results=results)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    return all(c['passed']for c in results.values())
if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
