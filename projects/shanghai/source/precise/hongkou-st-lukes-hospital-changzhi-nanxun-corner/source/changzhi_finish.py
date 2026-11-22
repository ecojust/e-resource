"""Tileable mineral render for the restored corner. No source photograph is embedded."""
from pathlib import Path
STUCCO='Changzhi | fine warm grey lime render'
TEXTURE=Path(__file__).with_name('lime-render.jpg')

TILE='Changzhi | red brown roof tile courses'
TILE_TEXTURE=Path(__file__).with_name('clay-roof.jpg')

def make(path=TEXTURE):
    import numpy as np
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    noise=np.random.default_rng(5034)
    raw=noise.normal(size=(512,512))
    broad=gaussian_filter(noise.normal(size=raw.shape),17.,mode='wrap')
    medium=gaussian_filter(raw,2.1,mode='wrap')
    grit=noise.normal(0,1.9,raw.shape)+2.2*medium/medium.std()+1.6*broad/broad.std()
    # Approximate neutral diffuse colour. The district image contains shadow and overcast light.
    rgb=np.array([193.,188.,184.])+grit[:,:,None]*np.array([1.,1.,.98])
    Image.fromarray(np.clip(np.rint(rgb),0,255).astype('uint8')).save(path,quality=91,subsampling=0)

def tile(path=TILE_TEXTURE):
    import numpy as np
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    rng=np.random.default_rng(159193)
    h,w=512,768
    y,x=np.indices((h,w))
    row=y//64
    xx=(x+(row%2)*32)%w
    col=xx//64
    weather=gaussian_filter(rng.normal(size=(h,w)),10,mode='wrap')
    texture=rng.normal(0,2.,(h,w))+weather/weather.std()*3.8
    ceramic=rng.normal(0,6.2,(8,12))[row,col]
    overlap=np.exp(-((y%64)/3.5)**2)*-24+np.exp(-((y%64-58)/4.)**2)*6
    profile=-10*np.cos((xx%64+4.)*2*np.pi/64)+5*np.sin((xx%64)*2*np.pi/64)
    rgb=np.array([126.,79.,62.])[None,None,:]+(texture+ceramic+overlap+profile)[:,:,None]*[1.,.9,.76]
    Image.fromarray(np.clip(np.rint(rgb),0,255).astype('uint8')).save(path,quality=91,subsampling=0)

if __name__=='__main__':
    tile()
    make()
