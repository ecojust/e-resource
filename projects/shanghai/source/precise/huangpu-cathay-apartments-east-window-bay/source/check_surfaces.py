"""Cast independent geographic-metre rays against all three decoded Cathay Apartments facade meshes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json, os, runpy, subprocess
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
ID='huangpu-cathay-apartments-east-window-bay'
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
    def front(label,x,z,mats,low,high):sample(label,(x,-3,z),(0,1,0),14,mats,low,high)
    for layer,(base,head) in enumerate(((5.84,7.69),(9.04,11.04),(12.40,14.70)),2):
        for col in range(4):
            x=-2.04+(col+.5)*.82
            for frac in (.22,.46,.77):
                z=base+(head-base)*frac
                front('glazing behind individually recessed stone lights',x+.09,z,['smoke blue glass','grey glass','muted green glass'],3.105,3.13)
            for z in (base+(head-base)*.39,base+(head-base)*.69) if layer<4 else (base+(head-base)*.54,):
                front('metal horizontal transom',x+.09,z,['dark window frame'],3.03,3.07)
            front('cut stone upper head',x,head+.11,['buff stone'],2.84,2.89)
        for k in (1,2,3):
            for frac in (.38,.79):
                front('stone mullion',-2.04+k*.82,base+(head-base)*frac,['buff stone'],2.84,2.91)
        for x in (-1.88,.94):
            front('continuous stone sill',x,base-.086,['stone lip'],2.77,2.82)
    for z in (6.08,7.04,8.40,9.49,10.82,11.60,12.77,13.64,14.41,15.07):
        front('brown brick over and beside windows',1.84,z,['brown facing brick'],2.998,3.002)
        front('alternating corner quoin',2.66,z,['buff stone'],2.928,2.953)
    for z in (8.94,12.29):
        for delta in (.145,.275,.405):
            for x in (-.92,-.19):
                front('metal enclosure horizontal blades',x,z+delta,['painted rack'],2.501,2.53)
        for x in (-.96,-.13):
            sample('projecting lower shelf under rack',(x,-.35,z-.25),(0,0,1),1,['charcoal sill'],.243,.257)
    for x in (-2.25,-1,0,1,2.2):
        front('front grey cornice moulding',x,15.78,['grey eave trim'],2.54,2.58)
        front('narrow projecting upper drip',x,16.0,['grey eave trim'],2.455,2.51)
        sample('short sloped roof strip from above',(x,.32,18),(0,0,-1),3,['weathered roof'],1.69,1.77)
        for z in (.12,1.55,4.6):front('entire walk zone below partial model remains transparent',x,z,[],0,14)
    for z in (6.2,8.32,10.43,12.52,14.2):
        sample('exposed dark brick short eastern return',(4.7,.74,z),(-1,0,0),3,['brown facing brick'],1.948,1.952)
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
