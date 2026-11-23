"""Cast independent geographic-metre rays against all three decoded Lane 553 inscribed balcony meshes."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json, os, runpy, subprocess
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
ID='huangpu-fuxing-fang-553-inscribed-balcony'
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
 # Open ground passage, first material either side of each inset and painted letters.
 for x in [-1.4,-1.15,-.8,-.44,0,.4,.8,1.15,1.4]:
  for z in [.06,1.56,2.18,3.54]:cast('clear lane beneath the balcony',(x,-.85,z),(0,1,0),2.3,[])
 for x in [-.73,-.55,-.325,-.075,.136,.34,.56,.727]:
  for z,m in [(3.96,'lower concrete drip'),(4.052,'light stone frame'),(4.10,'grey balcony concrete'),(4.14,'light stone frame'),(4.21,'title panel stone'),(4.805,'title panel stone'),(4.885,'light stone frame'),(4.937,'grey balcony concrete'),(4.97,'light stone frame')]:
   cast('front slab, mouldings and recessed stone',(x,-.75,z),(0,1,0),1,[m])
 for x in [-.62,.62]:
  cast('visible soffit bracket',(x,.80,3.55),(0,0,1),.39,['grey balcony concrete'])
 for x in [-.73,0,.71]:
  cast('terrace floor from above',(x,.50,6.00),(0,0,-1),2.3,['lower concrete drip'])
 for k,(a,c)in enumerate([((-1.22,.35),(-.85,0)),((.85,0),(1.22,.35))]):
  a,c=np.array(a),np.array(c);e=(c-a)/np.linalg.norm(c-a);out=np.array([e[1],-e[0]]);mid=(a+c)/2
  for z,m in [(4.205,'recessed side panel'),(4.50,'recessed side panel'),(4.89,'light stone frame')]:
   cast('folded flank '+str(k),[*map(float,mid+out*.5),z],[*map(float,-out),0],.8,[m])
 for idx,x in enumerate([-.2,.42]):
  for j in range(3,24,3):
   z=5.263+j*.0585+.031
   cast('thin sloping wooden louver',(x,.5,z),(0,1,0),.7,['shutter blade'])
  for z in [6.691,6.705]:cast('upper shutter rail',(x,.6,z),(0,1,0),.7,['dark shutter timber'])
 for x in [-.82,-.64,.849,.973]:
  for row in [4,11,18]:
   cast('street brick and joint',(x,.8,4.978+row*.0875+.033),(0,1,0),.3,['red facing brick','weathered facing brick','brick mortar'])
 letters=json.loads((Path(__file__).with_name('painted-title.json')).read_bytes())['letters']
 for char,outline in letters.items():
  poly=shape(outline);safe=poly.buffer(-.005);pts=[(x,y)for x in np.linspace(poly.bounds[0],poly.bounds[2],20)for y in np.linspace(poly.bounds[1],poly.bounds[3],20)if safe.contains(__import__('shapely').Point(x,y))]
  assert len(pts)>=9,char
  for x,y in pts[::max(1,len(pts)//9)][:9]:cast('painted character '+char,(float(x),-.75,4.516+float(y)),(0,1,0),.77,['red painted inscription'])
  # Crossing the sky between strokes must reach the stone panel at both distances.
  xmin,ymin,xmax,ymax=poly.bounds
  stroke_gap=[]
  for y in np.linspace(ymin+.2*(ymax-ymin),ymax-.17*(ymax-ymin),16):
   for x in np.linspace(xmin+.10*(xmax-xmin),xmax-.10*(xmax-xmin),24):
    point=__import__('shapely').Point(x,y)
    if poly.distance(point)<.007:continue
    line=__import__('shapely').LineString([(xmin,y),(xmax,y)])
    row=poly.intersection(line)
    if row.is_empty:continue
    left,_,right,_=row.bounds
    if left+.02<x<right-.02:stroke_gap.append((float(x),float(y)))
  assert len(stroke_gap)>=9,char
  for x,y in stroke_gap[::max(1,len(stroke_gap)//7)][:7]:
   cast('stone visible between '+char+' strokes',(x,-.75,4.516+y),(0,1,0),.78,['title panel stone'])
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
