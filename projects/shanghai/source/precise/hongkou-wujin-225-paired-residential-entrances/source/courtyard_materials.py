"""Painted timber, metalwork and the three distinct masonry finishes."""
import numpy as np
from material_names import PLASTER,RED,WHITE,TEXTURES
STONE='Wujin courtyard | buff stone'
WOOD='Wujin courtyard | oxblood wood'
SOFFIT='Wujin courtyard | light eaves underside'
GUTTER='Wujin courtyard | aged metal'
PIPE='Wujin courtyard | pale downspout'
def finish(rgb,rough=.85,metal=0.):
    f=np.asarray(rgb)/255.
    return dict(color=np.where(f<.04045,f/12.92,((f+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={**{k:dict(texture=str(p),color=[1.,1.,1.],roughness=.92,metallic=0.)for k,p in TEXTURES.items()},
         STONE:finish([160,148,128]),WOOD:finish([113,66,54]),SOFFIT:finish([158,148,133]),
         GUTTER:finish([103,101,88],.73,.2),PIPE:finish([174,170,155],.77,.12)}
INTERIOR='Wujin courtyard | warm plaster in recess'
FLOOR='Wujin courtyard | grey interior floor'
RECESS='Wujin courtyard | unlit enclosed doorway'
INNERWOOD='Wujin courtyard | dark interior framing'
PALETTE.update({INTERIOR:finish([149,137,118]),FLOOR:finish([117,110,100]),RECESS:finish([57,53,50]),INNERWOOD:finish([76,63,51])})

CABINET='Courtyard fittings | dark red painted steel'
PANEL='Courtyard fittings | oxblood door'
PALE='Courtyard fittings | pale lettering'
BLACK='Courtyard fittings | black latch'
PALETTE.update({CABINET:finish([126,44,39],.70,.12),PANEL:finish([156,44,41],.76,.08),PALE:finish([216,209,184]),BLACK:finish([54,57,53],.84,.10)})
