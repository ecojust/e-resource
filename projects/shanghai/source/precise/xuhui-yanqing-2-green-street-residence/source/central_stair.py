"""Registered three-stage stair windows, top casements and the curved plaster stair enclosure."""
from math import atan2,cos,sin,pi
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from stair_surface import PLAN,wall_y,at_surface
from street_entry import openings as entry_openings

WALL='Yanqing 2 | pale celadon mineral render'
BASE='Yanqing 2 | charcoal plinth'
CREAM='Yanqing 2 | ivory stair window trim'
FRAME='Yanqing 2 | black steel casement'
PANE='Yanqing 2 | shaded blue-grey window glass'
LANDING='Yanqing 2 | dark iron balcony'
SOFFIT='Yanqing 2 | grey balcony underside'

def finish(rgb,roughness,metal=0.):
    c=np.asarray(rgb)/255.
    lin=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    return {'color':lin.tolist(),'roughness':roughness,'metallic':metal}
PALETTE={WALL:finish((142,160,148),.93),BASE:finish((71,66,68),.90),
         CREAM:finish((188,187,167),.91),FRAME:finish((48,54,47),.66,.16),
         PANE:finish((66,79,79),.35),LANDING:finish((46,48,47),.64,.20),SOFFIT:finish((158,153,141),.95)}
# Native June window ends set the projected horizontal positions. The three
# December cameras provide independent sill elevations and clarify occluded heads.
STEPS=[(-2.04,-.735,3.205,4.34),(-.605,.455,4.035,5.18),(.845,1.695,4.790,5.94)]
UPPER=[(-1.80,-.93,7.80,9.17),(-.64,.49,7.81,9.20),(.82,1.72,7.79,9.18)]
EDGES=[float(x) for x in PLAN[:,0]]

def part(b,shape,d0,d1,material,tag):
    if shape.is_empty or d1<=d0:return
    x0,z0,x1,z1=shape.bounds
    # Each slice spans a single segment of the surveyed curve. Both skins and
    # the sides share vertices; projecting a curved 2D polygon once would fill
    # its long chord and put steel and glass off the curved masonry plane.
    cuts=[x0]+[x for x in EDGES if x0+1e-6<x<x1-1e-6]+[x1]
    for j,(lo,hi) in enumerate(zip(cuts,cuts[1:])):
        if hi-lo<1e-5:continue
        geom=shape.intersection(box(lo,z0-.1,hi,z1+.1))
        if geom.is_empty or geom.area<1e-8:continue
        slope=(wall_y(hi)-wall_y(lo))/(hi-lo);y0=wall_y(lo)
        b.prism(geom,-d1,-d0,lambda x,z,d:(x,y0+(x-lo)*slope-d,z),material,'Stair enclosure | '+tag)

def window(b,bounds,idx,upper,lod):
    l,r,sill,head=bounds
    outer=box(l,sill,r,head)
    name=('top room ' if upper else 'stair flight ')+str(idx)
    part(b,outer,.118,.145,PANE,name+' | grey glazing')
    inner=box(l+.028,sill+.029,r-.028,head-.031)
    # Top transom and two/three lower lights are visible as separate panes.
    clm=2 if r-l<1.12 else 3
    steel=outer.difference(inner)
    divisions=[box(l+(r-l)*j/clm-.009,sill,l+(r-l)*j/clm+.009,head)for j in range(1,clm)]
    divisions.extend(box(l,sill+(head-sill)*q-.008,r,sill+(head-sill)*q+.008)
                     for q in ((.34,.67,.82) if upper else (.36,.74)))
    part(b,unary_union([steel,*divisions]),.080,.115,FRAME,name+' | black casement')
    part(b,box(l-.053,sill-.072,r+.058,sill+.01),-.075,.035,CREAM,name+' | projecting sill')
    part(b,box(l-.038,head-.01,r+.045,head+.053),-.039,.020,CREAM,name+' | shallow head')
def add_stair(b,lod=False,extra_cutouts=()):
    low=[box(l,z,r,h)for l,r,z,h in STEPS+UPPER]
    low+=[entry_openings()['gate'][1],*extra_cutouts]
    main=box(PLAN[0,0],0,PLAN[-1,0],9.48).difference(unary_union(low))
    for z0,z1,mat,d0 in [(0,.545,BASE,-.012),(.545,9.48,WALL,0)]:
        part(b,main.intersection(box(-20,z0,20,z1)),d0,.205,mat,'curved exterior wall')
    for i,w in enumerate(STEPS):window(b,w,i+1,False,lod)
    for i,w in enumerate(UPPER):window(b,w,i+1,True,lod)
    # Pale outlined diamond above the middle landing, independently visible
    # through the foliage in 2015 and unobscured in the December station.
    for j,(cx,cz,rx,rz) in enumerate([(-.06,6.34,.475,.81)]):
        boundary=Polygon([(cx,cz+rz),(cx+rx,cz),(cx,cz-rz),(cx-rx,cz)])
        strip=boundary.difference(boundary.buffer(-.083,join_style=2))
        part(b,strip,-.018,-.001,CREAM,'outlined diamond above middle flight')
    part(b,box(PLAN[0,0],9.37,PLAN[-1,0],9.47),-.09,.22,CREAM,'curved cornice')
