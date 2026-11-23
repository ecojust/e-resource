"""Cast independent geographic-metre rays against all three decoded Nanchang Road house entrance meshes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json, os, runpy, subprocess
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
ID='huangpu-park-terrace-nanchang-124-portal'
HELPER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
Reader=runpy.run_path(str(HELPER))['SerialScene']
def digest(f):return sha256(f.read_bytes()).hexdigest()
def check(scene):
    rows=[]
    def sample(label,origin,direction,maximum,materials,low=0,high=30):
        h=scene.ray(list(origin),list(direction),maximum)
        ok=(h is None)if not materials else bool(h and h['material']in materials and low<=h['distance_m']<=high)
        rows.append(dict(part=label,origin=origin,direction=direction,maximum=maximum,materials=materials,interval=(low,high),hit=h,passed=ok))
    from math import pi,cos,sin
    # Start between the outer gate and the dwelling for its threshold and transom.
    for i in range(1,14):
        a=i*pi/14
        for radius,lo,hi,mats in [(.614,.21,.29,['cream moulding']),(.66,.21,.31,['cream moulding']),(.711,.20,.31,['cream moulding'])]:
            sample('continuous projecting arch bead',(radius*cos(a),-.30,3.28+radius*sin(a)),(0,1,0),2,mats,lo,hi)
    for x in (-.757,.757):
        for z in (.12,.72,1.22,2.88,3.18):
            mats=['dressed base']if z==.12 else ['cream moulding']
            sample('flanking pilaster face',(x,-.30,z),(0,1,0),2,mats,.19,.29)
    for x in (-.405,-.135,.135,.405):
        for z in (2.59,2.798):
            sample('individual transom pane',(x,-.25,z),(0,1,0),1,['shadowed window'],.570,.590)
    for x in (-.37,.13,.35):
        sample('inner iron door',(x,-.3,1.3),(0,1,0),1,['painted iron','worn iron edge'],.61,.70)
    for x,y,h in ((-.35,-.68,2.50),(1.79,-.9,2.59)):
        for z in (.13,.52,.91,1.33,1.82):
            sample('separate street pier',(x+.14,-3,z),(0,1,0),4,['dressed base','wash sandstone','sheltered plaster'],1.80,2.12)
        for dx in (-.06,.06):
            sample('top cap from above',(x+dx,y,3.7),(0,0,-1),2.0,['cream moulding'],3.70-h-.015,3.70-h+.015)
    for x,z in ((1.685,1.658),(1.89,1.66),(1.675,1.855)):
        sample('green house number enamel',(x,-3,z),(0,1,0),3,['enamel green'],1.82,1.85)
    for x in (.04,.33,.9,1.35):
        for z in (.30,.75,1.10,1.61,1.97):
            sample('closed black street gate',(x,-3,z),(0,1,0),4,['painted iron'],1.97,2.36)
    for x in (-1.3,2.26):
        for z in (.34,1.77,3.30):sample('outside documented facade is empty',(x,-3,z),(0,1,0),6,[],0,0)
    sample('unbuilt upper floors',(0,-3,4.16),(0,1,0),6,[],0,0)
    for x,y in [(-.35,-.68),(1.79,-.90)]:
        for z in (.53,.95,1.31,1.53):
            sample('grey painted stripe on separate stone course',(x,y-.50,z),(0,1,0),.6,['pale grey pier stripe'],.249,.26)
    return dict(passed=all(r['passed']for r in rows),samples=rows)
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
