"""Draw tileable brick facing and inset plaque stone; the two relief maps are procedural."""
from pathlib import Path
import importlib.util,json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
common=PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py'
spec=importlib.util.spec_from_file_location('meiquan_texture_writer',common);writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
STEMS={'Meiquan | pale gate brick':'gate-brick','Meiquan | cut plaque stone':'name-tablet-stone'}
NORMAL_FILENAMES={key:stem+'-normal.png'for key,stem in STEMS.items()}
REPEAT_METRES={'Meiquan | pale gate brick':(1.36,1.0),'Meiquan | cut plaque stone':(.64,.64)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={key:{'color':[1.,1.,1.],'texture':str(HERE/(stem+'.png')),'normal':str(HERE/NORMAL_FILENAMES[key]),'roughness':.90 if 'brick' in stem else .82}for key,stem in STEMS.items()}
def metric_uv(part):
    part['texcoords']=(np.array(part['texcoords'])/(.78*np.asarray(REPEAT_METRES[part['material']]))).tolist()
def generate():
    obs=json.loads((HERE.parent/'measurements/finish-samples.json').read_bytes());yy,xx=np.mgrid[:128,:128]
    for i,(key,stem)in enumerate(STEMS.items()):
        gen=np.random.default_rng(8541935+i);noise=gen.normal(size=(128,128));fine=gaussian_filter(noise,.47,mode='wrap');broad=gaussian_filter(noise,3.2,mode='wrap')
        # Both photographs put the name and the stonework under tree shade. Use the
        # brightest field samples for material albedo, then shade using the model.
        rgb=np.percentile([s['median_srgb']for s in obs[key]],80,axis=0)
        if i==0:
            row=yy//16;offset=16*(row%2);col=((xx+offset)//32)%4
            joint_x=np.minimum((xx+offset)%32,32-(xx+offset)%32)
            joint_z=np.minimum(yy%16,16-yy%16)
            mortar=np.exp(-(np.minimum(joint_x,joint_z)/.76)**2)
            tone=gen.uniform(-4.7,4.7,(8,4))[row,col]
            variation=tone+2.4*fine+9*broad-21*mortar
            height=.00043*fine-.0055*mortar
        else:
            variation=2.3*fine+10*broad;height=.0002*fine
        color=np.clip(rgb+variation[:,:,None],0,255).astype('uint8');a,b=REPEAT_METRES[key]
        dx=(np.roll(height,-1,1)-np.roll(height,1,1))*64/a;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*64/b
        vec=np.stack([-dx,dy,np.ones_like(dx)],axis=-1);vec/=np.linalg.norm(vec,axis=-1,keepdims=True)
        Image.fromarray(color).save(HERE/(stem+'.png'),optimize=True)
        Image.fromarray(np.round(255*(vec*.5+.5)).astype('uint8')).save(HERE/NORMAL_FILENAMES[key],optimize=True)
if __name__=='__main__':generate()
