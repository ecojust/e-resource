"""Generate repeating brick and grey stone finishes from a fixed seed."""
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
BRICK='713 | russet face brick'
STONE='713 | weathered grey stone'
RED='713 | fired clay fan'
DARK_RED='713 | recessed oxblood clay'
METAL='713 | dark ventilator slats'
BACK='713 | ventilator shadow'

def tint(rgb,rough=.85,metal=0):
    return dict(color=[(n/255)**2.2 for n in rgb],roughness=rough,metallic=metal)

PALETTE={BRICK:dict(color=[1,1,1],roughness=.92,texture=str(HERE/'facing-brick.png')),
         STONE:dict(color=[1,1,1],roughness=.94,texture=str(HERE/'warm-grey-stone.png')),
         RED:tint([153,66,50]),DARK_RED:tint([109,46,39]),METAL:tint([81,78,73],.66,.15),
         BACK:tint([42,39,35])}

def generate():
    rng=np.random.default_rng(713)
    h,w=256,384
    yy,xx=np.indices((h,w))
    row=yy//16
    u=(xx+24*(row%2))%48
    variation=rng.normal(0,3.1,(16,8))[(row%16),((xx+24*(row%2))//48)%8]
    grain=rng.normal(0,3.3,(h,w))
    pigment=np.array([147,73,58])+((variation+grain)[:,:,None]*[1.0,.84,.70])
    joints=((yy%16==0)|(u==0))[:,:,None]
    brick=np.where(joints,[154,109,90]+grain[:,:,None]*.7,pigment)
    Image.fromarray(np.uint8(brick.clip(0,255))).save(HERE/'facing-brick.png',optimize=True)
    fine=rng.normal(0,3.8,(120,120));large=rng.normal(0,2.7,(15,15)).repeat(8,0).repeat(8,1)
    stone=np.array([166,162,153])+(fine+large)[:,:,None]
    Image.fromarray(np.uint8(stone.clip(0,255))).save(HERE/'warm-grey-stone.png',optimize=True)
if __name__=='__main__':generate()
