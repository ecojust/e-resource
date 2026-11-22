"""Generate red pressed brick and a lightly stained grey cap independently of the reference photos."""
from pathlib import Path
import numpy as np
from PIL import Image
from brickwork import BRICK,END,PALE
from material_coordinates import texture_coordinates

SOURCE=Path(__file__).resolve().parent
BRICK_MAP='guandu-brick-courses.png';COPING_MAP='guandu-grey-coping.png'


def make_brick(path):
    rng=np.random.default_rng(10941910);w,h=928,1344
    yy,xx=np.indices((h,w)); # The atlas covers 21.5 m in width and 19.3 m in height.
    by=yy/5.4;course=np.floor(by).astype(int);bx=xx/10.30+(course%2)*.5
    index=np.floor(bx).astype(int);tone=rng.normal(0,3.2,(course.max()+1,index.max()+1))[course,index]
    chroma=rng.normal(0,1.25,(course.max()+1,index.max()+1))[course,index]
    cluster=np.asarray(Image.fromarray(rng.integers(0,255,(32,18),dtype=np.uint8)).resize((w,h),Image.Resampling.BILINEAR),dtype=float)
    variation=tone+(cluster-127.0)*.047+rng.normal(0,1.2,(h,w))
    joint=(np.mod(by,1)<.132)|(np.mod(bx,1)<.07)
    field=np.array([158,88,66])+variation[:,:,None]*np.array([1.,.77,.61])+chroma[:,:,None]*np.array([.25,-.25,-.32])
    field[joint]=np.array([144,98,80])+variation[joint,None]*.48
    dotted=np.clip(field,0,255).astype('uint8');Image.fromarray(dotted).quantize(colors=128,dither=Image.Dither.NONE).save(path,optimize=True)


def make_coping(path):
    rng=np.random.default_rng(10941917);w,h=512,160;yy,xx=np.indices((h,w))
    def noise(x,y):
        small=rng.integers(0,255,(y,x),dtype='uint8');return np.asarray(Image.fromarray(small).resize((w,h),Image.Resampling.BICUBIC),float)-127
    field=noise(35,7)*.091+noise(78,40)*.052-9*np.exp(-yy/15)-5*np.exp(-(h-yy)/15)+rng.normal(0,2.3,(h,w))
    Image.fromarray(np.clip(np.array([158,154,144])+field[:,:,None],0,255).astype('uint8')).quantize(colors=64,dither=Image.Dither.NONE).save(path,optimize=True)




def apply(builder):
    for path,produce in [(SOURCE/BRICK_MAP,make_brick),(SOURCE/COPING_MAP,make_coping)]:
        if not path.exists():produce(path)
    for mat in (BRICK,END,PALE):
        builder.palette[mat]={'color':[1,1,1],'roughness':.92,'metallic':0,'texture':str(SOURCE/(COPING_MAP if mat==PALE else BRICK_MAP))}
    for part in builder.parts:
        if part['material'] in (BRICK,END,PALE):
            uv=[texture_coordinates(part['material'],v,part['label'])for v in part['vertices']]
            assert all(0<=u<=1 and 0<=v<=1 for u,v in uv),(part['label'],min(uv),max(uv))
            part['texcoords']=[(u,1-v)for u,v in uv]
