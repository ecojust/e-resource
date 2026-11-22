"""Cast independent geographic-metre rays against all three decoded church meshes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json, os, runpy, subprocess
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
ID='jingan-xinen-church-west-porch'
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
    for x in (-2.96,-2.57,-.88,.87,2.61,3.10):
        for z in (.81,1.32,2.48,3.46):front('front granite screen piers',x,z,['granite porch'],2.995,3.010)
    for x in (-1.68,0,1.70):
        for d in (-.37,.38):
            for z in (2.41,3.55):front('three dark letter screens',x+d,z,['dark letter screen','crimson characters'],3.28,3.33)
        for z,mat in [(2.223,'granite dressing'),(3.82,'granite dressing')]:front('sill or lintel',x,z,[mat],2.79,2.87)
    for x in (-3.04,-2.63,-1.32,.72,2.16,3.23):
        front('upper drip stone',x,5.238,['granite dressing'],2.79,2.85)
        front('English inscription tablet',x,4.66,['weathered fascia','incised lettering'],2.95,2.99)
    for side in (-1,1):
        for y in (2.04,2.62,3.23,3.85,4.44):
            for z in (.48,1.54,2.33):
                sample('north and south open arch clear', (side*4.92,y,z),(-side,0,0),2.0,[])
        for y in (.45,.74,5.75,5.99):
            for z in (.91,1.55,2.03):
                sample('solid side arch pier',(side*4.90,y,z),(-side,0,0),2.65,['granite porch'],1.20,1.27)
        for y in (1.16,2.31,3.23,4.2,5.16):
            sample('side arch superstructure',(side*4.9,y,4.43),(-side,0,0),2.6,['weathered fascia'],1.15,1.27)
    for x in (-2.22,-1.47,-.77,-.14,.66,1.42,2.13):
        for z in (6.84,7.21,7.79):
            front('three-light Gothic glass',x,z,['grey glazing','green grey glazing'],9.472,9.51)
    for x in (-1.03,1.11):
        for z in (6.86,7.16,7.82,8.19):front('granite vertical mullions',x,z,['granite dressing'],9.218,9.237)
    for x in (-1.9,-.48,.37,1.93):
        for z in (6.87,7.27):front('metal glazing bars',x,z,['iron frame'],9.382,9.41)
    for x in (-4.15,-3.54,3.64,4.42):
        for z in (6.82,7.92,8.31):front('exposed blue grey west brick',x,z,['blue grey brick','fine bed joint','brick shading'],9.34,9.37)
    for x in (-.51,-.28,.30,.58):front('red cross arm',x,17.44,['cross red'],9.235,9.26)
    for z in (16.30,16.76,17.95,18.08):front('red cross upright',0,z,['cross red'],9.244,9.274)
    for x in (-4.86,-3.37,3.33,4.98):
        sample('open sky above pitch',(x,-2,15.66),(0,1,0),12,[])
    for x in (-2.1,0,2.2):
        sample('porch paving',(x,3.18,.80),(0,0,-1),1,['paving'],.715,.735)
        sample('porch roof surface',(x,3.18,7),(0,0,-1),3,['grey shingle'],1.81,1.85)
    for side in (-1,1):
        for x in (.95,1.90,2.82):
            sample('short west roof return',(side*x,6.93,20),(0,0,-1),12,['grey shingle','roof course'],3,11)
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
