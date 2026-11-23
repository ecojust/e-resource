"""Cast independent geographic-metre rays against all three decoded Lane 198 Ruijin entrance meshes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json, os, runpy, subprocess, math
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
ID='huangpu-anhe-terrace-ruijin-gate'
HELPER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
Reader=runpy.run_path(str(HELPER))['SerialScene']
def digest(f):return sha256(f.read_bytes()).hexdigest()
def check(scene):
    rows=[]
    def shoot(label,x,y,z,direction,expected,dist=1.75):
        hit=scene.ray([x,y,z],direction,dist)
        passed=bool(hit and hit['material'] in expected) if expected else hit is None
        rows.append(dict(part=label,origin=[x,y,z],direction=direction,expected=expected,maximum=dist,hit=hit,passed=passed))
    hf=4.09/2
    for side,w in [(-1,.91),(1,.94)]:
        center=side*(hf+w/2)
        for x in (center-.15,center+.13):
            for z in (.29,.69,1.21,2.93,3.04,3.26,3.70,3.89,4.011):
                mats=['grey coping','cap shadow'] if z>3.8 or 3.0<z<3.16 else ['mineral grey render','coarse exposed aggregate']
                shoot('cast pier courses',x,-1,z,[0,1,0],mats)
        shoot('flat coping',center,.35,4.7,[0,0,-1],['grey coping'])
        shoot('courtyard side of post',center,1.4,.9,[0,-1,0],['mineral grey render','coarse exposed aggregate'])
    for z,names in [(2.79,['green enamel']),(2.235,['white enamel']),(1.898,['white enamel','blue address ink'])]:
        shoot('street number plates',-hf-.455+.12,-.5,z,[0,1,0],names)
    for side,(left,right) in enumerate([(-hf+.027,-.045),(.045,hf-.027)]):
        for z in (.11,1.385,1.607,2.606,2.85):
            shoot('leaf retaining rail',(left+right)/2,-.6,z,[0,1,0],['black enamel'])
        for i in range(5):
            x=left+(right-left)*(i+.5)/5;w=(right-left)/5*.61
            shoot('paired lattice upright',x+w/2,-.6,1.79,[0,1,0],['black enamel'])
            shoot('open rectangle beside the scroll',x+w*.69,-.6,.55,[0,1,0],[])
            shoot('gilded spear point',x,-.6,2.995,[0,1,0],['weathered brass finish'])
            xx=x+w*.14+w*.30*math.cos(-math.pi*.67)
            zz=.819+.96*.22+.96*.205*math.sin(-math.pi*.67)
            shoot('lower gold return',xx,-.6,zz,[0,1,0],['weathered brass finish'])
    for x in (-.6,.0,.6):
        shoot('open flagstones behind leaf',x,1.03,1.2,[0,1,0],[],1.8)
    shoot('gap at meeting edges',0,-.65,1.94,[0,1,0],[])
    shoot('interior side of rail',.65,1.1,2.85,[0,-1,0],['black enamel'])
    return dict(passed=all(row['passed'] for row in rows),samples=rows)
def main():
    parser=ArgumentParser();parser.add_argument('--manifest',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args();j=json.loads(args.manifest.read_bytes());assert j['id']==ID;roles={}
    with TemporaryDirectory()as d:
        for role in ('raw','full','lod'):
            a=j['assets'][role];f=args.manifest.parent/a['file'];assert digest(f)==a['sha256'] and f.stat().st_size==a['bytes'];g=f
            if role!='raw':
                g=Path(d)/(role+'.glb');subprocess.run(['node',UNPACK,f,g,DECODER],stdout=subprocess.DEVNULL,check=True)
            roles[role]=dict(asset=a['sha256'],**check(Reader(g)))
            if role!='raw':g.unlink()
    out=dict(id=ID,manifest_sha256=digest(args.manifest),checker_sha256=digest(Path(__file__)),reader_sha256=digest(HELPER),results=roles);args.out.write_text(json.dumps(out,indent=2)+'\n');return all(r['passed']for r in roles.values())
if __name__=='__main__':raise SystemExit(0 if main()else 1)
