"""Original repeating brick, mortar and limewash, at one model course per 63 mm."""
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from material_names import PLASTER,RED,WHITE,TEXTURES
width,height=768,384
y,x=np.indices((height,width),dtype=float);rows,cols=16,8
row=(y/(height/rows)).astype(int)
xx=(x+((row%2)*.5)*width/cols)/(width/cols);col=np.floor(xx).astype(int)%cols
u=(xx%1.)*width/cols;v=y%(height/rows)
rng=np.random.default_rng(225)
def grain(scale):
    a=gaussian_filter(rng.normal(size=(height,width)),scale,mode='wrap')
    return a/a.std()
distance=np.minimum.reduce([u,width/cols-u,v,height/rows-v])+grain(.9)*.43
stone_grain=grain(.54)*2.+grain(2.9)*1.6
for mat,base,mortar,spread in [(PLASTER,[85,82,80],[149,139,124],6.2),(RED,[151,80,59],[164,127,101],6.2),(WHITE,[206,200,187],[187,181,169],2.2)]:
    shades=rng.normal(0,spread,(rows,cols,1))+rng.normal(0,1.5,(rows,cols,3))
    bed=np.array(mortar)+(stone_grain*.75+grain(7)*1.6)[:,:,None]
    surface=np.array(base)+shades[row,col]+(stone_grain+grain(6)*1.35)[:,:,None]
    blend=np.clip((distance-.72)/1.35,0,1)[:,:,None]
    img=bed*(1-blend)+surface*blend
    Image.fromarray(np.clip(img,0,255).astype('uint8')).save(TEXTURES[mat],quality=90,subsampling=0)
