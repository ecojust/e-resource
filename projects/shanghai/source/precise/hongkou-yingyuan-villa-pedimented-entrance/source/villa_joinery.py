"""Brick pediments, deeply set wooden casements and the recessed villa entrance."""
import json,math
from pathlib import Path
from shapely.geometry import Polygon,LineString,box
from shapely.ops import unary_union
from mineral_render import CAST

BRICK='Baked cherry brick';LIGHT_BRICK='Sunlit brick header';MORTAR='Recessed lime joints'
LIMESTONE='Warm sill limestone';DARK='Shadow at timber reveal';WOOD='Walnut casements'
DOOR='Varnished entrance oak';BRASS='Dull brass';GLASS='Glass reflecting the park'
SECOND='Shaded glazing';RED='Vermilion raised name';STONE='Grey cut stair granite'
MILK='Pendant frosted glass';IRON='Patinated iron'
OUTLINES=json.loads(Path(__file__).with_name('sign-outlines.json').read_bytes())


def wire(f,points,radius,depth,material,sides,label):
    for a,b in zip(points,points[1:]):
        f.builder.tube([f.point(*a,depth),f.point(*b,depth)],radius,material,sides,f.label+'/'+label)


def pediment(f,u,bottom,width,rise,lod,label):
    """Open triangular tympanum, raking brick cornices and an upright soldier course."""
    half=width/2
    tri=Polygon([(u-half,bottom+.09),(u+half,bottom+.09),(u,bottom+rise)])
    f.prism(tri,.015,.12,CAST,label+'/ochre tympanum')
    f.box(u,bottom-.012,width+.09,.078,.19,.115,WOOD,label+'/under cornice')
    f.box(u,bottom+.074,width,.15,.21,.124,MORTAR,label+'/joint bed')
    pitch=.088 if not lod else .145
    count=max(7,round(width/pitch))
    for n in range(count):
        w=width/count;f.box(u-half+(n+.5)*w,bottom+.075,w-.011,.138,.096,.201,
                            LIGHT_BRICK if n%4==1 else BRICK,label+'/brick soldiers')
    for sign in (-1,1):
        start=(u+sign*(half+.035),bottom+.130);end=(u,bottom+rise+.105)
        # The raking courses meet with a mitre at the apex.
        beam=LineString([start,end]).buffer(.089,cap_style=2,join_style=2)
        f.prism(beam,.041,.199,MORTAR,label+'/raking joint bed')
        intervals=max(4,round(math.dist(start,end)/(.133 if not lod else .22)))
        for n in range(intervals):
            a=(n+.021)/intervals;b=(n+.979)/intervals
            p=(start[0]+a*(end[0]-start[0]),start[1]+a*(end[1]-start[1]))
            q=(start[0]+b*(end[0]-start[0]),start[1]+b*(end[1]-start[1]))
            f.prism(LineString([p,q]).buffer(.078,cap_style=2),.114,.225,
                    BRICK if n%4!=2 else LIGHT_BRICK,label+'/raking stretchers')


def sash(f,u,sill,width,height,lod,label,blind=False):
    x0=u-width/2;head=sill+height
    panel=box(x0,sill,x0+width,head)
    f.prism(panel.buffer(.010,join_style=2),-.260,-.242,DARK,label+'/rear rebate')
    glass=panel.buffer(-.065,join_style=2)
    f.prism(glass,-.225,-.211,SECOND if blind else GLASS,label+'/glazing')
    f.prism(panel.difference(glass),-.204,-.110,WOOD,label+'/fixed surround')
    f.box(u,sill+height/2,.066,height-.112,.131,-.131,WOOD,label+'/meeting stiles')
    for i in (-1,1):
        centre=u+i*width*.237
        frame=box(centre-width*.234,sill+.054,centre+width*.234,head-.055)
        interior=frame.buffer(-.038,join_style=2)
        f.prism(frame.difference(interior),-.192,-.127,WOOD,label+'/opening leaves')
        if not lod:
            f.box(centre,head-.185,width*.427,.024,.04,-.118,WOOD,label+'/top rebate')
    for side in (-1,1):
        x=u+side*(width/2+.067)
        f.box(x,sill+height/2,.128,height+.042,.101,.044,MORTAR,label+'/jamb bed')
        count=max(8,round(height/(.078 if not lod else .15)))
        for n in range(count):
            step=height/count
            f.box(x,sill+step*(n+.5),.122,step-.008,.093,.079,
                  BRICK if (n+(side>0))%5 else LIGHT_BRICK,label+'/brick reveals')
    for delta,addw,thickness,depth in [(0,.25,.073,.13),(-.067,.35,.064,.19),(-.127,.25,.052,.12)]:
        f.box(u,sill+delta,width+addw,thickness,depth+.075,depth/2-.014,LIMESTONE,label+'/sill profiles')


def glazed_leaf(f,u,z,width,height,lod,label):
    frame=box(u-width/2,z,u+width/2,z+height)
    octagons=[];xspan=width*.297
    for row in range(4):
        centre=z+.315+row*(height-.575)/3;rise=.164 if row!=3 else .185
        points=[(-xspan*.69,-rise),(xspan*.69,-rise),(xspan,-rise*.56),(xspan,rise*.56),
                (xspan*.69,rise),(-xspan*.69,rise),(-xspan,rise*.56),(-xspan,-rise*.56)]
        hole=Polygon([(u+x,centre+y)for x,y in points]);octagons.append(hole)
        f.prism(hole.buffer(.009,join_style=2),-1.112,-1.089,SECOND,label+'/octagonal glazing')
        bead=hole.buffer(.025,join_style=2).difference(hole)
        f.prism(bead,-1.045,-1.015,BRASS,label+'/octagonal glazing beads')
        diamond=[(u-xspan*.66,centre),(u,centre-rise*.72),(u+xspan*.66,centre),(u,centre+rise*.72),(u-xspan*.66,centre)]
        wire(f,diamond,.008,-1.054,BRASS,5 if lod else 8,label+'/diamond leadwork')
        if not lod:
            for side in (-1,1):
                wire(f,[(u+side*xspan,centre+rise*.57),(u+side*xspan*.53,centre+rise*.17)],.006,-1.055,BRASS,6,label+'/clipped corner leadwork')
    f.prism(frame.difference(unary_union(octagons)),-1.085,-1.044,DOOR,label+'/oak rails and stiles')
    for side in (-1,1):
        f.box(u+side*width*.46,z+height/2,.018,height-.075,.017,-1.035,BRASS,label+'/edge inset')


def entrance(f,dim,lod):
    centre=(dim['measured_u']['door_portal_left_outer_at_header']+dim['measured_u']['door_portal_right_outer_at_header'])/2
    width=dim['portal_outer_width'];fascia=dim['portal_fascia_width'];top=dim['portal_top'];soffit=dim['portal_soffit'];landing=dim['entry_landing']
    for sign in (-1,1):
        x=centre+sign*(width/2-.074)
        f.box(x,(soffit+landing)/2,.148,soffit-landing,1.28,-.493,CAST,'Entrance/return pier')
        f.box(x,(soffit+landing)/2,.091,soffit-landing,.11,.106,BRICK,'Entrance/narrow brick face')
    leaf_width=dim['door_leaf_total']/2
    f.box(centre,landing+dim['door_height']/2,2*leaf_width+.18,dim['door_height']+.13,.09,-1.143,DARK,'Entrance/deep timber casing')
    for sg in (-1,1):
        u=centre+sg*(leaf_width/2+.008)
        glazed_leaf(f,u,landing,leaf_width,dim['door_height'],lod,'Entrance/paired doors')
        f.box(centre+sg*.065,landing+1.04,.028,.188,.067,-.998,BRASS,'Entrance/pull handles')
    wall=box(centre-width/2+.055,landing,centre+width/2-.055,soffit+.035)
    aperture=box(centre-leaf_width-.110,landing-.01,centre+leaf_width+.110,landing+dim['door_height']+.10)
    f.prism(wall.difference(aperture),-1.283,-1.183,CAST,'Entrance/recessed vestibule wall')
    f.box(centre,soffit+.066,width,.153,1.65,-.439,CAST,'Entrance/ceiling')
    for z,w,h,d in [(soffit+.047,fascia-.16,.08,.31),(soffit+.111,fascia-.065,.075,.38),(top-.093,fascia,.125,.42),(top-.018,fascia+.028,.055,.47)]:
        f.box(centre,z,w,h,d,d*.28,BRICK,'Entrance/projecting brick lintel')
    count=round(fascia/(.11 if not lod else .20))
    for i in range(count):
        stride=fascia/count
        f.box(centre-fascia/2+stride*(i+.5),top-.086,stride-.011,.102,.031,.332,LIGHT_BRICK if i%5==0 else BRICK,'Entrance/lintel soldier joints')
    for piece in OUTLINES['name']:
        poly=Polygon([(x+centre,y+4.12)for x,y in piece[0]],[[(x+centre,y+4.12)for x,y in ring]for ring in piece[1:]])
        f.prism(poly,.014,.071,RED,'Entrance/vermilion raised name')
    wire(f,[(centre,soffit-.025),(centre,soffit-.51)],.009,-.40,IRON,6,'Entrance/pendant rod')
    f.box(centre,soffit-.568,.193,.143,.188,-.40,MILK,'Entrance/pendant opal glazing')
    for zz in (soffit-.486,soffit-.647):f.box(centre,zz,.225,.034,.22,-.40,IRON,'Entrance/pendant rim')
    for k in range(4):
        ht=landing*(k+1)/4;reach=1.42-.31*k;ww=width+.56-.10*k
        f.box(centre,ht/2,ww,ht,reach+.95,(reach-.95)/2,STONE,'Entrance/four granite treads')
        f.box(centre,ht-.016,ww+.027,.038,.044,reach+.006,LIMESTONE,'Entrance/cut nosings')

