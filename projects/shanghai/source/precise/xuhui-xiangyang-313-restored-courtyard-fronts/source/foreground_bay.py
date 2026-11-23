"""The four-by-five dark window, its pale sill and the shuttered lower court opening."""
from pathlib import Path
import json
from shapely.geometry import box
from shapely.ops import unary_union

HERE = Path(__file__).parent
FRAME='Xiangyang 313 | dark painted window joinery'
REVEAL='Xiangyang 313 | shaded inside reveal'
GLASSES=('Xiangyang 313 | grey reflected glass','Xiangyang 313 | blue grey glass','Xiangyang 313 | pale reflected glass')
SILL='Xiangyang 313 | pale projecting sill'
HEAD='Xiangyang 313 | blue edged shallow hood'
HARDWARE='Xiangyang 313 | weathered metal hardware'
LOUVRE='Xiangyang 313 | dark shutter blades'
PALETTE={
    FRAME:{'color':[.060,.058,.069],'roughness':.65},
    REVEAL:{'color':[.025,.029,.031],'roughness':.9},
    GLASSES[0]:{'color':[.155,.162,.185],'metallic':.17,'roughness':.34},
    GLASSES[1]:{'color':[.121,.153,.188],'metallic':.17,'roughness':.31},
    GLASSES[2]:{'color':[.243,.251,.272],'metallic':.14,'roughness':.36},
    SILL:{'color':[.69,.68,.635],'roughness':.85},
    HEAD:{'color':[.122,.164,.208],'metallic':.29,'roughness':.62},
    HARDWARE:{'color':[.145,.143,.133],'metallic':.39,'roughness':.66},
    LOUVRE:{'color':[.043,.041,.042],'roughness':.76},
}
MEASURED=json.loads((HERE.parent/'measurements/large-window-readings.json').read_bytes())

def large_window(face,bounds,lod=False):
    """Fill the masonry opening in the supplied facade; bounds use local metres."""
    l,lo,r,hi=bounds;w=r-l;h=hi-lo
    hole=box(l,lo,r,hi);clear=box(l+.042*w,lo+.032*h,r-.041*w,hi-.068*h)
    face.prism(hole,-.190,-.179,REVEAL,'large window/interior shadow')
    face.prism(hole.difference(clear),-.114,-.049,FRAME,'large window/outer frame')
    posts=[l+v*w for v in MEASURED['left_to_right_frame_centres']]
    rails=[hi-v*h for v in MEASURED['top_down_transverse_centres']]
    # Separate, thick leaf joints and fine transverse glazing bars can be
    # distinguished on the photograph all the way across the four leaves.
    bars=unary_union([box(x-.026*w,lo,x+.026*w,hi)for x in posts]+
                     [box(l,z-.009*h,r,z+.009*h)for z in rails])
    face.prism(clear.intersection(bars),-.114,-.064,FRAME,'large window/stiles and glazing bars')
    panes=clear.difference(bars)
    gauges=MEASURED['glass_readings']
    ordered=sorted(panes.geoms,key=lambda g:(sum(g.centroid.x>x for x in posts),-g.centroid.y))
    assert len(ordered)==20
    for panel,gauge in zip(ordered,gauges):
        rr,gg,bb=gauge['median_rgb_8bit']
        material=GLASSES[2] if (rr+gg+bb)/3>115 else GLASSES[1] if bb-rr>12 else GLASSES[0]
        face.prism(panel,-.122,-.111,material,f"large window/leaf {gauge['column']}, light {gauge['row_from_top']}")
    face.box((l+r)/2,lo-.034,w*1.16,.073,.179,.026,SILL,'large window/pale projecting sill')
    for x in (l-.078*w,r+.056*w):
        for offset in (.084,.12):
            face.box(x,hi-offset*h,.057*w,.014*h,.026,.006,HARDWARE,'large window/visible side fastening')

def shutter_bank(face,bounds,lod=False):
    """Make the four tall dark leaves and the blue-edged rain hood on the ground floor."""
    l,lo,r,hi=bounds;w=r-l;h=hi-lo
    face.prism(box(l,lo,r,hi),-.20,-.182,REVEAL,'lower shutters/recess')
    for i in range(4):
        a=l+i*w/4+.003;c=l+(i+1)*w/4-.003
        opening=box(a,lo,c,hi)
        lower=box(a+.036*w,lo+.07*h,c-.031*w,lo+.55*h)
        upper=box(a+.036*w,lo+.615*h,c-.031*w,hi-.085*h)
        face.prism(opening.difference(unary_union((lower,upper))),-.096,-.048,FRAME,f'lower shutters/leaf {i+1} mortised surround')
        for name,zone,n in [('lower',lower,11),('upper',upper,8)]:
            x0,b,x1,t=zone.bounds
            face.prism(zone,-.136,-.123,REVEAL,'lower shutters/shadow behind blades')
            for j in range(n):
                z=b+(j+.5)*(t-b)/n
                face.box((x0+x1)/2,z,x1-x0,.52*(t-b)/n,.034,-.080,LOUVRE,f'lower shutters/{name} bank, leaf {i+1}')
    face.box((l+r)/2,hi+.121,w+.32,.044,.293,.128,HEAD,'shuttered entrance/shallow rain hood')
    for x in (l-.086,r+.085):
        face.line((x,hi+.085,.21),(x,hi-.121,.017),.011,HARDWARE,6 if lod else 10,'shuttered entrance/short diagonal hood bracket')

PLASTER='Xiangyang 313 | pale courtyard render'
CASE='Xiangyang 313 | pale enamel condenser'
PALETTE.update({
    PLASTER:{'color':[.735,.677,.548],'roughness':.94},
    CASE:{'color':[.65,.65,.605],'roughness':.68,'metallic':.1},
})

def condenser(face,camera,lod):
    from shapely.geometry import Point
    depth=.28
    upper_left=camera.wall((373,137),-depth)
    lower_right=camera.wall((414,162),-depth)
    x0,z1=upper_left[0],upper_left[2]
    x1,z0=lower_right[0],lower_right[2]
    fan_x=x0+.380*(x1-x0)
    fan_z=z0+.507*(z1-z0)
    radius=(z1-z0)*.365
    resolution=9 if lod else 16
    port=Point(fan_x,fan_z).buffer(radius,quad_segs=resolution)
    casing=box(x0,z0,x1,z1)
    face.prism(casing.difference(port),.045,depth,CASE,'condenser/enamel housing with round vent')
    face.prism(port,depth-.067,depth-.063,REVEAL,'condenser/dark exchanger behind fan grille')
    for i,ratio in enumerate((.26,.50,.73,.92)):
        radius_i=radius*ratio
        ring=Point(fan_x,fan_z).buffer(radius_i,quad_segs=resolution).difference(
            Point(fan_x,fan_z).buffer(max(.002,radius_i-.0065),quad_segs=resolution))
        face.prism(ring,depth-.009,depth-.002,HARDWARE,f'condenser/circular guard {i+1}')
    for x in (x0+.085,x1-.080):
        face.box(x,z0-.025,.045,.038,depth+.05,depth/2,HARDWARE,'condenser/projecting steel foot')
        face.line((x,z0-.185,.018),(x,z0-.046,depth*.87),.014,HARDWARE,6 if lod else 9,'condenser/triangular support')
    face.box(x1-.064,z0+.57*(z1-z0),.068,.019,.009,depth+.006,HEAD,'condenser/small dark badge')

def upper_opening(face, bounds):
    l,lo,r,hi=bounds
    clear=box(l+.045,lo+.038,r-.045,hi)
    outer=box(l,lo,r,hi)
    face.prism(outer.difference(clear),-.092,-.035,FRAME,'upper open window/jambs and sill')
    face.prism(clear,-.234,-.228,REVEAL,'upper open window/shaded recess')
    # The upper head is above the photograph. The two open leaves are read
    # from the partially visible lower rail, not reconstructed from an assumed head.
    from photo_architecture import Facade
    for side,start,end,mat in [('left',(l+.054,.06),(l+.27,-.20),GLASSES[2]),
                               ('right',(r-.054,.06),(r-.30,-.18),GLASSES[1])]:
        leaf=Facade(face.builder,start,end,'upper open window/'+side)
        w=leaf.length;frame=box(-w/2,lo+.051,w/2,hi);glass=box(-w/2+.032,lo+.088,w/2-.032,hi)
        leaf.prism(frame.difference(glass),-.014,.014,FRAME,'open sash edges')
        leaf.prism(glass,-.010,-.003,mat,'open sash pane')
    face.box((l+r)/2,lo-.032,r-l+.135,.071,.192,.027,SILL,'upper open window/protruding pale sill')

def add_foreground_bay(builder,lod=False):
    from photo_architecture import Facade
    from register_courtyard import Camera
    cam=Camera('case1');face=Facade(builder,(-1,0),(1,0),'restored projecting court wall')
    coords=[cam.wall(point,0) for point in MEASURED['corner_pixels']]
    tl,tr,br,bl=coords
    large=((tl[0]+bl[0])/2,(bl[2]+br[2])/2,(tr[0]+br[0])/2,(tl[2]+tr[2])/2)
    undercut=-1.255
    shutters=(-.665,.065,.886,1.997)
    high=(-.705,6.902,.655,7.875)
    mass=unary_union([box(undercut,0,1.91,2.56),box(-2.125,2.55,1.91,high[3])])
    openings=unary_union([box(*large),box(*shutters),box(*high)])
    face.prism(mass.difference(openings),-.215,0,PLASTER,'continuous wall with three real apertures')
    # The pale lower return beneath the projecting upper corner is visible
    # in the photograph; dimensions behind the wall are only a working cut.
    side=Facade(builder,(-2.125,.65),(-2.125,0),'projecting bay/east return')
    side.wall(2.55,high[3],thickness=.115,material=PLASTER)
    lower=Facade(builder,(undercut,.65),(undercut,0),'lower recessed entrance return')
    lower.wall(0,2.555,thickness=.115,material=PLASTER)
    builder.plan_prism(box(-2.126,0,undercut+.003,.65),2.545,2.607,PLASTER,'projecting bay/soffit above recess')
    face.box(-.101,3.135,4.11,.051,.078,.007,SILL,'projecting bay/lower plaster drip band')
    large_window(face,large,lod)
    shutter_bank(face,shutters,lod)
    upper_opening(face,high)
    condenser(face,cam,lod)
