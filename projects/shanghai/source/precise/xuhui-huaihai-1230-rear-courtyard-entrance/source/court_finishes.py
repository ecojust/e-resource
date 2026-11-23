"""Draw repeatable brick and cement surfaces for the photographed rear block, in physical metres."""
from pathlib import Path
import argparse
import importlib.util
import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
def source_module(name,path):
    spec=importlib.util.spec_from_file_location(name,PROJECT/path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
writer=source_module('huaihai_brick_writer','source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
BRICK='Guangming | warm courtyard brick'
SOLDIER='Guangming | soldier-course facing'
CAST='Guangming | grey precast balcony'
FOOT='Guangming | grey painted base and bands'
SURFACES={
    BRICK:('huaihai-running-bond',(1.332,.648),.90,82801),
    SOLDIER:('huaihai-soldiers',(.648,.444),.90,82802),
    CAST:('huaihai-rail-cement',(.96,.96),.92,82803),
    FOOT:('huaihai-grey-base',(.96,.96),.88,82804),
}
FILENAMES={k:v[0]+'.png' for k,v in SURFACES.items()}
NORMAL_FILENAMES={k:v[0]+'-normal.png' for k,v in SURFACES.items()}
REPEAT_METRES={k:v[1] for k,v in SURFACES.items()}
PALETTE={k:{'color':[1.,1.,1.],'texture':str(HERE/FILENAMES[k]),'normal':str(HERE/NORMAL_FILENAMES[k]),'roughness':v[2]} for k,v in SURFACES.items()}
writer.HERE=HERE
writer.STEMS={k:v[0] for k,v in SURFACES.items()}
writer.NORMAL_FILENAMES=NORMAL_FILENAMES
embed_normals=writer.embed_normals

def map_finish(part):
    # Adjacent faces with different projection axes require separate UV seams.
    position=np.asarray(part['vertices']);faces=np.asarray(part['triangles']);tri=position[faces]
    n=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
    tangent=np.column_stack((-n[:,1],n[:,0],np.zeros(len(n))));tangent[abs(n[:,2])>.99999]=(1.,0.,0.)
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    up=np.cross(n,tangent)
    mapped=np.stack([np.einsum('fvi,fi->fv',tri,v) for v in (tangent,up)],axis=-1)
    uv=np.round(mapped/REPEAT_METRES[part['material']],8)
    vertices=[];texcoords=[];triangles=[];indices={}
    for face,coords in zip(faces.tolist(),uv.tolist()):
        out=[]
        for i,point in zip(face,coords):
            key=(i,*point)
            if key not in indices:
                indices[key]=len(vertices);vertices.append(position[i].tolist());texcoords.append(point)
            out.append(indices[key])
        triangles.append(out)
    part.update(vertices=vertices,texcoords=texcoords,triangles=triangles)

def generate(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    for name,(_,period,_,seed) in SURFACES.items():
        nx,ny=(384,192) if name in (BRICK,SOLDIER) else (192,192)
        iy,ix=np.indices((ny,nx));u=(ix+.5)/nx;v=1-(iy+.5)/ny
        rng=np.random.default_rng(seed)
        field=lambda a,b:writer.field(u,v,a,b,rng)
        fine=field(71,49);broad=field(8,7)
        noise=rng.normal(size=u.shape);x=u*period[0];z=v*period[1]
        if name in (BRICK,SOLDIER):
            body=np.array([196.,145.,109.]);mortar=np.array([221.,197.,166.])
            if name==BRICK:
                width,height=.222,.054
                row=np.floor(z/height).astype(int);xx=x+(row%2)*.111
            else:
                width,height=.054,.222
                row=np.floor(z/height).astype(int);xx=x
            bx=xx%width;bz=z%height
            dist=np.minimum(np.minimum(bx,width-bx),np.minimum(bz,height-bz))
            strength=np.clip((dist-.0024-.00031*fine)/.0025,0,1)
            ids=(row%(12 if name==BRICK else 2))*(6 if name==BRICK else 12)+np.floor(xx/width).astype(int)%(6 if name==BRICK else 12)
            units=rng.normal(0,[4.2,3.2,2.8],(ids.max()+1,3))[ids]
            rgb=(body+units)*strength[...,None]+mortar*(1-strength[...,None])
            rgb+=(2.3*fine+1.65*noise+.98*broad)[...,None]
            relief=.0021*strength+.00020*fine+.00009*noise
        else:
            body=(np.array([167.,167.,158.]) if name==CAST else np.array([153.,153.,147.]))
            rgb=body+(1.9*fine+1.3*broad+.96*noise)[...,None]
            relief=.00030*fine+.00016*noise
        dx=(np.roll(relief,-1,1)-np.roll(relief,1,1))*nx/(2*period[0])
        down=(np.roll(relief,-1,0)-np.roll(relief,1,0))*ny/(2*period[1])
        n=np.stack((-dx,down,np.ones_like(dx)),axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
        Image.fromarray(np.clip(np.rint(rgb),0,255).astype('uint8')).save(directory/FILENAMES[name],optimize=True)
        Image.fromarray(np.rint((n+1)*127.5).astype('uint8')).save(directory/NORMAL_FILENAMES[name],optimize=True)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,default=HERE);generate(cli.parse_args().output)
