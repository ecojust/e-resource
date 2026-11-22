"""Two original procedural finishes, derived from a photographed surface's general appearance."""
from pathlib import Path
import numpy as np
from PIL import Image
from material_coordinates import texture_coordinates,WOOD,PANEL

HERE=Path(__file__).resolve().parent
TEXTURES={WOOD:'oval-grain.png',PANEL:'cement-panel.png'}
def generate(material,target):
    rng=np.random.default_rng(11241932 if material==WOOD else 11242021)
    w,h=(420,110) if material==WOOD else (320,108)
    yy,xx=np.indices((h,w))
    if material==WOOD:
        bend=.98*np.sin(xx/75)+1.2*np.sin(xx/43+yy/17)
        grain=np.sin(2*np.pi*(yy/11+bend*.19+.17*np.sin(yy/7+xx/51)))
        knot=np.exp(-((xx-57)/41)**2-((yy-69)/18)**2)
        grain+=.7*knot*np.sin(.48*np.sqrt(((xx-57)*.47)**2+(yy-69)**2))
        field=grain*5.8+np.cos(yy/24)*2.7+rng.normal(0,1.0,(h,w))
        base=[122,99,78];variation=[1,.86,.67]
    else:
        small=rng.integers(0,255,(10,27),dtype='uint8')
        mottling=np.asarray(Image.fromarray(small).resize((w,h),Image.Resampling.BICUBIC),float)-128
        field=mottling*.055+rng.normal(0,1.8,(h,w))-4.1*np.exp(-(yy/8)**2)
        base=[166,168,158];variation=[.91,.94,1.]
    image=np.clip(np.asarray(base)+field[:,:,None]*np.asarray(variation),0,255).astype('uint8')
    Image.fromarray(image).quantize(colors=64,dither=Image.Dither.NONE).save(target,optimize=True)

def apply(builder):
    for mat,filename in TEXTURES.items():
        target=HERE/filename
        if not target.is_file():generate(mat,target)
        builder.palette[mat]={'color':[1.,1.,1.],'roughness':.86,'metallic':0.,'texture':str(target)}
    for part in builder.parts:
        if part['material'] in TEXTURES:
            uv=[texture_coordinates(part['material'],p)for p in part['vertices']]
            assert all(0<=u<=1 and 0<=v<=1 for u,v in uv)
            part['texcoords']=[(u,1-v)for u,v in uv]
