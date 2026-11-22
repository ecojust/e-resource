"""Make three seamless original finishes in the dimensions used by the model."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from material_names import PLASTER,RED,TILE,TEXTURES

def make():
    width,height=768,384
    y,x=np.indices((height,width),dtype=float)
    row=(y/24).astype(int)
    xx=(x+(row%2)*48)/96
    col=np.floor(xx).astype(int)%8
    u=(xx%1)*96
    v=y%24
    rng=np.random.default_rng(1305)
    def grain(scale):
        a=gaussian_filter(rng.normal(size=(height,width)),scale,mode='wrap')
        return a/a.std()
    for name,base,bed,spread in [(PLASTER,[95,95,96],[129,125,121],7),(RED,[157,101,78],[146,121,107],6)]:
        dist=np.minimum.reduce([u,96-u,v,24-v])+grain(1)*.43
        f=np.clip((dist-.65)/1.35,0,1)[:,:,None]
        shade=rng.normal(0,spread,(16,8,1))+rng.normal(0,1.7,(16,8,3))
        body=np.array(base)+shade[row,col]+(2.2*grain(.55)+1.5*grain(3)+1.05*grain(8))[:,:,None]
        mortar=np.array(bed)+(1.8*grain(1.2)+grain(7)*1.2)[:,:,None]
        Image.fromarray(np.uint8(np.clip(mortar*(1-f)+body*f,0,255))).save(TEXTURES[name],quality=91,subsampling=0)
    tx=x/(width/6);ty=y/(height/5);rib=(np.cos(2*np.pi*tx)+1)/2
    col=np.floor(tx).astype(int)%6;row=np.floor(ty).astype(int)%5
    overlap=13*np.exp(-((ty%1)/.072)**2)
    shades=rng.normal(0,6,(5,6,1))
    tile=np.array([117,83,72])+shades[row,col]+(11*rib-6-overlap+3*grain(1.55)+1.7*grain(5))[:,:,None]
    Image.fromarray(np.uint8(np.clip(tile,0,255))).save(TEXTURES[TILE],quality=92,subsampling=0)
if __name__=='__main__':make()
