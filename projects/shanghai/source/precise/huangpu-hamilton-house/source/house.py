"""Five facets of the southeast corner apartment house at 170 Middle Jiangxi Road."""
from pathlib import Path
import math
import numpy as np
from shapely import affinity
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from sign_lettering import lettering_shapes

BRICK='grey brown face brick'
STONE='sandstone coloured cast stone'
PANEL='dark entrance stone'
IRON='painted steel casements'
GLASS='grey blue residential glazing'
GREEN='green canvas sunshade'
GOLD='gilded sign characters'
METAL='silver canopy trim'
ROOF='grey roof felt'
AC='painted condenser case'
SHADE='dark interior and vents'
PALETTE={
    BRICK:{'color':[.46,.416,.346],'roughness':.91},STONE:{'color':[.56,.507,.426],'roughness':.86},
    PANEL:{'color':[.225,.225,.208],'roughness':.68},IRON:{'color':[.190,.189,.171],'roughness':.57,'metallic':.31},
    GLASS:{'color':[.265,.312,.326],'roughness':.32,'metallic':.23},GOLD:{'color':[.72,.52,.18],'roughness':.38,'metallic':.55},
    METAL:{'color':[.476,.486,.474],'roughness':.55,'metallic':.41},ROOF:{'color':[.342,.34,.317],'roughness':.90},
    AC:{'color':[.613,.615,.567],'roughness':.71},SHADE:{'color':[.11,.125,.127],'roughness':.83},
    GREEN:{'color':[.169,.244,.180],'roughness':.90}}
FONT=Path(__file__).with_name('fonts')/'FuzhouFacadeLetters.otf'
RADIUS=13.95928
def arc(degrees):
    a=math.radians(degrees)
    return (RADIUS*math.sin(a),RADIUS*(math.cos(a)-1))
ARC=[arc(a)for a in (-56.3,-39.7,-16.7,16.7,39.7,56.3)]
LEFT=(-16.57,-.87)
RIGHT=(16.33,-.58)
# The two low wings end before the original party lines. The upper volumes
# are set back in depth progressively. Their unobserved cut faces stay plain.
BASE=[LEFT,*ARC,RIGHT,(13.4,2.76),(7.7,4.12),(3.42,6.56),(-3.28,6.56),(-8.1,4.14),(-13.51,2.6)]
CENTRES=[10.68,14.15,17.63,21.11,24.59,28.07,31.55,35.03,38.51,41.99]
TOPS=[39.42,45.65,53.00,45.65,39.42]
LOWER=32.95

def panel(f,u,z,w,h,back,front,mat,label):
    f.box(u,z,w,h,front-back,(back+front)/2,mat,label)

def window(f,x,z,w,h,lod,label,arch=0,split=True,blind=False):
    shape=opening(x,z,w,h,arch=arch,segments=8 if lod else 19)
    f.prism(shape.buffer(.007,join_style=2),-.35,-.32,GLASS,label+' glass')
    inner=shape.buffer(-.061,join_style=2)
    bars=[box(x-w/2,z+h*.73-.024,x+w/2,z+h*.73+.024)]
    if split:bars.append(box(x-.024,z,x+.024,z+h))
    gr=shape.buffer(-.008,join_style=2).difference(inner.difference(unary_union(bars)))
    f.prism(gr,-.30,-.18,IRON,label+' steel sash')
    if blind and not lod:panel(f,x,z+h*.81,w-.18,h*.21,-.325,-.305,AC,'pale half-drawn blind')
    if not lod:panel(f,x,z-.044,w+.11,.095,-.019,.087,STONE,'shallow window sill')
    return shape

def grille(f,x,z,lod):
    # Individually positioned street-visible condenser boxes. The fan circles,
    # central hubs, grilles and ledges belong to the full-detail mesh.
    panel(f,x,z,.76,.48,.015,.36,AC,'air conditioning units')
    if lod:return
    panel(f,x-.13,z,.40,.36,.36,.381,SHADE,'fan recess')
    pts=[f.point(x-.13+.157*math.cos(t*math.tau/16),z+.157*math.sin(t*math.tau/16),.395)for t in range(17)]
    f.builder.tube(pts,.013,AC,6,f.label+'/condenser fan ring')
    for i in range(-2,3):
        panel(f,x-.13+i*.058,z,.015,.27,.381,.397,AC,'fan guard bars')
    for i in range(3):panel(f,x+.18,z-.085+i*.072,.16,.014,.36,.388,IRON,'unit slats')
    panel(f,x,z-.27,.88,.048,.01,.42,IRON,'condenser wall mounts')

def entrance(f,lod):
    holes=[]
    for i,x in enumerate((-2.03,0,2.03)):
        w=1.67
        holes.append(opening(x,.075,w,4.20))
        panel(f,x,2.15,w+.02,4.17,-1.52,-1.48,SHADE,'recessed entrance dark lining')
        for sx in (-1,1):
            panel(f,x+sx*(w/2+.014),2.16,.075,4.22,-1.48,-.05,PANEL,'three entrance jambs')
        for j in (-1,1):
            panel(f,x+j*.372,1.61,.70,2.91,-1.40,-1.32,IRON,'domestic entrance door frame')
            panel(f,x+j*.372,1.97,.55,1.84,-1.32,-1.27,GLASS,'inset door glass')
            if not lod:panel(f,x+j*.068,1.30,.046,.23,-1.27,-1.16,METAL,'entrance door pulls')
        panel(f,x,3.61,1.46,.80,-1.42,-1.33,GLASS,'entrance upper transom')
        panel(f,x,4.16,w,.13,-1.48,-.09,PANEL,'recessed entrance soffit')
        panel(f,x,.078,w,.13,-1.48,-.03,PANEL,'stone threshold')
    for x in (-3.82,-1.02,1.02,3.82):
        # The stepped dark stone ends and pale piers stand out in the 2017 entrance image.
        panel(f,x,1.65,.35,3.22,-.03,.16,PANEL,'dark entrance pier')
        panel(f,x,3.69,.30,.88,-.03,.13,STONE,'upper entrance pier')
    panel(f,0,4.53,7.88,.34,-.12,1.36,METAL,'straight grey canopy')
    panel(f,0,4.34,7.65,.05,-.08,1.23,PANEL,'canopy underside')
    for x in (-2.90,-.98,.98,2.90):
        panel(f,x,5.07,.031,.83,.78,.83,IRON,'sign support post')
    for index,char in enumerate('福州大楼'):
        poly=next(iter(lettering_shapes(char,.75,.78,font=FONT)))[1]
        if lod:poly=poly.simplify(.011,preserve_topology=True)
        f.prism(affinity.translate(poly,xoff=(index-1.5)*1.97,yoff=5.32),.828,.917,GOLD,'name inscription '+char)
    return holes

def facet(f,i,lod):
    central=i==2;double=i in (1,3);n=3 if central else 2 if double else 1
    xs=[(j-(n-1)/2)*(2.03 if central else 1.89)for j in range(n)]
    holes=entrance(f,lod) if central else [window(f,x,.44,1.53,3.92,lod,'shopfront',split=False)for x in xs]
    f.wall(0,4.78,holes,.30,PANEL if central else STONE)
    holes=[]
    for x in xs:holes.append(window(f,x,5.23,1.49,2.89,lod,'street first storey',arch=.75 if central else 0))
    nrow=10 if central else 9 if double else 8
    for j,z in enumerate(CENTRES[:nrow]):
        for k,x in enumerate(xs):
            holes.append(window(f,x,z-1.05,1.46 if central else 1.36,2.10,lod,'residential window',split=not lod or (j+k)%4!=0,blind=(j*3+k+i)%8==1))
    if double:
        for x in xs:
            ap=opening(x,41.49,1.32,2.94,.61,segments=8 if lod else 16)
            holes.append(ap)
            # No back panel: the 2017 upper shoulder apertures show open sky.
            panel(f,x,41.45,1.49,.12,-.28,.15,STONE,'open shoulder sill')
    if central:
        for x in xs:
            ap=opening(x,45.64,1.42,5.38,.69,segments=8 if lod else 18);holes.append(ap)
            f.prism(ap.buffer(.013),-.79,-.74,SHADE,'deep crown arcade shadow')
            for j in range(4 if lod else 7):
                panel(f,x,46.09+j*.56,1.27,.055,-.72,-.53,IRON,'recessed tower louvres')
    f.wall(4.78,TOPS[i],holes,.32,STONE if central else BRICK)
    for z in (4.79,8.91):panel(f,0,z,f.length,.17,-.023,.12,STONE,'projecting band')
    for side in (-1,1):
        u=side*(f.length/2-.23);panel(f,u,(8.99+TOPS[i])/2,.39,TOPS[i]-8.99,-.015,.19,BRICK,'terrace edge pier')
        if not lod:panel(f,u,TOPS[i]-.65,.19,.74,.17,.226,STONE,'edge pier cap')
    for j,k in ({0:[(1,0),(4,0)],1:[(0,0),(3,1),(5,1)],2:[(0,2),(1,2),(3,1),(4,2),(6,0)],3:[(0,1),(2,0),(4,1),(7,0)],4:[(2,0),(5,0)]}[i]):
        grille(f,xs[k]+.57,CENTRES[j]-.91,lod)
    if central:
        # A short fabric awning over the centre of the first residential row
        # appears in the 2017 front view; it does not cover the shoulder bays.
        panel(f,0,9.48,4.54,.28,.05,.61,GREEN,'green canvas awning')
        panel(f,0,9.30,4.53,.11,.53,.62,GREEN,'awning valance')

def wing(f,lod):
    xs=[(i-1)*f.length/3 for i in range(3)]
    lower=[window(f,x,.48,1.30,3.82,lod,'short wing street window')for x in xs]
    f.wall(0,4.8,lower,.32,STONE)
    holes=[window(f,x,5.34,1.25,2.48,lod,'wing second storey')for x in xs]
    for j,h in enumerate(CENTRES[:7]):
        for i,x in enumerate(xs):
            holes.append(window(f,x,h-1.02,1.23,2.04,lod,'wing apartment',blind=(j+i)%6==1))
        if j in (0,3,5):grille(f,xs[j%3]+.36,h-.90,lod)
    f.wall(4.8,LOWER,holes,.32,BRICK)
    for z in (4.79,8.91,LOWER-.09):panel(f,0,z,f.length,.16,-.02,.12,STONE,'wing cornice')

def shoulder_back_openings(f):
    """Continue the four open front arches through the recessed shoulder walls."""
    edge=LineString([f.a[:2],f.b[:2]])
    openings=[]
    for index in (1,3):
        front=Facade(f.builder,ARC[index],ARC[index+1],'open shoulder')
        for x in (-.945,.945):
            alley=Polygon([front.point(u,0,d)[:2] for u,d in
                          ((x-.70,.05),(x+.70,.05),(x+.70,-14.),(x-.70,-14.))])
            intersection=edge.intersection(alley)
            if intersection.geom_type!='LineString' or intersection.length<.05:continue
            ds=[float((point-f.center[:2])@f.t[:2])for point in
                np.asarray(intersection.coords)]
            openings.append(box(min(ds)-.03,41.46,max(ds)+.03,44.47))
    return openings

def close_level(b,front,rear,z0,z1,label,lod,above=None,exposed=False):
    ring=[*front,*rear]
    shape=Polygon(ring)
    assert shape.is_valid,(label,ring)
    roof=shape.difference(Polygon(above)) if above else shape
    b.plan_prism(roof,z1-.16,z1,ROOF,label+'/roof')
    for i in range(len(front)-1,len(ring)):
        f=Facade(b,ring[i],ring[(i+1)%len(ring)],label+'/return '+str(i))
        holes=[]
        if exposed and i in (len(front)-1,len(ring)-1) and f.length>3.4:
            for z in CENTRES:
                if z-1.01>z0+.2 and z+1.01<z1-.30:
                    holes.append(window(f,0,z-1.01,1.20,2.02,lod,'upper side window'))
            if z0==TOPS[0]:
                ap=opening(0,41.49,1.22,2.85,.57,segments=8 if lod else 17);holes.append(ap)
        if z0==TOPS[0]:holes.extend(shoulder_back_openings(f))
        f.wall(z0,z1,holes,.25,BRICK)
        if f.length>2.2:panel(f,0,z1-.08,f.length,.13,-.015,.056,STONE,'return coping')

def crown(b,lod):
    pts=[(-3.06,.51),(3.06,.51),(3.69,1.22),(3.69,3.91),(3.15,4.54),(-3.15,4.54),(-3.69,3.91),(-3.69,1.22)]
    for i,a in enumerate(pts):
        f=Facade(b,a,pts[(i+1)%len(pts)],'Crown/pale fluted drum '+str(i))
        front=i==0;side=i in (2,6)
        holes=[]
        if front:
            for x in (-1.52,-.76,0,.76,1.52):
                ap=opening(x,54.48,.19,3.51,.09,segments=5 if lod else 9);holes.append(ap)
                f.prism(ap,-.37,-.33,GLASS,'inset vertical crown lights')
                panel(f,x,55.50,.19,.070,-.32,-.23,IRON,'transom on crown light')
        if side:
            for x in (-.50,.50):
                holes.append(window(f,x,54.81,.27,2.76,lod,'tower flank slit',split=False))
        f.wall(52.72,59.89,holes,.27,STONE)
        if front:
            for x in (-2.40,-1.90,-1.15,-.38,.38,1.15,1.90,2.40):
                panel(f,x,56.57,.105,6.01,-.013,.096,STONE,'edge of crown vertical channel')
            for sign in (-1,1):
                # Higher corner blocks flank the shallow centre, as in the 2017 photograph.
                panel(f,sign*2.71,56.75,.68,7.54,-.21,.24,BRICK,'higher crown corner pier')
                panel(f,sign*2.71,60.42,.73,.19,-.22,.27,STONE,'corner pier cap')
        else:panel(f,0,59.74,f.length,.14,-.03,.046,STONE,'flat crown coping')
    plan=Polygon(pts)
    b.plan_prism(plan,59.73,59.91,ROOF,'Crown/roof')
    b.plan_prism(plan.buffer(-.23,join_style=2),59.89,60.03,ROOF,'Crown/set-in rear coping')

def add_house(b,lod):
    for i,(a,c)in enumerate(zip(ARC,ARC[1:])):
        facet(Facade(b,a,c,'Corner/'+str(i)),i,lod)
    wing(Facade(b,LEFT,ARC[0],'Fuzhou wing'),lod)
    wing(Facade(b,ARC[-1],RIGHT,'Jiangxi wing'),lod)
    low=[(11.49,-.64),(7.36,3.56),(3.06,5.54),(-3.08,5.54),(-7.36,3.56),(-11.49,-.64)]
    middle=[(8.03,1.76),(3.15,4.91),(-3.16,4.91),(-8.03,1.76)]
    high=[(4.11,2.62),(3.46,4.61),(-3.46,4.61),(-4.11,2.62)]
    front=[LEFT,*ARC,RIGHT]
    close_level(b,front,BASE[len(front):],0,LOWER,'ground and short wings',lod,[*ARC,*low])
    close_level(b,ARC,low,LOWER,TOPS[0],'stepped corner mass',lod,[*ARC[1:-1],*middle],True)
    close_level(b,ARC[1:-1],middle,TOPS[0],TOPS[1],'open shoulders',lod,[*ARC[2:4],*high],True)
    close_level(b,ARC[2:4],high,TOPS[1],TOPS[2],'three-arch tower',lod,exposed=True)
    crown(b,lod)
    # Ground-floor body stops at the recessed bronze doors. Each notch belongs
    # to one of three separately modelled entrance portals below the canopy.
    datum=ARC[2][1]
    pockets=unary_union([box(x-.77,datum-.18,x+.77,datum+1.29)for x in (-2.03,0,2.03)])
    b.plan_prism(Polygon(BASE).difference(pockets),.10,.14,PANEL,'Ground/interior structural floor')
