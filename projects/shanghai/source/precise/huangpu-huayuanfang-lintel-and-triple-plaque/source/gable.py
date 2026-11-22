"""Surveyed single gateway with traditional right-to-left lane name and horizontal open ironwork."""
from pathlib import Path
from shapely.geometry import Polygon,shape
import json
from profile_tools import BRICK as PLASTER,cb,slab,bricks_uv
TRIM='Projecting pale grey frame'
RAIL='Dark iron open band'
RED='Raised red Chinese characters'
FIELD='Pale inset inscription field'
PALETTE={}
for name,rgb in [(PLASTER,(255,255,255)),(TRIM,(131,137,128)),(RAIL,(67,64,58)),(RED,(149,68,53)),(FIELD,(170,162,142))]:
    PALETTE[name]=dict(color=[(k/255)**2.2 for k in rgb],roughness=.87)
PALETTE[PLASTER]['texture']=str(Path(__file__).with_name('finish.png'))

def letters():
    return [(r['character'],shape(r['geometry']))for r in json.loads(Path(__file__).with_name('three-characters.json').read_bytes())]

def model(b,lod=False):
    for x in (-1.52,1.52):
        cb(b,x-.164,x+.164,-.135,.28,0,2.71,PLASTER,'Square gate pier')
        cb(b,x-.218,x+.218,-.187,.295,.03,.22,TRIM,'Pier foot')
        cb(b,x-.204,x+.204,-.18,.32,2.58,2.69,TRIM,'Bearing at main lintel')
    cb(b,-1.76,1.76,-.155,.31,2.655,3.035,PLASTER,'Deep gate lintel')
    cb(b,-1.795,1.795,-.205,.328,3.004,3.075,TRIM,'Upper rim of lintel')
    for x in (-1.56,1.56):
        cb(b,x-.108,x+.108,-.10,.24,3.06,3.63,PLASTER,'Side post of open band')
    for z in (3.223,3.357,3.490):
        cb(b,-1.50,1.50,-.093,-.044,z-.018,z+.018,RAIL,'Horizontal bar in open band')
    cb(b,-1.756,1.756,-.147,.31,3.58,4.56,PLASTER,'Head over the open band')
    cb(b,-1.825,1.825,-.219,.352,3.555,3.654,TRIM,'Lower projecting sign ledge')
    cb(b,-1.814,1.814,-.212,.343,4.542,4.621,TRIM,'Projecting sign coping')
    cb(b,-1.786,1.786,-.192,.335,4.618,4.648,PLASTER,'Raised line of coping')
    cb(b,-1.171,1.171,-.175,-.125,3.716,4.462,FIELD,'Rectangular name field')
    for z in (3.706,4.470):cb(b,-1.213,1.213,-.211,-.155,z-.024,z+.024,TRIM,'Horizontal sign bead')
    for side in (-1,1):
        x=side*1.215
        cb(b,x-.026,x+.026,-.214,-.152,3.706,4.476,TRIM,'Vertical sign bead')
        for offset in (.12,.176,.232,.288):
            xx=side*(1.215+offset)
            cb(b,xx-.012,xx+.012,-.19,-.145,3.75,4.48,TRIM,'Vertical flutes at plaque end')
    for ch,poly in letters():
        face=poly.simplify(.0035 if lod else .0008,preserve_topology=True)
        slab(b,face,-.212,-.169,RED,'Inscription '+ch)
    bricks_uv(b)
