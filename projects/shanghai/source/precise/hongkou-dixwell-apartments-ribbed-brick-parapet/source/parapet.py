"""One street-facing parapet crown and the pair of window hoods beneath it."""
from pathlib import Path
from random import Random
from PIL import Image, ImageDraw
from shapely.affinity import scale
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

BRICK = 'Dark red face brick'
PLASTER = 'Pale parapet render'
STONE = 'Weathered parapet ledge'
STEEL = 'Dark painted window steel'
GLASS = 'Grey blue glazing'
HOOD = 'Folded dark sheet metal'
SILL = 'Stone window sill'
MORTAR = 'Recessed pointing'
PALETTE = {name:dict(color=color, roughness=roughness) for name,color,roughness in [
    (BRICK,[.97,.97,.97],.92),(PLASTER,[.78,.765,.72],.89),(STONE,[.62,.61,.57],.92),
    (STEEL,[.179,.17,.163],.66),(GLASS,[.32,.38,.392],.28),
    (HOOD,[.22,.236,.245],.65),(SILL,[.49,.459,.423],.93),(MORTAR,[.49,.452,.409],.94)]}
SCALE=.041
RIBS=(584.4,596.2,608.0,619.8,631.6)
WINDOWS=((549,573),(638,663))
def xcoord(u): return (u-608.0)*SCALE
def zcoord(v): return (254-v)*SCALE
def xyz(u,v,front): return xcoord(u),-front,zcoord(v)
def panel(b,l,t,r,base,back,front,material,label):
    b.prism(box(xcoord(l),zcoord(base),xcoord(r),zcoord(t)),back,front,
            lambda x,z,d:(x,-d,z),material,label)

def texture(destination):
    """Original staggered facing brick. No photograph is embedded in the asset."""
    rng=Random(411)
    im=Image.new('RGB',(744,528),(141,124,112))
    pen=ImageDraw.Draw(im)
    for course,v in enumerate(range(-4,528,8)):
        for u in range(-18 if course%2 else -5,744,26):
            tone=rng.choice([-8,-5,-3,0,2,3,4,7,9])
            base=(96+tone,66+tone,60+tone)
            pen.rectangle((u+1,v+1,u+25,v+7),fill=base)
            for _ in range(24):
                dv=rng.choice([-10,-8,-5,4,6,10])
                pen.point((u+rng.randint(1,25),v+rng.randint(1,7)),fill=tuple(c+dv for c in base))
    im.save(destination)

def crown_rib(b,axis,index,lod):
    """A faceted projecting rib with two offset cap courses and a short raised centre."""
    to_x=xcoord(axis)
    for level,(bottom,top,half,ext) in enumerate([
            (179.8,155.8,4.45,.067),(156.5,153.8,4.8,.081),
            (154.3,151.6,5.13,.098),(152.1,150.15,4.5,.077),(150.4,149.35,2.7,.055)]):
        w=half*SCALE
        polygon=Polygon([(to_x-w,-.015),(to_x+w,-.015),(to_x+w,.050),
                         (to_x+.48*w,.090+ext),(to_x,.117+ext),
                         (to_x-.48*w,.090+ext),(to_x-w,.050)])
        b.prism(scale(polygon,yfact=-1,origin=(0,0)),zcoord(bottom),zcoord(top),lambda x,y,z:(x,y+.225,z),
                BRICK,f'Raised brick rib {index} course {level+1}')
    if not lod:
        # The close daylight photograph shows returns of successive brick courses.
        for i in range(8):
            front=.166
            z=zcoord(176.8-2.5*i)
            polygon=Polygon([(to_x-.048,front),(to_x,front+.018),(to_x+.043,front),
                             (to_x+.043,front+.006),(to_x,front+.024),(to_x-.048,front+.006)])
            b.prism(scale(polygon,yfact=-1,origin=(0,0)),z,z+.006,lambda x,y,z:(x,y+.225,z),MORTAR,
                    f'Brick course face return {index}')

def hood(b,l,r,idx):
    # A thin folded canopy projects in front of its recessed steel window.
    profile=Polygon([(-.035,zcoord(207.0)),(.390,zcoord(208.55)),
                     (.390,zcoord(210.45)),(.368,zcoord(210.45)),(.368,zcoord(209.08)),
                     (-.035,zcoord(207.63))])
    b.prism(profile,-xcoord(r+3.2),-xcoord(l-3.2),lambda d,z,nx:(-nx,-d,z),HOOD,
            f'Folded projecting window canopy {idx}')
    for u in (l+.65,r-.65):
        outline=Polygon([(.02,zcoord(210.4)),(.34,zcoord(209.25)),(.02,zcoord(214.4))])
        b.prism(outline,-xcoord(u)-.015,-xcoord(u)+.015,lambda d,z,nx:(-nx,-d,z),
                HOOD,f'Side support below hood {idx}')

def window(b,l,r,idx,lod):
    panel(b,l,214,r,247,-.19,-.15,GLASS,f'Recessed window glazing {idx}')
    for j,fraction in enumerate((.035,.33,.66,.965)):
        u=l+(r-l)*fraction
        thickness=.52 if j in (0,3) else .37
        panel(b,u-thickness,214,u+thickness,247,-.151,-.086,STEEL,f'Window {idx} upright {j+1}')
    for j,v in enumerate((214.6,221.9,231.7,246.2)):
        panel(b,l,v-.37,r,v+.37,-.150,-.073,STEEL,f'Window {idx} cross rail {j+1}')
    panel(b,l-1,247,r+1,248.7,-.135,.079,SILL,f'Projecting sill {idx}')
    hood(b,l,r,idx)
    if not lod:
        for u in (l+.2,r-.2):
            panel(b,u-.15,216,u+.15,245,-.085,-.068,STEEL,f'Steel frame outer rebate {idx}')

def add_building(b,lod):
    openings=[box(xcoord(l),zcoord(247),xcoord(r),zcoord(214)) for l,r in WINDOWS]
    backing=box(xcoord(526),zcoord(254),xcoord(690),zcoord(211.3)).difference(unary_union(openings))
    b.prism(backing,-.235,0.,lambda x,z,d:(x,-d,z),BRICK,'Street brick facade with two window openings')
    # Four recessed fields suggest the joints between successive parapet slabs.
    cuts=[526,548,580,637,667,690]
    for i,(l,r) in enumerate(zip(cuts,cuts[1:])):
        panel(b,l+.10,178.5,r-.10,211.6,-.245,.017,PLASTER,f'Pale parapet panel {i+1}')
        panel(b,l,178.35,r,179.65,-.262,.036,STONE,f'Parapet coping {i+1}')
    panel(b,526,210.55,690,213.40,-.218,.047,STONE,'Lower drip below pale parapet')
    # The tall brick crown rises behind the pale coping.
    panel(b,577.3,152.18,638.6,180.0,-.485,-.243,BRICK,'Brick crown body')
    for i,axis in enumerate(RIBS,1): crown_rib(b,axis,i,lod)
    for i,(l,r) in enumerate(WINDOWS,1): window(b,l,r,i,lod)
    b.palette[BRICK]['texture']=str(Path(__file__).with_name('brick-courses.png'))
    for part in b.parts:
        if part['material']==BRICK:
            part['texcoords']=[[(x+.11*y+3.65)/7.35,1-(z-.14*y+.10)/5.21]
                               for x,y,z in part['vertices']]
