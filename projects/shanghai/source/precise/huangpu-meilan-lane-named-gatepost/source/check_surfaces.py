"""Cast independent geographic-metre rays against all three decoded Meilan Lane named pier meshes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json, os, runpy, subprocess
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
ID='huangpu-meilan-lane-named-gatepost'
HELPER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
UNPACK=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
Reader=runpy.run_path(str(HELPER))['SerialScene']
def digest(f):return sha256(f.read_bytes()).hexdigest()
def check(scene):
 from pathlib import Path
 from shapely.geometry import shape
 import numpy as np,json
 rows=[]
 def cast(label,origin,direction,dist,materials):
  hit=scene.ray(list(origin),list(direction),dist)
  rows.append(dict(part=label,origin=list(origin),direction=list(direction),maximum=dist,expected=materials,hit=hit,passed=bool(hit and hit['material'] in materials)if materials else hit is None))
 for x in [-.276,0,.276]:
  for z in [.125,.41,.48,.74,1.03,2.63,3.30,3.45,3.57,3.65]:
   names=['weathered plinth']if z<.44 else ['grey dressed stone','cap stone','recessed stone']
   cast('ashlar pier and cap',(x,-1,z),(0,1,0),2,names)
 for x in [-1.40,-.99,-.82,-.46]:
  cast('coping above plaque wall',(x,.19,3),(0,0,-1),1.0,['cap stone'])
 for x in [-.21,0,.20]:
  cast('pier top',(x,.28,4.2),(0,0,-1),1.,['grey dressed stone'])
 for x,z,m in [(-.939,2.123,'nameplate green'),(-.445,2.185,'nameplate green'),(-.70,1.677,'pale metal plaque'),(-.441,1.644,'pale metal plaque'),(-.688,1.332,'antique brass'),(-.422,.922,'antique brass'),(-.55,.94,'notice backing'),(-1.15,1.83,'antique brass'),(-.373,2.241,'red lamp lens'),(-.373+.052,2.241,'lamp silver bezel')]:
  cast('plaque wall and fittings',(x,-1,z),(0,1,0),2,[m])
 d=json.loads((Path(__file__).with_name('named-letter-shapes.json')).read_bytes())['letters']
 for char,center in [('梅',2.256),('兰',1.856),('坊',1.355)]:
  poly=shape(d[char]['geometry']);safe=poly.buffer(-.002)
  points=[(x,y)for x in np.linspace(poly.bounds[0],poly.bounds[2],19)for y in np.linspace(poly.bounds[1],poly.bounds[3],21)if safe.contains(__import__('shapely').Point(x,y))]
  for x,y in points[::max(1,len(points)//12)][:12]:cast('raised gilt inscription '+char,(float(x),-1,center+float(y)),(0,1,0),1.005,['gilt lettering'])
 for x in [.43,.72,1.1,1.65,2.2,2.63]:
  for z in [.06,1.48,3.1]:cast('reserved lane opening',(x,-1,z),(0,1,0),2,[])
 for x,z in [(-.16,.92),(.12,2.41),(-.8,1.29),(-1.34,1.77)]:cast('reverse face from the courtyard',(x,1.1,z),(0,-1,0),1.4,['grey dressed stone','recessed stone'])
 return dict(passed=all(v['passed']for v in rows),samples=rows)
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
