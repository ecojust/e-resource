"""Original periodic brick and river-pebble finishes, generated in metric space."""
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
spec=importlib.util.spec_from_file_location('metric_gltf',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
BRICK='Xinhua 11 | red facing brick';PEBBLE='Xinhua 11 | grey pebble dash'
STEMS={BRICK:'xinhua-red-facing-brick',PEBBLE:'xinhua-grey-pebble-dash'}
NORMAL_FILENAMES={m:path+'-normal.png' for m,path in STEMS.items()}
REPEAT_METRES={BRICK:(1.02,.58),PEBBLE:(.34,.34)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={m:dict(color=[1.,1.,1.],texture=str(HERE/(stem+'.png')),normal=str(HERE/NORMAL_FILENAMES[m]),roughness=.90)for m,stem in STEMS.items()}
def metric_uv(part):
    part['texcoords']=(np.asarray(part['texcoords'])/.78/REPEAT_METRES[part['material']]).tolist()
def generate():
    from scipy.ndimage import gaussian_filter,minimum_filter
    size=192;yy,xx=np.mgrid[:size,:size]/size
    for index,material in enumerate(STEMS):
        rng=np.random.default_rng(132011+index)
        noise=gaussian_filter(rng.normal(size=(size,size)),.55,mode='wrap')
        if material==BRICK:
            row=(yy*8).astype(int);u=xx*4+(row%2)*.5
            gap=np.minimum(abs(u-np.rint(u))*.255,abs(yy*8-np.rint(yy*8))*.0725)
            mortar=np.exp(-(gap/.006)**2)
            tile=rng.uniform(-8,9,(8,4))[row,u.astype(int)%4]
            rgb=np.array([145,87,69])+((1-mortar)*tile+noise*5)[:,:,None]+mortar[:,:,None]*[13,31,39]
            height=noise*.00065-mortar*.0038
        else:
            wide=gaussian_filter(rng.normal(size=(size,size)),2.0,mode='wrap')
            chips=(wide>0.016).astype(float);edges=chips-minimum_filter(chips,size=3,mode='wrap')
            grain=26*noise+27*wide+11*chips-6*edges
            rgb=np.array([137,132,120])+grain[:,:,None];height=noise*.0008+.0018*chips+.0015*wide
        a,b=REPEAT_METRES[material];du=(np.roll(height,-1,1)-np.roll(height,1,1))*size/(2*a);dv=(np.roll(height,-1,0)-np.roll(height,1,0))*size/(2*b)
        normal=np.stack([-du,dv,np.ones_like(du)],-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        Image.fromarray(np.rint(np.clip(rgb,0,255)).astype('uint8')).save(HERE/(STEMS[material]+'.png'),optimize=True)
        Image.fromarray(np.rint((normal*.5+.5)*255).astype('uint8')).save(HERE/NORMAL_FILENAMES[material],optimize=True)
if __name__=='__main__':generate()
