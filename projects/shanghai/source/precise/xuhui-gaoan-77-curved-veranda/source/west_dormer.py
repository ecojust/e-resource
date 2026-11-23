"""Four-light flat-capped dormer seen above the west eave on photograph 26."""
import json
from pathlib import Path
from shapely.geometry import box
from garden_sashes import sash
from materials import DARK,PLASTER,STONE
from south_verandah import slab
SURVEY=json.loads((Path(__file__).resolve().parents[1]/'measurements/west-dormer-control.json').read_text())
OBS=SURVEY['observations']
FRONT=SURVEY['front_plane_x_m']
BACK=.85
window_depths=sorted(r['model_xyz_m'][1] for r in OBS['glass top'])
lo,hi=window_depths
CAP=sum(p['model_xyz_m'][2] for p in OBS['outer coping'])/2
head=sum(p['model_xyz_m'][2] for p in OBS['glass top'])/2
sill=sum(p['model_xyz_m'][2] for p in OBS['visible glass base'])/2-.032
CUT=box(FRONT-.025,lo-.14,BACK+.008,hi+.14)

def add_west_dormer(f,lod):
    front=f.face(FRONT,hi,0,-1)
    aperture=box(0,sill,hi-lo,head)
    panel=box(-.137,sill-.13,hi-lo+.137,CAP-.17)
    front.solid(panel.difference(aperture),-.105,0,PLASTER,'west dormer | four-light front')
    sash(front,aperture,'west dormer | paired casements',4,(.26,),False,depth_scale=.40)
    for d,sign in [(lo,1),(hi,-1)]:
        side=f.face(FRONT if sign==1 else BACK,d,sign,0)
        side.rect(0,BACK-FRONT,sill-.05,CAP-.13,-.10,0,PLASTER,'west dormer | cheek')
    for pad,base,top,mat,tag in [(.13,CAP-.19,CAP-.103,DARK,'lower fascia'),(.17,CAP-.115,CAP-.057,STONE,'flashing'),(.19,CAP-.056,CAP,DARK,'flat coping')]:
        slab(f,box(FRONT-pad,lo-pad,BACK+.035,hi+pad),base,top,mat,'west dormer | '+tag)
