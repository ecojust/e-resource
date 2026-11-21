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
ID='huangpu-russell-company-fuzhou-three-bay-front'
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
    for index,x in enumerate([1.535,4.45,7.365]):
        mat=['Blue east door joinery','Ivory middle door joinery','Black west door joinery'][index]
        base=1.56 if index<2 else 1.29
        for dx in [-.44,-.17,.19,.43]:
            for dz in [.32,.78,1.24]:
                front(f'Door {index+1} recessed pane {dx}/{dz}',x+dx,base+dz,'Dark street door glazing',-.277,origin_d=.76)
        for h in [base+.38,base+.82,base+1.30]:
            front(f'Door {index+1} centre joint {h}',x,h,mat,-.14,origin_d=.76)
        for dx in [-.49,.40]:
            front(f'Door {index+1} fanlight transom {dx}',x+dx,3.76,mat,-.14,origin_d=.76)
        for dx in [-.97,.97]:
            clearance=.025 if index==2 else .065
            xx=x+dx+(clearance if dx>0 else -clearance)
            front(f'Round arch {index+1} dressed jamb {dx}',xx,2.95,'Dark cut stone arch trim',.062,origin_d=.76)
        front(f'Round arch {index+1} high crown',x+.16,4.86,'Dark cut stone arch trim',.062)
        front(f'Round arch {index+1} radial mortar seam',x,4.86,'Pale mortar joints',.073,.006)
        front(f'Pointed hood {index+1} tip',x,9.68,'Dark cut stone arch trim',.085)
        for dx in [(-1.159 if index==0 else -1.10),1.10]:
            front(f'Pointed hood {index+1} vertical leg {dx}',x+dx,7.46,'Dark cut stone arch trim',.085)
        for dx in [-.27,.24]:
            for z in [6.41,6.89,7.32,7.83]:
                front(f'Upper folded bay {index+1} front glass {dx}/{z}',x+dx,z,'Upper sash reflective glass',.468)
        front(f'Upper bay {index+1} central rail',x,7.06,'Aged pale aluminium window frame',.519)
        for dx,z in [(-.854,6.82),(.856,7.23)]:
            # Flat prisms on the splayed returns are behind the forward panes.
            nd=(.51-(abs(dx)-.73)*(.32/.30))-.042*((.32**2+.30**2)**.5/.30)
            front(f'Upper bay {index+1} splayed side {dx}',x+dx,z,'Upper sash reflective glass',nd,.014)
        for z,mat0,d in [(5.955,'Dark iron window and terrace supports',.51),(8.18,'Aged pale aluminium window frame',.51)]:
            front(f'Folded bay {index+1} sill or head at {z}',x+.24,z,mat0,d)
    for dx in [-.123,.123]:front('West small upper fanlight',7.365+dx,8.64,'Upper sash reflective glass',-.067)
    for x,z in [(.63,5.43),(3.32,6.46),(4.45,8.51),(8.32,9.14),(6.32,2.07)]:
        front('Air-conditioning case',x-.19,z+.13,'Pale condenser metal',.34)
        front('Fan dark centre',x+.12,z,'Condenser dark intake',.355)
    for x in [.43,5.98]:
        for z in [3.28,6.14,7.22,8.98]:
            y=.21 if z<4.83 else .15
            front('Painted drainpipe',x,z,'Off-white drain and cable covers',y+.046,.012)
    for x in [.88,2.23,3.53,5.33,6.88,8.22]:
        front('Weathered hood lower band',x,10.62,'Lighter dressed stone arris',.193)
        front('Roof drip edge',x,11.215,'Zinc roof edge and gutter',.773)
        top('Covered roof ribbon',x,1.17,11.1745,'Zinc roof edge and gutter')
    for i in [0,2,4,7,10,14,17]:
        x=.24+.25+i*(8.41-.50)/17
        front(f'Modillion {i+1}',x,10.86,'Weathered pale eave and modillion',.3855)
    for x,z,m,d in [(.96,5.14,'Weathered dark granite ashlar',.009),(4.67,5.17,'Weathered dark granite ashlar',.009),
              (2.94,8.86,'Weathered dark granite ashlar',.009),(5.72,9.76,'Weathered dark granite ashlar',.009),
              (3.91,10.13,'Weathered dark granite ashlar',.009),(5.35,10.43,'Weathered dark granite ashlar',.009)]:
        front('Hewn ashlar face',x,z,m,d)
    for x in [2.01,4.12,5.53]:
        top('Raised landing behind its rail',x,-.81,1.56,'Grey granite landing and stairs')
        top('Front planter stone curb',x,-2.89,.49,'Buff stone planting enclosure')
        front('Painted upper landing rail',x,2.53,'Painted cream landing iron',1.123,.009)
    for i in range(9):
        depth=1.06+(9-i)*.215
        top(f'East granite tread {i+1}',.74,-depth+.096,1.56*(i+1)/9,'Grey granite landing and stairs')
    top('West stone door threshold',7.34,-.43,1.28,'Grey granite landing and stairs')
    for x in [.88,4.45,7.26]:cast('Air above the eaves',[x,-.32,12.17],[0,-1,0],2.,None)
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
            result['stone_uv']=runpy.run_path(str(PROJECT/'data/audit/russell-company-fuzhou-three-bay-front-v1/check-stone-sampling.py'))['sample'](path)
            results[role]=result
            print(role,result['count'],[(s['name'],s['hit'])for s in result['samples']if not s['passed']][:8],flush=True)
    answer=dict(id=ID,checker_sha256=digest(Path(__file__)),source_reader_sha256=digest(READER),results=results)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    return all(c['passed']for c in results.values())
if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
