"""Create four architectural finishes without sampling photographic pixels into the images."""
import argparse
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
WALL='cream plaster'
TRIM='gray render'
ARCH='Wukang 129 | grey painted archivolt'
WOOD='Wukang balcony | dark red painted joinery'
SURFACES={WALL:('wukang-cream-render',1.12,[215,206,184],.93,.00045,82401),
          TRIM:('wukang-grey-render',.96,[141,145,144],.86,.00026,82402),
          ARCH:('wukang-painted-arch',.78,[124,132,130],.82,.00014,82403),
          WOOD:('wukang-red-joinery',.68,[103,53,47],.61,.00009,82404)}
FILENAMES={n:v[0]+'.png' for n,v in SURFACES.items()}
NORMAL_FILENAMES={n:v[0]+'-normal.png' for n,v in SURFACES.items()}
REPEAT_METRES={n:[v[1],v[1]] for n,v in SURFACES.items()}
PALETTE={n:dict(color=[1.,1.,1.],texture=str(HERE/FILENAMES[n]),normal=str(HERE/NORMAL_FILENAMES[n]),roughness=v[3]) for n,v in SURFACES.items()}
backend=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('wukang_129_glb_writer',backend)
writer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)
writer.HERE=HERE
writer.STEMS={n:v[0] for n,v in SURFACES.items()}
writer.NORMAL_FILENAMES=NORMAL_FILENAMES
embed_normals=writer.embed_normals

def generate(folder):
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    count=256
    u,v=np.meshgrid(np.arange(count)/count,np.arange(count)/count)
    for mat,(_,period,base,roughness,amplitude,seed) in SURFACES.items():
        rng=np.random.default_rng(seed)
        def field(horizontal,vertical):return writer.field(u,v,horizontal,vertical,rng)
        broad=field(8,9);grain=rng.normal(0,1,u.shape)
        if mat==WALL:
            coarse=field(75,68);variation=1.25*broad+.77*coarse+1.2*grain
            height=.65*coarse+.33*grain
        elif mat==TRIM:
            coarse=field(51,97);variation=.85*broad+.80*coarse+.72*grain
            height=.45*coarse+.30*grain
        elif mat==ARCH:
            grains=field(100,86)+.62*grain
            chips=np.clip(-grains-.69,0,2.0)-.5*np.clip(grains-.87,0,2.0)
            variation=-5.73*chips+1.04*broad+.70*grain;height=.46*chips+.31*grain
        else:
            # A low-contrast streak in the paint follows the local timber direction.
            streak=field(48,5)
            variation=1.02*broad+.87*streak+.55*grain
            height=.48*streak+.20*grain
        rgb=np.asarray(base)+variation[...,None]*[1.,.96,.88]
        Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8')).save(folder/FILENAMES[mat],optimize=True)
        height*=amplitude
        du=(np.roll(height,-1,axis=1)-np.roll(height,1,axis=1))*count/(2*period)
        dv=(np.roll(height,-1,axis=0)-np.roll(height,1,axis=0))*count/(2*period)
        normal=np.stack((-du,dv,np.ones_like(du)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(np.rint((normal+1.)*127.5).astype('uint8')).save(folder/NORMAL_FILENAMES[mat],optimize=True)

def map_finish(part):
    """Give every plane a physical UV and split the vertices at genuine mapping seams."""
    verts=np.asarray(part['vertices']);faces=np.asarray(part['triangles']);corners=verts[faces]
    n=np.cross(corners[:,1]-corners[:,0],corners[:,2]-corners[:,0])
    n/=np.linalg.norm(n,axis=1,keepdims=True)
    t=np.column_stack((-n[:,1],n[:,0],np.zeros(len(n))));t[np.abs(n[:,2])>.999999]=(1.,0.,0.)
    t/=np.linalg.norm(t,axis=1,keepdims=True);up=np.cross(n,t)
    metres=np.stack((np.einsum('fvi,fi->fv',corners,t),np.einsum('fvi,fi->fv',corners,up)),axis=-1)
    uv=np.round(metres/SURFACES[part['material']][1],8)
    unique,new_faces,new_vertices,new_uvs={},[],[],[]
    for ids,coords in zip(faces.tolist(),uv.tolist()):
        row=[]
        for i,pair in zip(ids,coords):
            key=(i,*pair)
            if key not in unique:
                unique[key]=len(new_vertices);new_vertices.append(verts[i].tolist());new_uvs.append(pair)
            row.append(unique[key])
        new_faces.append(row)
    part.update(vertices=new_vertices,triangles=new_faces,texcoords=new_uvs)
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=HERE)
    generate(parser.parse_args().output)
