"""Reread actual triangles for an orthographic study of the entry."""
from pathlib import Path
import json,runpy,sys,struct,hashlib
import numpy as np
from PIL import Image
from embreex.rtcore_scene import EmbreeScene
from embreex.mesh_construction import TriangleMesh
p=Path(__file__).resolve().parents[2]
fn=Path(sys.argv[1]);out=Path(sys.argv[2])
g=runpy.run_path(p/'data/audit/postal-office-v1/independent-glb-review-helpers.py')
tri,mat,names,_=g['load_triangles'](fn);b=fn.read_bytes();j=json.loads(b[20:20+struct.unpack_from('<I',b,12)[0]]);colors=np.array([x['pbrMetallicRoughness']['baseColorFactor'][:3] for x in j['materials']])
scene=EmbreeScene();mesh=TriangleMesh(scene,tri.astype('f'))
def unit(x):
 x=np.array(x,float)
 return x/np.linalg.norm(x)
a=np.array([-4.1214075,-.44]);t=unit(np.array([-36.90109165,37.99145046])-a);door=a+31.35*t
norm=np.array([-t[1],t[0],0.]);eye=unit(norm+np.array([0.,0.,.04]));center=np.array([*door,3.68]);right=unit(np.cross([0.,0.,1.],eye));up=unit(np.cross(eye,right));light=unit(norm+np.array([-.23,.21,1.45]))
W,H=586,490;u,v=np.meshgrid(np.arange(W),np.arange(H));orig=(center+(u.ravel()[:,None]-(W-1)/2)*right*.0142+((H-1)/2-v.ravel()[:,None])*up*.0142+eye*12).astype('f')
dirs=np.broadcast_to(-eye,orig.shape).copy().astype('f');ix=scene.run(orig,dirs,query='INTERSECT');distance=scene.run(orig,dirs,query='DISTANCE')
normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.maximum(1e-8,np.linalg.norm(normal,axis=1))[:,None]
visible=ix>=0;fac=normal[ix[visible]];sh=np.abs(fac@light);hits=orig[visible]+dirs[visible]*distance[visible,None];ln=np.broadcast_to(light,hits.shape).astype('f').copy()
shadow=scene.run((hits+.004*light).astype('f'),ln,query='DISTANCE')
brightness=.40+.63*sh*np.where((shadow>0)&(shadow<40),0.12,1)
canv=np.full((W*H,3),[.46,.52,.56]);canv[visible]=np.clip((colors[mat[ix[visible]]]*brightness[:,None])**(1/2.15),0,1)
im=Image.fromarray(np.uint8(canv.reshape(H,W,3)*255));im.save(out)
print(hashlib.sha256(b).hexdigest(),hashlib.sha256(out.read_bytes()).hexdigest(),len(ix),visible.sum(),len(set(ix[visible])))
