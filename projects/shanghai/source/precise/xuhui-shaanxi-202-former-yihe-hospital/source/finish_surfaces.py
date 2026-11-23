"""Original tileable finishes for the courtyard masonry, granite door surround, and dressed steps."""
import argparse
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
WALL='Yihe | buff courtyard masonry'
ASHLAR='Yihe | grey granite ashlar'
STEP='Yihe | grey step granite'
# The model carries the architectural courses. These periods belong to the
# grain field and do not repeat a second set of beds or door joints.
SURFACES={
    WALL:('yihe-buff-masonry',1.84,(195,192,178),.94,.00042,81211),
    ASHLAR:('yihe-grey-granite-ashlar',1.26,(171,169,158),.90,.00083,81212),
    STEP:('yihe-dressed-step-granite',1.52,(159,155,145),.91,.00047,81213),
}
FILENAMES={mat:rec[0]+'.png' for mat,rec in SURFACES.items()}
NORMAL_FILENAMES={mat:rec[0]+'-normal.png' for mat,rec in SURFACES.items()}
REPEAT_METRES={mat:(rec[1],rec[1]) for mat,rec in SURFACES.items()}
shared=HERE.parents[1]/'xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('yihe_relief_maps',shared)
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
writer.HERE=HERE;writer.STEMS={k:v[0] for k,v in SURFACES.items()};writer.NORMAL_FILENAMES=NORMAL_FILENAMES
embed_normals=writer.embed_normals
PALETTE={k:dict(color=[1.,1.,1.],roughness=v[3],texture=str(HERE/FILENAMES[k]),
                normal=str(HERE/NORMAL_FILENAMES[k])) for k,v in SURFACES.items()}

def map_finish(part):
    """Project each actual triangle onto orthonormal face axes, in metres."""
    mat=part['material']
    if mat not in SURFACES:return
    p=np.array(part['vertices'],dtype=float);old=part['triangles'];uv=[];verts=[];faces=[];cache={}
    for face in old:
        a,b,c=p[list(face)];normal=np.cross(b-a,c-a);normal/=np.linalg.norm(normal)
        if abs(normal[2])>.999999:
            u=np.array([1.,0.,0.]);v=np.cross(normal,u)
        else:
            u=np.array([-normal[1],normal[0],0.]);u/=np.linalg.norm(u);v=np.cross(normal,u)
        axes=tuple(np.round(np.r_[u,v],6));new=[]
        for index in face:
            key=(index,axes)
            if key not in cache:
                cache[key]=len(verts);verts.append(p[index].tolist())
                uv.append([float(p[index]@u)/SURFACES[mat][1],float(p[index]@v)/SURFACES[mat][1]])
            new.append(cache[key])
        faces.append(new)
    part.update(vertices=verts,triangles=faces,texcoords=uv)

def generate(output):
    output.mkdir(exist_ok=True,parents=True);n=256
    u,v=np.meshgrid(np.arange(n)/n,np.arange(n)/n)
    for mat,(stem,repeat,base,rough,grain,seed) in SURFACES.items():
        rng=np.random.default_rng(seed)
        broad=writer.field(u,v,7,9,rng);small=writer.field(u,v,83,79,rng)
        grains=rng.normal(0.,1.,(n,n));aggregate=np.maximum(grains-.90,0)
        if mat==WALL:
            value=1.05*broad+.85*small+.70*grains;field=.35*broad+.74*small+.22*grains
        elif mat==ASHLAR:
            value=1.15*broad+2.4*small+2.2*grains-7.*aggregate;field=.30*broad+.55*small+.85*grains
        else:
            rubbed=writer.field(u,v,18,91,rng)
            value=.82*broad+1.3*small+1.8*grains-5.4*aggregate+.60*rubbed;field=.20*broad+.57*small+.40*grains+.20*rubbed
        image=np.rint(np.clip(np.array(base)+value[...,None],0,255)).astype('uint8')
        relief=grain*field
        dx=(np.roll(relief,-1,1)-np.roll(relief,1,1))*n/(2*repeat)
        dv=(np.roll(relief,-1,0)-np.roll(relief,1,0))*n/(2*repeat)
        normal=np.stack([-dx,dv,np.ones_like(dx)],axis=2);normal/=np.linalg.norm(normal,axis=2)[...,None]
        Image.fromarray(image).save(output/FILENAMES[mat],optimize=True)
        Image.fromarray(np.rint((normal+1)*127.5).astype('uint8')).save(output/NORMAL_FILENAMES[mat],optimize=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=HERE);generate(ap.parse_args().output)
