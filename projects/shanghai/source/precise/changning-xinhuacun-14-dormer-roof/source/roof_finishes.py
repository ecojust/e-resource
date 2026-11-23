"""Original periodic sash-roof ceramic and brick finishes, generated in metric space."""
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
spec=importlib.util.spec_from_file_location('metric_gltf',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
TILE='Xinhua 14 | red ceramic pans';BRICK='Xinhua 14 | weathered red facing brick'
STEMS={TILE:'house14-clay-pan',BRICK:'house14-red-brick'}
NORMAL_FILENAMES={m:path+'-normal.png' for m,path in STEMS.items()}
REPEAT_METRES={BRICK:(1.04,.58),TILE:(.80,.80)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={m:dict(color=[1.,1.,1.],texture=str(HERE/(stem+'.png')),normal=str(HERE/NORMAL_FILENAMES[m]),roughness=.90)for m,stem in STEMS.items()}
def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/.78/REPEAT_METRES[part['material']]).tolist()
def generate():
    from scipy.ndimage import gaussian_filter,minimum_filter
    size=192;yy,xx=np.mgrid[:size,:size]/size
    for index,material in enumerate(STEMS):
        rng=np.random.default_rng(132014+index)
        noise=gaussian_filter(rng.normal(size=(size,size)),.55,mode='wrap')
        if material==BRICK:
            row=(yy*8).astype(int);u=xx*4+(row%2)*.5
            gap=np.minimum(abs(u-np.rint(u))*.255,abs(yy*8-np.rint(yy*8))*.0725)
            mortar=np.exp(-(gap/.006)**2)
            tile=rng.uniform(-8,9,(8,4))[row,u.astype(int)%4]
            rgb=np.array([144,82,60])+((1-mortar)*tile+noise*5)[:,:,None]+mortar[:,:,None]*[13,31,39]
            height=noise*.00065-mortar*.0038
        else:
            ribs=(1+np.cos(2*np.pi*4*xx))/2
            courses=(yy*3)%1
            overlap=np.exp(-((np.minimum(courses,1-courses))/.065)**2)
            speckle=gaussian_filter(rng.normal(size=(size,size)),2.2,mode='wrap')
            rgb=np.array([151.,79.,65.])+(5*noise+18*speckle+9*ribs-23*overlap)[:,:,None]
            height=.008*ribs-.0026*overlap+.0006*noise
        a,b=REPEAT_METRES[material];du=(np.roll(height,-1,1)-np.roll(height,1,1))*size/(2*a);dv=(np.roll(height,-1,0)-np.roll(height,1,0))*size/(2*b)
        normal=np.stack([-du,dv,np.ones_like(du)],-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8')).save(HERE/(STEMS[material]+'.png'),optimize=True)
        Image.fromarray(np.rint((normal*.5+.5)*255).astype('uint8')).save(HERE/NORMAL_FILENAMES[material],optimize=True)
if __name__=='__main__':generate()
