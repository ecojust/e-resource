"""Test real first-hit materials and outward faces on the three signed street elevations; no builder objects are consulted."""
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
ID='huangpu-hengli-bank-henan-tianjin-corner'
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
    edges={'South':((-15.8184,0.),(0.,0.)),'Corner':((0.,0.),(2.8775,3.2731)),'East':((2.8775,3.2731),(.8376,32.4104)),'Upper S':((-11.65,6.54),(-2.16,6.54)),'Upper E':((-2.16,6.54),(-2.16,15.95))}
    def face(side,u,z,name,mat,depth,pad=.008):
        a,b=map(np.asarray,edges[side]);t=(b-a)/np.linalg.norm(b-a);normal=np.array([t[1],-t[0]])
        xy=(a+b)/2+t*u+normal*1.5
        cast(side+' '+name,[float(xy[0]),float(xy[1]),z],[-float(normal[0]),-float(normal[1]),0.],2.25,[mat],1.5-depth-pad,1.5-depth+pad)
    glass='Blue-grey street glazing';frame='Charcoal window joinery';brick='Hengli dark fired brick';pale='Pale spandrel relief';stone='Off-white cast cement'
    levels=[(6.13,7.73),(9.11,10.86),(12.40,13.80),(15.82,17.13)]
    # Sample every measured sash, with a stable point in the opening above each sill.
    # Expected obstructions are checked separately against their exact material and depth.
    equipment={('East',1,2),('East',2,2),('East',3,2),('East',5,2),('East',6,1),('East',11,2),('South',2,3),('South',4,3)}
    for side,first,pitch,bays in [('South',-15.8184/2+4.47,1.46,6),('East',-29.20857/2+.38,1.37,18)]:
        for i in range(bays):
            x=first+(i+.5)*pitch
            for n,(lo,hi)in enumerate(levels):
                if (side,i,n) in equipment:continue
                face(side,x+(-.20 if (side,i,n) in {('East',1,1),('East',2,3)} else .20),lo+.44,f'bay {i+1} level {n+1} recessed pane',glass,-.325)
                face(side,x+.15,hi-(hi-lo)*.27+.025,f'bay {i+1} level {n+1} transom',frame,-.216)
            face(side,x+.12,8.50,f'bay {i+1} pale spandrel',pale,.1095)
    for n,(low,hi) in enumerate(levels):
        face('Corner',.21,low+.42,f'central dim pane {n+1}',glass,-.325)
        face('Corner',1.01,low+.22,f'exposed fine brick {n+1}',brick,-.015)
    for side in ['Upper S','Upper E']:
        L=np.linalg.norm(np.subtract(edges[side][1],edges[side][0]))
        for z in [21.82,25.65]:
            for i in [-1,0,1]:
                face(side,i*L*.31+.23,z+.62,f'upper sash at {i}, {z}',glass,-.325)
    for i in [7,9,10,11,12,15,17]:
        x=-29.20857/2+.38+(i+.5)*1.37
        face('East',x+.18,19.64,f'extra front sash {i+1}',glass,-.325)
        if i>=11:face('East',x+.18,22.61,f'highest front sash {i+1}',glass,-.325)
    for x,z,name,mat,depth in [
        (0,4.78,'entrance frieze','Cool plinth stone',.29),
        (0,5.08,'entrance projecting cap',pale,.375),(-1.27,2.22,'stone jamb','Cool plinth stone',.145),
        (-.50,1.12,'double metal door','Age-darkened green bronze',-.226),
        (.27,19.345,'stepped cap',stone,.24),(.55,3.32,'plaque ground','Age-darkened green bronze',-.142)]:
        face('Corner',x,z,name,mat,depth,.012)
    for x,z,name,mat,depth in [(-29.20857/2+13.55+.31,1.03,'brass side entrance','Patinated brass',-.235),(-29.20857/2+13.55+.20,3.10,'brass transom field','Patinated brass',-.21),(-29.20857/2+8.51+.27,5.18,'twin condenser case','Dull grey condenser cases',.46),(-29.20857/2+6.27+.011,5.201,'fan recess','Charcoal window joinery',.471)]:
        face('East',x,z,name,mat,depth,.016)
    for x,y,z,name,mat in [(-6,8,29.13,'observable setback roof','Grey roof flashing'),(-5,2.4,19.14,'continuous lower terrace','Grey roof flashing')]:
        cast(name,[x,y,z+2],[0,0,-1],3,[mat],1.99,2.02)
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
            result['brick_uv']=runpy.run_path(str(PROJECT/'data/audit/hengli-bank-henan-tianjin-corner-v1/check-brick-sampling.py'))['sample'](path)
            results[role]=result
            print(role,result['count'],[(s['name'],s['hit'])for s in result['samples']if not s['passed']][:8],flush=True)
    answer=dict(id=ID,checker_sha256=digest(Path(__file__)),source_reader_sha256=digest(READER),results=results)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    return all(c['passed']for c in results.values())
if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
