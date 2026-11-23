"""Generate seamless pale marble and dressed grey stone without sampling any photographic texture."""
import importlib.util,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
f=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('pavilion_texture_io',f);writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'Pavilion | pale carved marble':'pale-marble','Pavilion | grey screen stone':'dressed-grey-stone'}
REPEAT_METRES={'Pavilion | pale carved marble':(.82,.82),'Pavilion | grey screen stone':(2.36,1.28)}
NORMAL_FILENAMES={key:stem+'-normal.png' for key,stem in STEMS.items()}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={key:{'color':[1.,1.,1.],'texture':str(HERE/(stem+'.png')),'normal':str(HERE/NORMAL_FILENAMES[key]),'roughness':.66 if 'marble' in stem else .88}for key,stem in STEMS.items()}

def metric_uv(part):
    part['texcoords']=(np.array(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()

def generate():
    observations=json.loads((HERE.parent/'measurements/finish-readings.json').read_bytes())['materials']
    yy,xx=np.mgrid[:128,:128]
    for i,(key,stem)in enumerate(STEMS.items()):
        seed=np.random.default_rng(8531935+i);noise=seed.normal(size=(128,128))
        broad=gaussian_filter(noise,5,mode='wrap');fine=gaussian_filter(noise,.7,mode='wrap')
        ref=np.median([v['median_srgb']for v in observations[key]],axis=0)
        if i==0:
            phase=2*np.pi*(xx+yy)/128+.33*np.sin(2*np.pi*yy/128)+4*broad
            veins=np.exp(-np.abs(np.sin(phase))/.045)
            value=1.35*fine+9*broad-2.5*veins
            height=.00008*fine-.00005*veins
        else:
            ref=np.minimum(166,ref*1.32+25)
            xphase=(xx+32*(yy//32%2))%64
            seam=np.maximum(np.exp(-(np.minimum(xphase,64-xphase)/.71)**2),np.exp(-(np.minimum(yy%32,32-yy%32)/.78)**2))
            tones=seed.uniform(-4,4,(4,2));panel=tones[yy//32,((xx+32*(yy//32%2))//64)%2]
            value=panel+4*fine+9*broad-12*seam
            height=.00056*fine-.0063*seam
        rgb=np.clip(ref+value[:,:,None],0,255).astype('uint8')
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))*64/REPEAT_METRES[key][0]
        dy=(np.roll(height,-1,0)-np.roll(height,1,0))*64/REPEAT_METRES[key][1]
        vec=np.stack([-dx,dy,np.ones_like(height)],axis=-1);vec/=np.linalg.norm(vec,axis=-1,keepdims=True)
        Image.fromarray(rgb).save(HERE/(stem+'.png'),optimize=True)
        Image.fromarray(np.round((vec*.5+.5)*255).astype('uint8')).save(HERE/NORMAL_FILENAMES[key],optimize=True)
if __name__=='__main__':generate()
