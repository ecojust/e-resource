"""Original lime-plaster finish for the restored garden elevation."""
from pathlib import Path
from garden_tower import WALL
TEXTURE=Path(__file__).with_name('garden-lime-plaster.png')


def make_texture(path, cornices):
    import numpy as np
    from PIL import Image
    w,h=384,704
    rng=np.random.default_rng(1861925)
    def field(nx,ny):
        seeds=rng.integers(0,256,(ny,nx),dtype='uint8')
        return np.asarray(Image.fromarray(seeds).resize((w,h),Image.Resampling.BICUBIC),float)/255-.5
    coarse=field(22,50);grain=field(105,185)
    z=15*(1-(np.arange(h)[:,None]+.5)/h)
    shade=-5.0*np.exp(-z/.85)+8*coarse+2.9*grain+rng.normal(0,1.4,(h,w))
    runoff=field(58,10)
    for cornice in cornices:
        dz=cornice-z
        shade-=np.where(dz>=0,1,0)*np.exp(-np.maximum(dz,0)/.38)*(2.1+3.5*runoff)
    value=np.clip(np.array([222,218,204])+shade[:,:,None],0,255)
    Image.fromarray(value.astype('uint8')).quantize(colors=68,dither=Image.Dither.NONE).save(path,optimize=True)


def apply(builder,dimensions):
    roofs=dimensions['fitted_elevations_m']
    if not TEXTURE.is_file():
        make_texture(TEXTURE,(dimensions['assumed_first_belt_m'],roofs['upper'],roofs['cornice']))
    builder.palette[WALL]={'color':[1,1,1],'metallic':0,'roughness':.95,'texture':str(TEXTURE)}
    for part in builder.parts:
        if part['material']==WALL:
            part['texcoords']=[(.36+.034*x+.021*y,1-(z+.19)/15.0)for x,y,z in part['vertices']]
            assert all(0<=u<=1 and 0<=v<=1 for u,v in part['texcoords'])
