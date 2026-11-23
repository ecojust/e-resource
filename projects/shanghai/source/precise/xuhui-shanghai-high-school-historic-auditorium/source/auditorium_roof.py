"""The front screen, red assembly roof and raised northern stage volume, in metres."""
import json
from pathlib import Path
from shapely.geometry import Polygon,box
from photo_architecture import Facade
from finish_surfaces import WALL,TRIM,ROOF
from south_front import DARK,COVER

DATA=Path(__file__).absolute().parents[1]/'measurements/hall-envelope.json'
RIDGE='Shanghai High School hall | muted ridge cover'
FLASH='Shanghai High School hall | lead edge flashing'
PALETTE={RIDGE:dict(color=[.48,.230,.158],roughness=.92),
         FLASH:dict(color=[.44,.455,.418],metallic=.23,roughness=.79)}

def roof_face(b,a,c,d,mat,label):
    # Two skins and three closed edges form one shallow, fully inspectable roof wedge.
    if (c[0]-a[0])*(d[1]-a[1])<(c[1]-a[1])*(d[0]-a[0]):c,d=d,c
    top=[a,c,d];lower=[(x,y,z-.135) for x,y,z in top]
    b.add(lower+top,[(0,2,1),(3,4,5),(0,1,4,3),(1,2,5,4),(2,0,3,5)],mat,label)

def straight_wall(b,start,end,bottom,height,material,label):
    f=Facade(b,start,end,label)
    f.box(0,(bottom+height)/2,f.length,height-bottom,.283,-.129,material,'wall')
    return f

def pitched_hall(b,d,lod):
    h=d['roof_eave_z'];crest=h+d['roof_pitch_rise'];width=d['auditorium_red_roof_half_span']
    south=d['front_head_depth_y'];north=d['rear_of_red_roof_y']
    # Near the garden facade, the eave turns through short diagonal corners beside
    # the entrance block. Both sides of the central transverse section rise to one ridge.
    r0=(0,south+.36,crest);r1=(0,north,crest)
    for hand in (-1,1):
        x=hand*width
        def roof_z(u):return h+(1-abs(u)/width)*(crest-h)
        front=[r0,(hand*(width-2.06),south+.75,roof_z(width-2.06)),(x,south+3.53,h)]
        back=(x,north,h)
        roof_face(b,front[0],front[1],front[2],ROOF,'Main roof | clipped entrance end')
        roof_face(b,front[0],front[2],back,ROOF,'Main roof | continuous red roof plane')
        roof_face(b,front[0],back,r1,ROOF,'Main roof | upper red plane')
        b.tube([front[2],back],.051,FLASH,sides=6 if lod else 10,label='Main roof | eave edge')
        # Close the north-facing gable against the stage. Front rake is visible from above.
        for y,z0,tag in [(south+.36,h-.10,'front'),(north,h-.10,'rear')]:
            poly=Polygon([(0,z0),(abs(x),z0),(0,crest-.11)])
            if hand>0:mapper=lambda u,z,k:(u,y-k,z)
            else:mapper=lambda u,z,k:(-u,y+k,z)
            b.prism(poly,-.079,.052,mapper,TRIM,'Main roof | '+tag+' gable cheek')
    b.tube([r0,r1],.081,RIDGE,sides=8 if lod else 14,label='Main roof | long ridge')
    for hand in (-1,1):
        x=hand*width;edge=hand*d['historic_east_wall_plane_x']
        b.plan_prism(box(min(x,edge)-.09,south,max(x,edge)+.09,north+.02),
                     h-.205,h-.09,COVER,'Main roof | narrow lower lateral roof')
    # Hide the small triangular gaps behind the clipped front hips. This surface
    # is a low roof visible in the separation between the front rim and the main pitch.
    b.plan_prism(box(-width,south-.1,width,south+3.56),h-.263,h-.13,COVER,'Roof | transition behind south block')

def add_roof(b,lod=False):
    d=json.loads(DATA.read_bytes());x=d['estimated_south_wall_width']/2
    front=d['front_head_depth_y'];rear=d['rear_limit_of_candidate_1155_y'];join=d['rear_of_red_roof_y']
    h=d['roof_eave_z'];backtop=d['stage_cover_z'];n=d['tall_stage_half_width']
    b.plan_prism(box(-x,0,x,rear),-.14,.018,DARK,'Base | historic footprint')
    west=straight_wall(b,(-x,rear),(-x,front),.012,h-.08,WALL,'West | inferred side length')
    west.box(0,.697,west.length,1.37,.10,.021,DARK,'low plinth')
    west.box(0,h-.18,west.length,.212,.32,.035,TRIM,'eave')
    # The edges of the source polygon constrain the unknown rear facade. The 1934
    # oblique shot does not establish window positions on that elevation.
    back=straight_wall(b,(x,rear),(-x,rear),.012,h-.06,WALL,'Rear | historic hall boundary')
    back.box(0,.697,back.length,1.37,.10,.016,DARK,'low plinth')
    back.box(0,h-.14,back.length,.20,.33,.053,TRIM,'eave')
    b.plan_prism(box(-x-.03,0,x+.03,front+.10),h-.018,h+.083,COVER,'Front | lower flat roof behind high screen')
    for hand in (-1,1):
        l,r=(hand*x,hand*n)
        b.plan_prism(box(min(l,r)-.06,join-.06,max(l,r)+.06,rear+.05),
                     h-.193,h-.065,COVER,'Stage | lower roof to either side')
    for a,c in [((-n,join),(n,join)),((n,join),(n,rear-.22)),((n,rear-.22),(-n,rear-.22)),((-n,rear-.22),(-n,join))]:
        face=straight_wall(b,a,c,h-.18,backtop,WALL,'Stage | raised rear volume')
        face.box(0,backtop-.085,face.length,.16,.32,.02,TRIM,'flat raised edge')
    b.plan_prism(box(-n-.11,join-.12,n+.11,rear-.12),backtop-.11,backtop+.045,COVER,'Stage | flat upper roof')
    # The east and west wall authors already supply the raised side cheeks.
    # Two dated aerial views show a lighter strip along the eastern part of the
    # otherwise dark rear roof. Transverse joints are visible in April 2025.
    strip=box(5.78,join+.55,11.00,rear-.65)
    b.plan_prism(strip,backtop+.047,backtop+.104,TRIM,'Stage | pale strip on rear roof')
    for at in (join+3.45,join+8.42,join+13.37):
        b.plan_prism(box(5.80,at-.028,10.98,at+.028),backtop+.103,backtop+.118,FLASH,'Stage | joint on pale strip')
    upper=Facade(b,(x,front),(-x,front),'Front | back of entrance block')
    upper.box(0,(h+d['south_top_z']-.36)/2,upper.length,d['south_top_z']-h-.36,.23,-.108,TRIM,'head return')
    b.plan_prism(box(-x+.06,.095,x-.06,front-.07),d['south_top_z']-.41,d['south_top_z']-.27,COVER,'Front | flat roof inside parapet')
    pitched_hall(b,d,lod)
