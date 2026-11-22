"""Test real first-hit materials and outward faces on the masonry, lamps, two iron leaves and the open Jintan Road lane; no builder objects are consulted."""
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
ID='huangpu-jixian-terrace-jintan-gate'
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
    stone='Weathered pale grey render';cap='Warmer projecting stone moulding'
    iron='Black painted iron';edge='Weathered iron highlights'
    for side in (-1,1):
        u=1.975*side
        for x in [u-.235,u,u+.235]:
            for z in [.81,1.20,1.62,2.10,2.58]:
                front(f'Vertical plaque {x}/{z}',x,z,'Reddish brown plaque backing',.152)
        for x in [u-.22,u,u+.22]:
            front('Plinth '+str(x),x,.21,stone,.12)
            front('Stone plaque head '+str(x),x,2.88,cap,.15)
            front('Terminal capital '+str(x),x,5.06,stone,.175)
        front('Raised pier relief '+str(side),u,4.32,cap,.144)
        front('Lantern glazing '+str(side),u,3.15,'Warm grey lantern glazing',.385,.10)
        front('Lantern eaves '+str(side),u,3.29,iron,.414,.01)
        cast('Lamp roof '+str(side),[u,-.285,3.53],[0,0,-1],.43,[iron],.125,.15)
        cast('Back of a pier '+str(side),[u,1.,2.025],[0,-1,0],1.3,[stone],.465,.49)
    for x in [-1.35,-.91,-.57,-.31,0,.39,.62,1.00,1.37]:
        spring=3.80-.31*(x/1.60)**2
        cast(f'Up to shallow soffit {x}',[x,.213,2.93],[0.,0.,1.],1.50,['Shaded underside of the lintel'],spring-2.943,spring-2.917)
        front('Head field '+str(x),x,4.18,stone,.015)
        cast(f'Air below the arch {x}',[x,-1.5,3.32],[0.,1.,0.],1.72,None)
    for x in [-.80,0,.80]:
        front('Tablet edge '+str(x),x+.201,4.82,'Muted slate inscription tablet',.061)
    # Independently recover two inside-of-stroke sample points from each licensed glyph;
    # the shaft is then cast on the decoded export, including physical letter returns.
    import sys
    sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
    from sign_lettering import lettering_shapes
    for x,char in zip([-.8,0.,.8],'集賢邨'):
        outline=lettering_shapes(char,.34,.36,font=SOURCE/'fonts/JixianGateSign.otf')[0][1]
        import shapely
        from shapely.ops import polylabel
        ink=shapely.buffer(outline,-.0023)
        parts=sorted(shapely.get_parts(ink),key=lambda f:-f.area)
        for k,v in enumerate(parts[:3]):
            witness=polylabel(v,tolerance=.001)
            front(f'Ink {char} {k}',x+witness.x,4.62+witness.y,'Dark traditional inscription',.073,.006)
    for x in [.23,.52,.83,1.10]:
        for z in [.13,.37,.70,1.10,1.78,2.4]:
            cast(f'Open passage {x}/{z}',[x,-1.0,z],[0,1,0],3.3,None)
    angle=np.radians(9);A=np.array([-1.548,.275]);t=np.array([np.cos(angle),np.sin(angle)]);n=np.array([np.sin(angle),-np.cos(angle)])
    for u in [.19,.39,.75,1.18,1.39]:
        xy=A+t*u
        for z in [.12,1.19,2.36]:
            cast(f'West gate rail {u}/{z}',[*list(xy+n*.18),z],[*list(-n),0],.39,[iron],.142,.165)
    for z in [.12,1.19,2.36]:
        # The east gate has been swung inward. Cast east across its projected frame.
        angle=np.radians(84);t=np.array([-np.cos(angle),np.sin(angle)]);normal=np.array([np.sin(angle),np.cos(angle)])
        xy=np.array([1.548,.275])+t*.75
        cast(f'Folded east gate rail {z}',[*list(xy+normal*.20),z],[*list(-normal),0],.42,[iron],.161,.181)
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
