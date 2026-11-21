"""The surviving lower drum and two short adjoining walls at the southeast corner."""
import math
from shapely.geometry import Polygon, box
from photo_architecture import Facade

BRICK='dark red pressed brick'
SHADOW='recessed red-brown brick'
GREY='weathered grey stringcourse'
STONE='pale worn balcony stone'
WINDOW='dark painted frames'
GLASS='smoky street glazing'
IRON='slender iron rail'
CANVAS='pale inclined awning'
PALETTE={name:{'color':rgb,'roughness':rough} for name,rgb,rough in [
    (BRICK,[.493,.277,.209],.91),(SHADOW,[.369,.195,.153],.95),
    (GREY,[.397,.361,.327],.92),(STONE,[.674,.617,.535],.91),
    (WINDOW,[.181,.142,.121],.81),(GLASS,[.173,.218,.210],.42),
    (IRON,[.205,.221,.213],.72),(CANVAS,[.635,.626,.583],.96)]}
R=2.10
START=-162.0
END=62.0
AXES=5
EAVE=11.55
DRUM=14.07

def radial(degrees,radius,z):
    angle=math.radians(degrees)
    return radius*math.cos(angle),radius*math.sin(angle),z

def arc_slab(b,inner,outer,bottom,top,material,label,count):
    angles=[START+(END-START)*i/count for i in range(count+1)]
    plan=[radial(a,outer,0)[:2] for a in angles]
    plan.extend(radial(a,inner,0)[:2] for a in reversed(angles))
    b.plan_prism(Polygon(plan),bottom,top,material,label)

def light(x,sill,width,height,rise):
    left=x-width/2;right=x+width/2;spring=sill+height-rise
    points=[(left,sill),(right,sill)]
    points.extend((x+width*.5*math.cos(i*math.pi/16),spring+rise*math.sin(i*math.pi/16)) for i in range(17))
    return Polygon(points)

def opening(f,x,sill,width,height,rise,columns,rows,storey):
    aperture=light(x,sill,width,height,rise)
    f.window(aperture,columns,rows,WINDOW,False,GLASS,storey)
    if rise:
        surround=aperture.buffer(.11,join_style=2).difference(aperture).intersection(box(x-width,sill+height-rise-.12,x+width,sill+height+.17))
        f.prism(surround,-.04,.064,SHADOW,'segmental brick head')
    return aperture

def awning(f,x,width,z,lod):
    left=x-width/2;right=x+width/2
    verts=[f.point(u,h,d) for u,h,d in [(left,z,.035),(right,z,.035),(right,z-.29,.50),(left,z-.29,.50),
        (left,z-.035,.035),(right,z-.035,.035),(right,z-.34,.50),(left,z-.34,.50)]]
    f.builder.add(verts,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],CANVAS,f.label+'/sloping fabric awning')
    if not lod:
        for edge in (left,right):f.line((edge,z-.46,.02),(edge,z-.31,.49),.013,IRON,6,'awning stay')

def corner(b,lod):
    lower=3.53;upper=7.31
    angles=[START+(END-START)*i/AXES for i in range(AXES+1)]
    for i,(a,c) in enumerate(zip(angles,angles[1:])):
        face=Facade(b,radial(a,R,0)[:2],radial(c,R,0)[:2],'Round corner bay '+str(i+1))
        holes=[opening(face,0,.78,1.06,2.00,.065,1,1,'lower window'),
               opening(face,0,4.02,1.00,2.88,.11,2,3,'second floor'),
               opening(face,0,7.91,1.00,2.98,.16,2,3,'upper light'),
               opening(face,0,12.05,.96,1.52,.045,1,2,'attic window')]
        face.wall(.02,DRUM-.10,holes,.33,BRICK)
        awning(face,0,1.12,2.94,lod)
    # The photograph shows engaged red shafts framing the two tiers. The photographed
    # light stone rail survives on the upper balcony, with darker rails on the floor below.
    for i,a in enumerate(angles):
        x,y,_=radial(a,R+.005,0)
        for z0,z1 in [(3.70,7.08),(7.57,11.05)]:
            h=z1-z0
            profile=[(z0,.21),(z0+.095,.21),(z0+.16,.174),(z0+.25,.145),(z0+h-.38,.137),
                     (z0+h-.28,.17),(z0+h-.22,.19),(z1-.085,.245),(z1,.245)]
            b.lathe((x,y),profile,BRICK,10 if lod else 18,'Red brick / engaged round shafts')
    n=24 if lod else 48
    for lo,hi,inner,outer,mat,label in [
        (.02,.48,R-.38,R+.085,GREY,'stone plinth'),
        (.56,.65,R-.29,R+.09,STONE,'base moulding'),
        (3.46,3.60,R-.35,R+.19,GREY,'first floor string'),
        (7.18,7.36,R-.36,R+.26,STONE,'curved balcony slab'),
        (11.12,11.26,R-.32,R+.205,SHADOW,'upper brick band'),
        (11.35,11.61,R-.35,R+.31,GREY,'drum cornice'),
        (11.63,11.84,R-.34,R+.16,BRICK,'drum sill'),
        (DRUM-.17,DRUM,R-.39,R+.105,GREY,'low surviving attic cap')]:
        arc_slab(b,inner,outer,lo,hi,mat,label,n)
    for lower_rail,h,rad,mat in [(3.68,.65,R-.09,IRON),(7.34,.65,R+.13,STONE)]:
        arc_slab(b,rad-.042,rad+.05,lower_rail+h,lower_rail+h+.065,mat,'segmented balcony handrail',n)
        for i in range(1,AXES*(3 if lod else 6)):
            a=START+(END-START)*i/(AXES*(3 if lod else 6));x,y,_=radial(a,rad,0)
            b.lathe((x,y),[(lower_rail,.039),(lower_rail+h,.039)],mat,6,'Gallery / vertical railing')
    for i in range(17 if lod else 32):
        a=START+(END-START)*(i+.5)/(17 if lod else 32);x,y,_=radial(a,R+.11,0)
        b.box((x,y,11.28),(.10,.16,.17),SHADOW,label='Upper cornice / modillion')
    # Only the current low roof is represented. The conical spire belongs to the 1908 source.
    angles=[START+(END-START)*i/n for i in range(n+1)]
    roof=Polygon([(0,0)]+[radial(a,R+.02,0)[:2] for a in angles])
    b.plan_prism(roof,DRUM-.07,DRUM-.015,GREY,'Upper drum / flat low roof')

def street_wall(f,axes,lod,porch=False):
    holes=[]
    for i,x in enumerate(axes):
        entry=(porch and i==len(axes)-1)
        if entry:
            hole=opening(f,x,.02,1.37,2.75,.52,2,3,'recessed arched entrance')
            f.prism(hole.buffer(.185).difference(hole),-.05,.135,SHADOW,'entrance hood')
            pediment=Polygon([(x-.92,3.06),(x+.92,3.06),(x+.59,3.25),(x,3.49),(x-.59,3.25)])
            f.prism(pediment,-.08,.15,GREY,'small entrance pediment')
        else:
            hole=opening(f,x,.77,1.29,2.04,.085,1,1,'ground light');awning(f,x,1.38,2.89,lod)
        holes.append(hole)
        for z in (3.96,7.83):
            holes.append(opening(f,x,z,1.37,2.81,.23,2,3,'street sash'))
    f.wall(.02,EAVE-.18,holes,.44,BRICK)
    for z,h,depth,mat in [(.27,.54,.54,GREY),(.66,.09,.59,STONE),(3.52,.16,.66,GREY),
                          (7.28,.15,.64,GREY),(11.0,.115,.63,SHADOW),(11.39,.19,.73,GREY)]:
        f.box(0,z,f.length+.018,h,depth,.02,mat,'horizontal stringcourse')
    for i in range(len(axes)-1):
        x=(axes[i]+axes[i+1])/2
        for z in (5.50,9.38):f.box(x,z,.34,3.38,.19,.04,BRICK,'brick pier')
    f.box(0,11.67,f.length,.42,.26,-.15,BRICK,'parapet below attic')

def facade(b,lod=False):
    corner(b,lod)
    ax,ay,_=radial(START,R,0);bx,by,_=radial(END,R,0)
    west=Facade(b,(ax-8.20,ay),(ax,ay),'Dianchi front')
    east=Facade(b,(bx,by),(bx,by+7.90),'East return')
    street_wall(west,[-2.66,0,2.69],lod,porch=True)
    street_wall(east,[-2.50,0,2.51],lod)
