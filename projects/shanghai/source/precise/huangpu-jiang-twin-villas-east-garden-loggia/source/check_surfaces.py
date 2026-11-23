"""Re-read each sealed GLB and probe the portico, its perforations, glazing and eave."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json, os, runpy, subprocess
HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ.get('SHANGHAI_PROJECT_ROOT',HERE.parents[3]))
MODEL='huangpu-jiang-twin-villas-east-garden-loggia'
HELPER=PROJECT/'data/audit/postal-office-v1/independent-glb-review-helpers.py'
AT=PROJECT/'source/precise/hongkou-general-post-office/source/decode_meshopt.mjs'
DECODER=PROJECT/'vendor/meshopt_decoder.module.js'
Reader=runpy.run_path(str(HELPER))['SerialScene']
def sig(p):return sha256(p.read_bytes()).hexdigest()
def check(reader):
 rows=[]
 def ray(name,p,d,want,limit=6):
  hit=reader.ray(p,d,limit)
  ok=(hit is None) if not want else bool(hit and hit['material'] in want)
  rows.append(dict(part=name,origin=p,direction=d,wanted=want,maximum=limit,hit=hit,passed=ok))
 def front(name,x,z,materials,limit=4):ray(name,[x,-1.15,z],[0,1,0],materials,limit)
 for z in [.37,1.51,2.84,3.85,4.79,5.81,6.68,8.51,9.43,10.27]:
  front('square pier shaft',.67,z,['pale carved stone'])
 for base,top,deck in [(0.,4.198,4.574),(4.574,7.707,8.083),(8.083,11.403,11.779)]:
  for h in [.47,.98,1.61,2.28]:
   front('garden column shaft',3.935,base+h,['pale carved stone'])
  for height in [top+.04,top+.10,top+.18,deck-.03]:
   front('moulded fascia',1.80,height,['pale carved stone','limestone edge'])
  # Springs of the rail sit at +.044 above the gallery level.
  left=.88;right=3.935-.20;pitch=(right-left)/14
  for i in [0,3,6,9,12]:
   x=left+(i+.5)*pitch
   front('turned vase body',x,base+.433,['pale carved stone'])
   front('open void between adjacent vases',x+pitch/2,base+.435,[],1.64)
  # The chosen ray meets the real rear facade only after passing the open gallery.
  front('render between sash windows',2.16,base+1.68,['warm stucco'])
  for c,w in [(1.11,.74),(3.32,.82)]:
   z=base+1.61
   ray('rear glass',[c+w*.23,1.31,z],[0,1,0],['deep grey glazing','upper glass'],2)
   ray('glazing bar',[c,1.31,z],[0,1,0],['light window frames'],2)
   ray('recessed window jamb',[c-w/2+.018,1.31,z],[0,1,0],['light window frames'],2)
  ray('continuous stone soffit',[2.06,1.08,top-.38],[0,0,1],['shade plaster'],.48)
  ray('external intercolumniation remains open',[2.19,-.80,base+2.08],[0,1,0],[],2.6)
 for z in [12.08,12.55,13.12]:
  front('roof end pier',.485,z,['pale carved stone'])
 for x in [.83,1.94,2.50,3.61]:
  front('crown cap rail',x,12.51,['pale carved stone'])
 for z in [1.64,5.87,9.19]:
  front('central passage outside registered west edge',-.35,z,[])
 ray('garden threshold',[2.12,1.08,.64],[0,0,-1],['gallery paving'],1.)
 return dict(passed=all(v['passed'] for v in rows),samples=rows)
def main():
 cli=ArgumentParser();cli.add_argument('--manifest',type=Path,required=True);cli.add_argument('--out',type=Path,required=True);a=cli.parse_args();m=json.loads(a.manifest.read_bytes());assert m['id']==MODEL;res={}
 with TemporaryDirectory()as t:
  for role in ('raw','full','lod'):
   rec=m['assets'][role];asset=a.manifest.parent/rec['file'];assert sig(asset)==rec['sha256'];f=asset
   if role!='raw':
    f=Path(t)/(role+'.glb');subprocess.run(['node',AT,asset,f,DECODER],check=True,stdout=subprocess.DEVNULL)
   res[role]=dict(asset=sig(asset),**check(Reader(f)))
 proof=dict(id=MODEL,manifest_sha256=sig(a.manifest),checker_sha256=sig(Path(__file__)),reader_sha256=sig(HELPER),results=res)
 a.out.write_text(json.dumps(proof,indent=2)+'\n')
 return all(r['passed'] for r in res.values())
if __name__=='__main__':raise SystemExit(0 if main() else 1)
