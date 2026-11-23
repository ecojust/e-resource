"""Original metric roughcast and painted joinery, informed by the 2017 Changle Road photograph."""
import argparse
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
SHARED=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('changle_metric_materials',SHARED)
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
UPPER='Changle | ochre roughcast above street'
LOWER='Changle | cream roughcast on lower storey'
GREEN='Changle | painted deep green casement'
BASE='Changle | grey rendered plinth'
SURFACES={
    UPPER:('changle-ochre-roughcast',.80,(174,153,121),.0025,7.2),
    LOWER:('changle-cream-roughcast',.80,(211,206,179),.0013,4.8),
    GREEN:('changle-deep-green-paint',.48,(31,48,43),.00016,1.45),
    BASE:('changle-grey-plinth',.64,(116,120,115),.00055,2.8),
}
FILENAMES={m:r[0]+'.png' for m,r in SURFACES.items()}
NORMAL_FILENAMES={m:r[0]+'-normal.png' for m,r in SURFACES.items()}
REPEAT_METRES={m:(r[1],r[1]) for m,r in SURFACES.items()}
PALETTE={m:{'color':[1.,1.,1.],'texture':str(HERE/FILENAMES[m]),'normal':str(HERE/NORMAL_FILENAMES[m]),'roughness':.7 if m==GREEN else .94} for m in SURFACES}
shared.HERE=HERE
shared.STEMS={m:r[0] for m,r in SURFACES.items()}
shared.REPEAT_METRES=REPEAT_METRES
shared.NORMAL_FILENAMES=NORMAL_FILENAMES
def map_finish(part):
    vertices=np.asarray(part['vertices'])
    faces=np.asarray(part['triangles'])
    triangles=vertices[faces]
    normal=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0])
    normal/=np.linalg.norm(normal,axis=1)[:,None]
    tangent=np.column_stack((-normal[:,1],normal[:,0],np.zeros(len(faces))))
    tangent[np.abs(normal[:,2])>.99999]=(1,0,0)
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    up=np.cross(normal,tangent)
    uv=np.stack((np.einsum('fvi,fi->fv',triangles,tangent),np.einsum('fvi,fi->fv',triangles,up)),axis=-1)
    uv=np.round(uv/SURFACES[part['material']][1],8)
    out_vertices=[];out_faces=[];out_uv=[];seams={}
    for face,coords in zip(faces.tolist(),uv.tolist()):
        ids=[]
        for idx,pair in zip(face,coords):
            key=(idx,*pair)
            if key not in seams:
                seams[key]=len(out_vertices)
                out_vertices.append(vertices[idx].tolist())
                out_uv.append(pair)
            ids.append(seams[key])
        out_faces.append(ids)
    part.update(vertices=out_vertices,triangles=out_faces,texcoords=out_uv)

embed_normals=shared.embed_normals

def generate(directory):
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    n=256
    for i,(name,(stem,metres,base,relief,contrast)) in enumerate(SURFACES.items()):
        rng=np.random.default_rng(83200+i)
        def filtered(sigma):
            p=gaussian_filter(rng.normal(size=(n,n)),sigma,mode='wrap')
            return (p-p.mean())/p.std()
        # High-pass measurements in the original show short vertical and slightly
        # longer horizontal surface marks. A periodic field gives the same UV
        # and relief on repeated editable and web exports.
        fine=filtered((.9,1.3));coarse=filtered((2.4,3.8));broad=filtered((13,16))
        if name in (UPPER,LOWER):
            crests=np.tanh(coarse*1.22)
            recess=np.maximum(0,filtered((1.4,2.9))-.68)
            height=relief*(.65*crests+.25*fine-.48*recess)
            albedo=.44*fine+.54*crests-.30*recess+.36*broad
        else:
            height=relief*(.55*fine+.3*coarse+.15*broad)
            albedo=.52*fine+.27*coarse+.37*broad
        rgb=np.asarray(base)+contrast*albedo[...,None]*np.array([1.,.97,.93])
        Image.fromarray(np.clip(np.rint(rgb),0,255).astype('uint8')).save(directory/FILENAMES[name],optimize=True)
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))*n/(2*metres)
        dv=(np.roll(height,-1,0)-np.roll(height,1,0))*n/(2*metres)
        normal=np.stack((-dx,dv,np.ones_like(dx)),axis=-1)
        normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
        Image.fromarray(np.rint((normal+1)*127.5).astype('uint8')).save(directory/NORMAL_FILENAMES[name],optimize=True)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,default=HERE)
    generate(cli.parse_args().output)
