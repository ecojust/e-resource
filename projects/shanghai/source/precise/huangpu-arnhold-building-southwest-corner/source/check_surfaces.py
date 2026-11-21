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
ID='huangpu-arnhold-building-southwest-corner'
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
    from math import sin,cos,pi,atan2,tan
    tangent=np.array([.058299,-.998299]);theta=atan2(-tangent[1],tangent[0]);rad=3.65;vx=-3.643346-2.101508*tangent[0]/tangent[1];du=rad*tan(theta/2);u1=np.array([vx,0])-tangent*du;u0=u1-tangent*12.5
    c=np.array([vx+du,rad]);south_len=18.75-c[0];alen=rad*theta
    def face(side,station,z,name,mat,depth,pad=.009):
        if side=='Sichuan':
            t=(u1-u0)/np.linalg.norm(u1-u0);n=np.array([t[1],-t[0]]);xy=u0+station*t
        elif side=='Jiujiang':n=np.array([0.,-1.]);xy=np.array([c[0]+station,0.])
        else:
            angle=-pi/2-theta+station/rad;n=np.array([cos(angle),sin(angle)]);xy=c+n*rad
            pad=max(pad,.095)
        cast(side+' '+name,[*(xy+1.5*n),z],[*(-n),0],2.4,[mat],1.5-depth-pad,1.5-depth+pad)
    levels=[(4.99,7.42),(8.79,11.34),(12.72,15.22),(16.71,18.73),(20.16,21.92),(23.71,25.39)]
    for side,stations in [('Sichuan',[1.78,5.83,9.94]),('Corner',[alen*.258,alen*.742]),('Jiujiang',[2.02,5.95,9.73,13.24,16.76])]:
        for i,station in enumerate(stations):
            for j,(bottom,top) in enumerate(levels):
                face(side,station-.21,bottom+.36,f'sash {i+1}-{j+2} pane','Smoky street glazing',-.315)
                face(side,station,bottom+.60,f'sash {i+1}-{j+2} vertical rail','Dark sash joinery',-.220)
                # These seven sills carry surveyed air-conditioning units on their right.
                # Cast on the uncovered left half and test the units separately below.
                obscured_right = ((side,i,j) in {
                    ('Sichuan',0,1),('Sichuan',1,2),('Sichuan',1,3),('Corner',0,3),
                    ('Jiujiang',1,1),('Jiujiang',2,0),('Jiujiang',2,2)})
                sill_offset=-.42 if obscured_right else .17
                face(side,station+sill_offset,bottom-.075,f'sash {i+1}-{j+2} sill','Weathered grey sill stone',.1585)
        u=.38 if side!='Corner' else .33
        for low,high in [(7.89,8.21),(11.99,12.32),(15.95,16.25),(19.33,19.64)]:
            face(side,u,(low+high)/2,'white floor belt','Pale cement stringcourses',.057)
        face(side,u,22.96,'projecting entablature','Weathered grey sill stone',.534)
        face(side,u,26.42,'roof cornice','Pale cement stringcourses',.343)
    west=12.5-(10.33-3.43)
    for char,(station,z) in zip('安利大楼',[(4.94185, 3.5271), (5.27686, 3.4312), (5.80913, 3.43628), (6.316, 3.50744)]):
        face('Sichuan',station,z,'320 portal character '+char,'Old gold building letters',.157)
    for side,station,z in [('Sichuan',2.05,8.57),('Sichuan',6.10,12.50),('Sichuan',6.10,16.57),
                           ('Jiujiang',6.25,8.58),('Jiujiang',10.24,4.78),('Jiujiang',10.19,12.51)]:
        face(side,station+.29,z+.19,'condenser front panel','Weathered condenser steel',.46)
    for side,station in [('Jiujiang',4.1),('Corner',alen*.62),('Sichuan',6.9)]:
        face(side,station,27.30,'upper guard rail','Black drainpipes and roof iron',-.101,pad=.018)
    for dx in [-.49,.51]:
        face('Sichuan',west+dx,1.61,'two inner door lites','Smoky street glazing',-.421)
    face('Sichuan',west,1.62,'double door joint','Dark sash joinery',-.276)
    face('Sichuan',west+1.40,1.77,'light door jamb','Pale cement stringcourses',.2535)
    face('Sichuan',west+1.65,1.60,'municipal plate','Street-level ashlar',.139)
    face('Sichuan',west,3.79,'outer door lintel','Weathered grey sill stone',.355)
    for side,u in [('Sichuan',10.4),('Corner',alen*.64),('Jiujiang',5.2)]:
        face(side,u,3.91,'continuous blue corner fascia','Blue metal street fascia',.185)
    south=16.55
    face('Jiujiang',south,3.43,'carved crown stone','Pale cement stringcourses',.216)
    face('Jiujiang',south+.12,1.82,'deep ashlar entry','Dark window recess',-.682)
    face('Jiujiang',south-1.13,1.56,'rusticated arch side','Street-level ashlar',.123)
    face('Corner',alen*.258+.1,16.56,'air conditioner grille','Dark sash joinery',.471)
    for x,y in [(7.32,1.4),(15.62,1.1),(-2.90,9.6)]:
        cast('street ribbon roof',[x,y,29.], [0,0,-1],4.,['Dark roof flashing'],2.51,2.55)
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
            result['brick_uv']=runpy.run_path(str(PROJECT/'data/audit/arnhold-building-southwest-corner-v1/check-brick-sampling.py'))['sample'](path)
            results[role]=result
            print(role,result['count'],[(s['name'],s['hit'])for s in result['samples']if not s['passed']][:8],flush=True)
    answer=dict(id=ID,checker_sha256=digest(Path(__file__)),source_reader_sha256=digest(READER),results=results)
    a.out.write_text(json.dumps(answer,ensure_ascii=False,indent=2)+'\n')
    return all(c['passed']for c in results.values())
if __name__=='__main__':
    raise SystemExit(0 if main() else 1)
