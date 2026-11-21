"""Render two detail views from the SHA-bound uncompressed GLB, using actual material IDs."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import struct

from embreex.mesh_construction import TriangleMesh
from embreex.rtcore_scene import EmbreeScene
import numpy as np
from PIL import Image


def normalize(a):
    a=np.asarray(a,dtype=float)
    return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-8)


def render(scene,tri,materials,colors,name,eye,look,width,height,hfov,out):
    eye=np.asarray(eye,float);look=np.asarray(look,float)
    forward=normalize(look-eye);right=normalize(np.cross(forward,[0.,0.,1.]));up=normalize(np.cross(right,forward))
    output_size=(width,height)
    width*=2
    height*=2
    scale=2*np.tan(np.radians(hfov)/2)/width
    normal=normalize(np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]))
    light=normalize([-.64,-1.,1.20])
    canvas=np.empty((height,width,3),dtype=np.uint8);visible_count=0;hit_faces=set()
    for row in range(0,height,40):
        stop=min(row+40,height)
        u,v=np.meshgrid(np.arange(width)+.5,np.arange(row,stop)+.5)
        rays=normalize(forward+(u.ravel()[:,None]-width/2)*right*scale+(height/2-v.ravel()[:,None])*up*scale).astype('f')
        origin=np.broadcast_to(eye,rays.shape).copy().astype('f')
        ids=scene.run(origin,rays,query='INTERSECT');visible=ids>=0
        depth=scene.run(origin,rays,query='DISTANCE')
        hits=origin[visible]+rays[visible]*depth[visible,None]
        self_shadow=scene.run((hits+.005*light).astype('f'),np.broadcast_to(light,hits.shape).copy().astype('f'),query='DISTANCE')
        intensity=.48+.54*np.abs(normal[ids[visible]]@light)*np.where((self_shadow>0)&(self_shadow<80),.16,1.)
        pixels=np.broadcast_to([.40,.46,.51],(len(rays),3)).copy()
        pixels[visible]=np.clip(np.maximum(0,colors[materials[ids[visible]]]*intensity[:,None])**(1/2.2),0.,1.)
        canvas[row:stop]=np.uint8(pixels.reshape(stop-row,width,3)*255)
        visible_count+=int(visible.sum());hit_faces.update(np.unique(ids[visible]))
    image=out/(name+'.jpg')
    Image.fromarray(canvas).resize(output_size,Image.Resampling.LANCZOS).save(image,quality=92)
    return dict(file=image.name,sha256=hashlib.sha256(image.read_bytes()).hexdigest(),camera=eye.tolist(),look_at=look.tolist(),horizontal_fov_deg=hfov,visible_antialias_samples=visible_count,first_hit_triangles=len(hit_faces))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('manifest',type=Path);parser.add_argument('out',type=Path);args=parser.parse_args()
    audit=Path(__file__).resolve().parent;g=runpy.run_path(audit.parent/'postal-office-v1/independent-glb-review-helpers.py')
    doc=json.loads(args.manifest.read_bytes());raw=args.manifest.parent/doc['assets']['raw']['file'];data=raw.read_bytes()
    assert hashlib.sha256(data).hexdigest()==doc['assets']['raw']['sha256']
    hdr=json.loads(data[20:20+struct.unpack_from('<I',data,12)[0]])
    colors=np.array([m['pbrMetallicRoughness']['baseColorFactor'][:3] for m in hdr['materials']])
    tri,materials,_,_=g['load_triangles'](raw);scene=EmbreeScene();mesh=TriangleMesh(scene,tri.astype('f'))
    args.out.mkdir(exist_ok=True,parents=True)
    shots=[]
    for rec in [('entrance-and-canopy',[4.5,-25.3,3.40],[0,0,3.88],42),('recessed-coffers',[8.9,-2.64,1.60],[-1.3,-1.97,3.62],58)]:
        name,eye,look,fov=rec
        shots.append(render(scene,tri,materials,colors,name,eye,look,680,410,fov,args.out))
    report=dict(id=doc['id'],raw_sha256=doc['assets']['raw']['sha256'],triangles=len(tri),script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),shots=shots)
    (args.out/'entrance-detail.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
