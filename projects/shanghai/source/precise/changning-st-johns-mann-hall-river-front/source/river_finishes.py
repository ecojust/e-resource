"""Generate original, periodic facing brick and pan-tile PBR textures in metric units."""
from pathlib import Path
import importlib.util,json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
spec=importlib.util.spec_from_file_location('mann_gltf_textures',PROJECT/'source/precise/xuhui-wanping-42-brick-window-bays/source/brick_finishes.py')
writer=importlib.util.module_from_spec(spec);spec.loader.exec_module(writer)
BRICK='Mann Hall | grey facing brick';ROOF='Mann Hall | dark grey pan tiles'
STEMS={BRICK:'mann-grey-brick',ROOF:'mann-grey-pan-tile'}
NORMAL_FILENAMES={m:stem+'-normal.png' for m,stem in STEMS.items()}
REPEAT_METRES={BRICK:(1.02,.61),ROOF:(1.00,1.04)}
writer.HERE=HERE;writer.STEMS=STEMS;writer.NORMAL_FILENAMES=NORMAL_FILENAMES
PALETTE={m:dict(color=[1.,1.,1.],texture=str(HERE/(stem+'.png')),normal=str(HERE/NORMAL_FILENAMES[m]),roughness=.92 if m==BRICK else .88)for m,stem in STEMS.items()}
def metric_uv(part):
    uv=np.asarray(part['texcoords'])/.78
    part['texcoords']=(uv/REPEAT_METRES[part['material']]).tolist()
def generate():
    measured=json.loads((HERE.parent/'measurements/river-material-samples.json').read_bytes())['samples']
    size=192;q,p=np.mgrid[:size,:size]/size
    for index,(m,which) in enumerate([(BRICK,'brick'),(ROOF,'tile')]):
        samples=np.array([r['median_srgb']for r in measured[which]])
        # Sunlit oblique vs shaded bank: pooled upper-middle reflectance preserves the measured roof/wall ordering.
        base=np.percentile(samples,65,axis=0)*1.07
        rng=np.random.default_rng(19080919+index);fine=gaussian_filter(rng.normal(size=(size,size)),.54,mode='wrap')
        if m==BRICK:
            row=np.floor(q*8).astype(int);gx=p*4+(row%2)*.5
            dx=np.abs(gx-np.round(gx))/4;dy=np.abs(q*8-np.round(q*8))/8
            mortar=np.exp(-(np.minimum(dx*.97,dy*.62)/.0054)**2)
            tone=rng.uniform(-7,7,(8,4))[row,np.floor(gx).astype(int)%4]+3.3*fine+7.5*mortar
            height=.0006*fine-.0045*mortar
        else:
            rib=np.maximum(0,np.cos(2*np.pi*(p*5)))**4
            lap=np.exp(-(np.minimum(q*4%1,1-q*4%1)/.10)**2)
            height=.017*rib-.0024*lap+.00045*fine
            tone=3.3*rib-5.1*lap+2.5*fine+rng.uniform(-3.4,3.4,(4,5))[(q*4).astype(int),(p*5).astype(int)]
        a,b=REPEAT_METRES[m]
        du=(np.roll(height,-1,1)-np.roll(height,1,1))*size/(2*a);dv=(np.roll(height,-1,0)-np.roll(height,1,0))*size/(2*b)
        normal=np.stack([-du,dv,np.ones_like(du)],-1);normal/=np.linalg.norm(normal,axis=-1)[:,:,None]
        Image.fromarray(np.clip(base+tone[:,:,None],0,255).astype('uint8')).save(HERE/(STEMS[m]+'.png'),optimize=True)
        Image.fromarray(np.round((normal*.5+.5)*255).astype('uint8')).save(HERE/NORMAL_FILENAMES[m],optimize=True)
if __name__=='__main__':generate()
