from pathlib import Path
from hashlib import sha256
import runpy,json,numpy as np
from PIL import Image,ImageDraw
import sys,tempfile,subprocess
from argparse import ArgumentParser
parser=ArgumentParser(description='Four architectural views from each independently decoded delivery mesh')
parser.add_argument('decoded_directory',type=Path); parser.add_argument('output',type=Path)
opts=parser.parse_args();w=opts.output;w.mkdir(exist_ok=True,parents=True);p=opts.decoded_directory;proj=Path(__file__).resolve().parents[4]
build=tempfile.TemporaryDirectory();library=Path(build.name)/'raster-depth.so';subprocess.run(['cc','-O2','-shared','-fPIC',Path(__file__).with_name('raster-depth.c'),'-o',library,'-lm'],check=True)
SS=runpy.run_path(str(proj/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'];unit=lambda v:np.array(v)/np.linalg.norm(v)
rows=[]
for role in ('full','lod'):
 path=p/('decoded-'+role+'.glb');ss=SS(path);blob=path.read_bytes();doc=json.loads(blob[20:20+int.from_bytes(blob[12:16],'little')]);colors=np.array([m['pbrMetallicRoughness']['baseColorFactor'][:3]for m in doc['materials']])
 for label,way,zlim,canvas in [('east',(.015,-1,.015),(3.65,13.03),(530,670)),('oblique',(.45,-.99,-.14),(3.65,13.03),(570,680)),('title',(.075,-1,.02),(3.67,5.67),(700,275)),('windows',(.13,-.97,.08),(5.48,12.99),(540,600))]:
  toward=unit(way);right=unit(np.cross([0,0,1],toward));up=unit(np.cross(toward,right));tri=ss.tri;cent=tri.mean(1);show=(tri[:,:,2].max(1)>=zlim[0])&(tri[:,:,2].min(1)<=zlim[1]);pr=np.stack((tri@right,-tri@up),axis=-1);corners=np.array([[x,y,z]for x in [-3.62,3.62]for y in [-.48,1.47]for z in zlim]);cuts=np.stack((corners@right,-corners@up),axis=-1);lo=cuts.min(0);hi=cuts.max(0);size=np.array(canvas);scale=min((size-48)/(hi-lo));xy=(pr-(lo+hi)/2)*scale+size/2;norm=ss.cross/np.maximum(np.linalg.norm(ss.cross,axis=1)[:,None],1e-12);lighting=.77+.23*np.maximum(0,norm@unit([-.48,-.94,.72]));rgb=np.uint8(np.clip(255*colors[ss.mi]*lighting[:,None],0,255))
  import ctypes
  rf=ctypes.CDLL(str(library)).raster
  rf.argtypes=[ctypes.c_int]*3+[ctypes.c_void_p]*6
  depths=np.ascontiguousarray(tri@toward,dtype=np.float64); screen=np.ascontiguousarray(xy,dtype=np.float64)
  image=np.full((canvas[1],canvas[0],3),[232,230,223],dtype=np.uint8); zbuffer=np.full(image.shape[:2],-np.inf,dtype=np.float64)
  arrs=[screen,depths,np.ascontiguousarray(show,dtype=np.uint8),np.ascontiguousarray(rgb,dtype=np.uint8),zbuffer,image]
  rf(len(tri),*canvas,*[v.ctypes.data for v in arrs])
  im=Image.fromarray(image)
  file=w/(role+'-'+label+'.png');im.thumbnail((485,585),Image.Resampling.LANCZOS);im.save(file,optimize=True);rows.append(dict(role=role,view=label,file=file.name,sha256=sha256(file.read_bytes()).hexdigest(),mesh_sha256=sha256(blob).hexdigest(),direction=way,elevation_crop=zlim))
(w/'rendered-actual-meshes.json').write_text(json.dumps(rows,indent=1)+'\n')
