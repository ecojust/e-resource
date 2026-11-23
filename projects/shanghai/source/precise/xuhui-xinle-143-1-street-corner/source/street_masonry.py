"""Metric unit facing, plinth and the two real apertures for the street-side service pipes."""
from shapely.geometry import box
from shapely.ops import unary_union
from photo_architecture import Facade
from register_street import Camera
from street_portal import BRICK,PLINTH,JAMB
from facing import CREAM
from service_flues import cutouts
BED='Xinlefang | faded joints in soldier band'
SOLDIER='Xinlefang | upright red trim units'
PALETTE={BED:{'color':[.49,.37,.33],'roughness':.88},SOLDIER:{'color':[.34,.146,.124],'roughness':.85}}
CORNICE_Z=10.52
TERRACE_RIGHT=-5.65
TERRACE_Z=10.18
RED_LINE_Z=8.602

def soldier_band(face,left,right,z,h,holes,name,lod):
    band=box(left,z,right,z+h).difference(holes)
    face.prism(band,.0005,.018,BED,name+' / joint bed')
    u=left
    while u<right-.015:
        # Thin, slightly projecting vertical bricks remain distinguishable in the scanned fascia.
        end=min(u+.067,right)
        unit=box(u+.003,z+.003,end-.003,z+h-.003).difference(holes)
        if end-u>.009:face.prism(unit,.018,.034 if not lod else .031,SOLDIER,name+' / vertical unit')
        u=end

def add_street_masonry(b,left,right,openings,lod=False):
    c=Camera('2018');face=Facade(b,(-1,0),(1,0),'Xinlefang / main street masonry')
    holes=unary_union([*openings,*cutouts(c).values()])
    for name,z0,z1,material in [('plinth',0,1.106,PLINTH),('red facing',1.106,RED_LINE_Z,BRICK),('roughcast top',RED_LINE_Z,CORNICE_Z,CREAM)]:
        outline=box(left,z0,right,z1)
        if material==CREAM:
            outline=outline.difference(box(left-.1,TERRACE_Z,TERRACE_RIGHT,CORNICE_Z+.1))
        face.prism(outline.difference(holes),-.226,0,material,name+' / cut wall')
    soldier_band(face,left,right,RED_LINE_Z-.114,.114,holes,'red to cream string course',lod)
    for x0,x1,top in [(left,TERRACE_RIGHT,TERRACE_Z),(TERRACE_RIGHT,right,CORNICE_Z)]:
        if x0<x1:soldier_band(face,x0,x1,top-.296,.126,holes,'red fascia below eaves',lod)
    # On the brick panel the short offset below the lower pipe and a continuous
    # dark vertical are visible at full source resolution.
    v=[(.663,3.67),(.663,5.53),(.865,5.53)]
    for pts,label,r in [(v,'offset service arm',.018),([(.648,3.68),(.648,8.50)],'upright conduit on facing',.021)]:
        b.tube([(x,-.056,z)for x,z in pts],r,JAMB,7 if lod else 11,'Xinlefang / '+label)
