"""River frontage, former archive entrance and the three recovered setbacks on the French Bund."""
from pathlib import Path
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering

STONE='buff washed-stone facing'
REVEAL='grey blue spandrel panel'
GLASS='smoked archive glazing'
SASH='dark bronze casement'
BLACK='charcoal polished granite'
JOINT='recessed ash joint'
BASE='pale granite plinth'
CAP='buff coping stone'
ROOF='asphalt roof terrace'
GOLD='gilded archive name'
STEEL='galvanised metal'
PALETTE={
    STONE:dict(color=[.624,.565,.463],roughness=.91),REVEAL:dict(color=[.424,.469,.474],roughness=.82),
    GLASS:dict(color=[.133,.170,.170],roughness=.25,metallic=.20),SASH:dict(color=[.124,.128,.114],roughness=.57,metallic=.36),
    BLACK:dict(color=[.073,.077,.077],roughness=.49),JOINT:dict(color=[.409,.379,.326],roughness=.94),
    BASE:dict(color=[.486,.493,.462],roughness=.86),CAP:dict(color=[.596,.552,.469],roughness=.79),
    ROOF:dict(color=[.356,.356,.333],roughness=.89),GOLD:dict(color=[.782,.597,.248],roughness=.43,metallic=.60),
    STEEL:dict(color=[.569,.577,.544],roughness=.53,metallic=.51)}
HALF=13.28
CENTRAL=7.65
SOFFIT=7.62
PITCH=3.52
LOW=36.03
MID=39.55
HIGH=43.07
FRONT=[(-HALF,.06),(HALF,.06)]
PLAN=Polygon([*FRONT,(13.34,29.15),(-7.64,37.84),(-13.35,24.13)])
TERRACE=box(-13.11,4.52,13.11,20.35)
CROWN=box(-CENTRAL,.06,CENTRAL,11.86)
FONT=Path(__file__).with_name('fonts')/'RiverArchiveSign.otf'


def glazing(f,windows,depth,label,low):
    if not windows:
        return
    glass=[];bars=[]
    for aperture,cols,transoms in windows:
        l,b,r,t=aperture.bounds
        glass.append(aperture.buffer(.012,join_style='mitre'))
        bars.append(aperture.difference(aperture.buffer(-.068,join_style='mitre')))
        for c in range(1,cols):
            x=l+(r-l)*c/cols;bars.append(box(x-.035,b,x+.035,t))
        for frac in transoms:
            z=b+(t-b)*frac;bars.append(box(l,z-.028,r,z+.028))
    f.prism(unary_union(glass),-depth-.045,-depth,GLASS,label+' glass')
    f.prism(unary_union(bars),-depth+.025,-depth+(.064 if low else .082),SASH,label+' casements')


def recessed_panels(f,panels,apertures):
    layer=unary_union(panels).difference(unary_union(apertures))
    f.prism(layer,.004,.041,REVEAL,'blue-grey casement spandrels')


def river_front(builder,low):
    f=Facade(builder,*FRONT,'River facade');upper=[];cuts=[];panels=[];sills=[]
    for i in range(10):
        z=SOFFIT+.33+i*PITCH
        for centre in (-4.94,0,4.94):
            for offset in (-1.14,0,1.14):
                u=centre+offset;op=box(u-.433,z,u+.433,z+1.99)
                cuts.append(op);upper.append((op,1,[.80]));sills.append(box(u-.455,z-.085,u+.455,z-.012))
                panels.append(box(u-.451,z-.31 if i==0 else z-PITCH+.07,u+.451,z+1.99))
        if i<8:
            for centre in [-10.57,10.57]:
                for dx in [-.59,.59]:
                    u=centre+dx;op=box(u-.465,z+.04,u+.465,z+1.97)
                    cuts.append(op);upper.append((op,1,[.80]));sills.append(box(u-.48,z-.055,u+.48,z+.01))
    outline=unary_union([box(-HALF,0,HALF,LOW),box(-CENTRAL,LOW,CENTRAL,HIGH)])
    portal=box(-8.13,0,8.13,SOFFIT)
    wing=[]
    for centre in [-10.66,10.66]:
        for dx in [-.63,.63]:
            op=box(centre+dx-.46,2.31,centre+dx+.46,6.58);cuts.append(op);wing.append((op,1,[.42,.84]))
    cuts.append(portal)
    facade=outline.difference(unary_union(cuts));f.prism(facade,-.32,0,STONE,'continuous warm stone envelope');recessed_panels(f,panels,cuts)
    for level in range(10):
        z=SOFFIT+level*PITCH
        # Photo shows a horizontal stone joint continuing through the outer wings.
        band=box(-HALF,z-.038,HALF,z+.012).intersection(facade)
        f.prism(band,.002,.012,JOINT,'horizontal stone bed joints')
    if not low:
        for i in range(1,10):
            z=SOFFIT+i*PITCH
            joints=unary_union([box(x-.011,z+.15,x+.011,z+PITCH-.08) for x in (-12.03,-8.97,-2.51,2.51,8.97,12.03)])
            f.prism(joints.intersection(facade),.002,.013,JOINT,'short panel joints')
        f.prism(unary_union(sills),.001,.089,CAP,'upper casement stools')
    glazing(f,upper,.295,'river windows',low);glazing(f,wing,.33,'outer tall ground windows',low)
    for x in [-10.7,10.7]:f.box(x,.81,5.13,1.62,.12,.03,BASE,'pale base of side wings')
    for left,right,z in [(-HALF,-CENTRAL,LOW),(-CENTRAL,CENTRAL,HIGH),(CENTRAL,HALF,LOW)]:
        f.box((left+right)/2,z-.37,right-left,.09,.16,.04,CAP,'lower cornice line')
        f.box((left+right)/2,z-.04,right-left+.06,.13,.21,.055,CAP,'terminal coping')

    # Winter street photographs show a dark granite frame, one deep central door and two side windows.
    entrance=box(-1.56,.13,1.56,5.96)
    side=[box(x-1.80,2.12,x+1.80,5.85)for x in [-5.08,5.08]]
    face=portal.difference(unary_union([entrance,*side]));f.prism(face,-.40,.32,BLACK,'three-bay granite public entrance')
    for x in [-7.58,-2.87,2.87,7.58]:
        f.box(x,3.41,.39,6.79,.23,.35,BLACK,'outer and inner granite posts')
    f.box(0,7.48,16.34,.18,.23,.38,BLACK,'granite cap above the name band')
    for index,character in enumerate('上海市档案馆'):
        add_facade_lettering(f,character,(index-2.5)*1.51,6.80,.75,.77,.349,.423,GOLD,
                            label=f'Archive name {index+1}',font=FONT)
    glazing(f,[(x,3,[.61])for x in side],.39,'archive sidelights',low)
    glazing(f,[(entrance,2,[.77])],.96,'inset double entrance',low)
    for u in [-1.58,1.58]:f.box(u,3.0,.095,5.98,1.28,-.31,BLACK,'return into entrance')
    f.box(0,6.0,3.17,.10,1.28,-.31,BLACK,'granite head reveal')
    f.box(0,.045,3.16,.09,1.50,-.20,BASE,'threshold')


def upper_wall(builder,a,b,bottom,top,heights,groups,low,label):
    f=Facade(builder,a,b,label);holes=[];glass=[];sil=[]
    for n in range(groups):
        center=(n+.5-groups/2)*f.length/groups
        for z in heights:
            for offset in [-.51,.51]:
                x=center+offset
                shape=box(x-.367,z,x+.367,z+1.92)
                holes.append(shape);glass.append((shape,1,[.79]))
                sil.append(box(x-.387,z-.066,x+.387,z-.005))
    wall=box(-f.length/2,bottom,f.length/2,top)
    f.prism(wall.difference(unary_union(holes)),-.26,0,STONE,'office return')
    glazing(f,glass,.28,'return glazing',low)
    if sil and not low:f.prism(unary_union(sil),.006,.075,CAP,'return sills')
    f.beam(top-.08,.14,.16,CAP,label='return coping')
    return f


def make_messageries(builder,low=False):
    river_front(builder,low)
    builder.plan_prism(PLAN,0,.082,BASE,'ground floor slab')
    ring=list(PLAN.exterior.coords)
    for i,(a,b) in enumerate(zip(ring,ring[1:])):
        if i==0:continue
        heights=[SOFFIT+.37+j*PITCH for j in range(8)]
        upper_wall(builder,a,b,.0,LOW,heights,[0,4,3,2,4][i],low,['','North lane return','West oblique return','Rear side return','South lane return'][i])
    # The orthophoto and the exposed north side establish three roof levels. Depths of returns are estimates.
    builder.plan_prism(PLAN.difference(TERRACE.union(CROWN)),LOW-.34,LOW-.24,ROOF,'base roof terrace')
    lower=list(TERRACE.exterior.coords)
    for a,b in zip(lower,lower[1:]):
        f=Facade(builder,a,b,'Middle setback')
        surface=box(-f.length/2,LOW-.25,f.length/2,MID)
        hidden=abs(a[1]-b[1])<.01 and a[1]<5
        if hidden:
            surface=surface.difference(box(-CENTRAL,LOW-.26,CENTRAL,HIGH))
        f.prism(surface,-.23,0,STONE,'setback walls')
        if not hidden:f.beam(MID-.09,.14,.14,CAP,label='setback coping')
    builder.plan_prism(TERRACE.difference(CROWN),MID-.35,MID-.23,ROOF,'upper terrace')
    upper=list(CROWN.exterior.coords)
    for a,b in zip(upper,upper[1:]):
        if abs(a[1]-b[1])<.01 and a[1]<1:continue
        if abs(a[0]-b[0])<.01:
            upper_wall(builder,a,b,LOW-.25,HIGH,[SOFFIT+.37+8*PITCH,SOFFIT+.37+9*PITCH],2,low,'Crown side returns')
        else:upper_wall(builder,a,b,MID-.25,HIGH,[SOFFIT+.37+9*PITCH],3,low,'Crown inland return')
    builder.plan_prism(CROWN,HIGH-.37,HIGH-.20,ROOF,'central flat crown')
    builder.box((.08,1.92,HIGH-.036),(.54,.54,.38),BASE,label='flagstaff foot')
    builder.tube([(.08,1.92,HIGH+.13),(.08,1.92,HIGH+2.66)],.044,STEEL,sides=8 if low else 14,label='river roof flagstaff')
