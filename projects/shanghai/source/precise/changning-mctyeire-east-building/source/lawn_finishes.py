"""Original repeatable render and clay surfaces, with measured colour ranges and relief in metres."""
import importlib.util
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
spec=importlib.util.spec_from_file_location('lawn_texture_writer',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
RENDER='Lambuth | garden stone finish';TILE='Lambuth | overlapping clay';GLASS='Lambuth | return window glazing'
STEMS={RENDER:'lawn-wing-pale-render',TILE:'lawn-wing-clay-roof'}
REPEAT_METRES={RENDER:(1.30,1.30),TILE:(.87,.74)}
NORMAL_FILENAMES={k:s+'-normal.png'for k,s in STEMS.items()}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={k:{'color':[1.,1.,1.],'texture':str(HERE/(n+'.png')),'normal':str(HERE/NORMAL_FILENAMES[k]),'roughness':.88}for k,n in STEMS.items()}
PALETTE[GLASS]={'color':[.20,.23,.215],'metallic':.115,'roughness':.35,'alpha':.87}
def generate():
    # Albedos are conditional conversions of the shaded sRGB patch medians recorded separately.
    rng=np.random.default_rng(19220912);yy,xx=np.mgrid[:128,:128]
    for name,stem in STEMS.items():
        grain=gaussian_filter(rng.standard_normal((128,128)),.47,mode='wrap')
        if name==RENDER:
            rgb=np.array([208.,205.,191.]);variation=grain*2.6;height=grain*.00042
        else:
            rgb=np.array([154.,110.,88.]);row=yy//64;col=((xx+row*13)//32)%4
            tile_field=rng.uniform(-3.8,3.8,(2,4))[row,col]
            x=((xx+row*13)%32)/32.;y=(yy%64)/64.
            ridge=np.exp(-((x-.08)/.105)**2)
            recess=np.exp(-(np.minimum(y,1-y)/.027)**2)
            variation=tile_field+grain*2.4+ridge*4.8-recess*5.4
            height=.0037*ridge-.0023*recess+.00027*grain
        colour=np.clip(rgb+variation[:,:,None],0,255).astype('uint8')
        u,v=REPEAT_METRES[name];nx=-(np.roll(height,-1,1)-np.roll(height,1,1))*64/u
        ny=(np.roll(height,-1,0)-np.roll(height,1,0))*64/v
        n=np.stack([nx,ny,np.ones_like(nx)],axis=2);n/=np.linalg.norm(n,axis=2,keepdims=True)
        Image.fromarray(colour).save(HERE/(stem+'.png'),optimize=True)
        Image.fromarray(np.round((n+.999999999)*127.5).clip(0,255).astype('uint8')).save(HERE/NORMAL_FILENAMES[name],optimize=True)
