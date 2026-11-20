"""The east street wall in the ROCKBUND elevation and completed-project photograph."""
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import lettering_shapes

BRICK='brown face brick'
SPANDREL='red-brown spandrel brick'
PIER='dark purple-brown rib brick'
MORTAR='shadowed brick joints'
STONE='pale water-washed stone'
RECESS='deep stone reveal'
GLASS='blue-grey glazing'
SASH='painted steel frame'
METAL='bronze lettering'
CUT='neutral section'
PALETTE={
    BRICK:{'color':[.41,.255,.196],'roughness':.90},
    SPANDREL:{'color':[.48,.275,.205],'roughness':.88},
    PIER:{'color':[.28,.201,.180],'roughness':.86},
    MORTAR:{'color':[.26,.216,.19],'roughness':.96},
    STONE:{'color':[.70,.65,.55],'roughness':.84},
    RECESS:{'color':[.38,.357,.307],'roughness':.88},
    GLASS:{'color':[.169,.228,.246],'metallic':.15,'roughness':.36},
    SASH:{'color':[.156,.164,.154],'metallic':.22,'roughness':.51},
    METAL:{'color':[.39,.275,.158],'metallic':.60,'roughness':.47},
    CUT:{'color':[.352,.302,.265],'roughness':.91}
}
HALF=11.56
FRONT=.10
BACK=1.98
# Fourteen lower window stacks, in seven pairs. A 25 m scale is printed on the source drawing.
WINDOW_X=[-10.24,-8.82,-7.17,-5.77,-3.925,-2.60,-.84,.52,2.26,3.63,5.40,6.79,8.52,9.91]
FLOORS=[4.56,7.61,10.65,13.71,16.80,19.87,22.96]
MAJOR=[-11.34,-8.01,-4.79,-1.69,1.42,4.53,7.71,11.26]
MINOR=[(a+b)/2 for a,b in zip(WINDOW_X[::2],WINDOW_X[1::2])]


def outline_top():
    return Polygon([(-HALF,4.45),(HALF,4.45),(HALF,26.73),(10.98,26.73),(10.98,28.53),
                    (8.02,28.53),(8.02,26.73),(3.83,26.73),(3.83,29.57),
                    (-3.81,29.57),(-3.81,26.73),(-HALF,26.73)])


def pointed(x,z,w,h):
    # The curved springing rises to the narrow apex seen between the four central pairs of ribs.
    a=w/2;s=z+h-w*.70
    return Polygon([(x-a,z),(x+a,z),(x+a,s),(x+.94*a,s+.20*w),(x+.63*a,s+.46*w),
                    (x,z+h),(x-.63*a,s+.46*w),(x-.94*a,s+.20*w),(x-a,s)])


def light(f,x,z,w,h,gothic=False,store=False):
    hole=pointed(x,z,w,h) if gothic else box(x-w/2,z,x+w/2,z+h)
    recess=.49 if store else .28
    f.prism(hole.buffer(.008,join_style=2),-recess-.025,-recess,GLASS,'glazing')
    inner=hole.buffer(-.055,join_style=2)
    bar=[box(x-.027,z,x+.027,z+h*.70),box(x-w/2,z+h*.68-.026,x+w/2,z+h*.68+.026)]
    if store:
        bar=[box(x-w/2,z+h*.89-.034,x+w/2,z+h*.89+.034)]
    grid=hole.difference(inner.difference(unary_union(bar)))
    f.prism(grid,-recess+.008,-recess+.061,SASH,'steel glazing bars')
    if not store:
        f.prism(box(x-w/2-.03,z-.053,x+w/2+.03,z+.006),-.015,.077,PIER,'shallow brick sills')
    if gothic:
        # Pointed brick brows project from the upper band above the four central windows.
        upper=hole.buffer(.14,join_style=2).difference(hole).intersection(box(x-w,z+h-.43,x+w,z+h+.25))
        f.prism(upper,.023,.16,PIER,'projecting pointed brick window brows')
        tip=Polygon([(x-.17,z+h+.035),(x,z+h+.155),(x+.17,z+h+.035),
                     (x+.09,z+h+.006),(x,z+h+.071),(x-.09,z+h+.006)])
        f.prism(tip,.158,.185,STONE,'pointed hood tips')
    return hole


def spandrel(f,x,lo,hi,lod):
    left=x-.56;right=x+.56
    if hi<=lo:return
    f.prism(box(left,lo,right,hi),-.012,.01,MORTAR,'spandrel mortar')
    if lod:
        f.prism(box(left+.01,lo+.02,right-.01,hi-.02),.012,.022,SPANDREL,'spandrel brick')
        return
    count=max(1,round((hi-lo)/.118))
    for r in range(count):
        a=lo+(hi-lo)*r/count+.008;b=lo+(hi-lo)*(r+1)/count-.008
        for j in range(-1,5):
            start=left+(j+.5*(r%2))*.325
            x0=max(left,start+.008);x1=min(right,start+.317)
            if x1-x0>.04 and b>a:
                f.prism(box(x0,a,x1,b),.012,.027,SPANDREL if (r+j)%5 else BRICK,'stretcher bond spandrels')


def rib_section(x,w,y,depth,major):
    # In plan the broad columns have three ridges, the narrow dividing strips have one.
    if major:
        profile=[(-.5,0),(-.46,.35),(-.31,.27),(-.22,.78),(-.10,.55),
                 (0,1),(.10,.55),(.22,.78),(.31,.27),(.46,.35),(.5,0)]
    else:profile=[(-.5,0),(0,1),(.5,0)]
    return Polygon([(x-w/2,y+.11),*( (x+w*u,y-depth*v) for u,v in profile ),(x+w/2,y+.11)])


def stone_tip(b,x,y,z,w,depth,major):
    # Each pale capital has pointed side lobes folded around the projecting brick ridge.
    factors=[(-.29,.31,.73),(0,.46,1),(.29,.31,.73)] if major else [(0,.83,.76)]
    # A pale backing and its ridge cover the top courses of each shaft. The separate
    # triangular lobes alone would disappear when seen frontally against the brick.
    backing=rib_section(x,w*1.12,y-.021,depth*1.035,major)
    b.prism(backing,z-.075,z+.115,lambda u,v,h:(u,v,h),STONE,'stone collars around brick shafts')
    for offset,fraction,height in factors:
        u=x+w*offset;a=w*fraction/2;h=height*(.51 if major else .38)
        pts=[(u-a,y-.015,z),(u,y-depth,z-.07),(u+a,y-.015,z),
             (u-a*.68,y+.015,z+h*.46),(u+a*.68,y+.015,z+h*.46),(u,y-depth*.65,z+h)]
        b.add(pts,[(0,1,5,3),(1,2,4,5),(3,5,4),(0,3,4,2),(0,2,1)],STONE,'folded limestone finials')


def shaft(b,x,width,top,major):
    foot=4.41;levels=[foot,16.83,19.89,22.98,25.94,top]
    levels=sorted(set(z for z in levels if z<=top))
    for index,(lo,hi) in enumerate(zip(levels,levels[1:])):
        width_i=width*(1-.054*index)
        depth=(.40 if major else .24)*(1-.09*index)
        shape=rib_section(x,width_i,FRONT+.014,depth,major)
        b.prism(shape,lo,hi,lambda u,v,z:(u,v,z),PIER,'crown-section brick pilasters'if major else'pointed secondary brick ribs')
        stone_tip(b,x,FRONT-.008,hi-.22,width_i,depth,major)


def add_frontage(builder,lod):
    f=Facade(builder,(-HALF,FRONT),(HALF,FRONT),'east facade')
    openings=[]
    for column,x in enumerate(WINDOW_X):
        for j,z in enumerate(FLOORS):
            higher=j==len(FLOORS)-1
            middle=column in (5,6,7,8)
            is_pointed=higher and middle
            h=2.19 if is_pointed else 2.02
            openings.append(light(f,x,z,1.01,h,is_pointed))
            if j+1<len(FLOORS):spandrel(f,x,z+h+.05,FLOORS[j+1]-.10,lod)
    for x in WINDOW_X[5:9]:
        top=box(x-.43,27.21,x+.43,28.17)
        openings.append(top)
        f.prism(top.buffer(.008,join_style=2),-.37,-.33,RECESS,'open-shadow attic panels')
    wall=outline_top().difference(unary_union(openings))
    f.prism(wall,-.33,0,BRICK,'historical brick street wall')
    for x in MAJOR+MINOR:
        raised=-3.81<x<3.83
        north=8.02<x<10.98
        h=29.62 if raised else 28.66 if north else 26.78
        shaft(builder,x,.71 if x in MAJOR else .37,h,x in MAJOR)
    # Three upper volumes visible in the design-office street elevation.
    roof=[(-HALF,-3.81,26.73),(-3.81,3.83,29.57),(3.83,8.02,26.73),
          (8.02,10.98,28.53),(10.98,HALF,26.73)]
    for lo,hi,h in roof:
        builder.box(((lo+hi)/2,(FRONT+.33+BACK)/2,h-.11),(hi-lo,BACK-FRONT-.33,.22),CUT,label='upper cut roof')
        builder.box(((lo+hi)/2,BACK-.09,h/2),(hi-lo,.18,h),CUT,label='back section')
        if h>27:
            for u in [lo,hi]:
                builder.box((u,(FRONT+.33+BACK)/2,(26.73+h)/2),(.12,BACK-FRONT-.33,h-26.73),BRICK,label='high parapet returns')
    ground=Facade(builder,(-HALF,.02),(HALF,.02),'pale stone storefront')
    storefronts=[]
    for x,w in [(-8.61,3.91),(-4.94,2.90),(4.96,2.92),(8.60,3.91)]:
        storefronts.append(light(ground,x,.27,w,2.90,store=True))
    door=box(-1.08,.12,1.08,3.03)
    storefronts.append(door)
    ground.prism(door.buffer(.009,join_style=2),-.63,-.60,GLASS,'recessed double entrance glazing')
    frame=door.difference(door.buffer(-.077,join_style=2)).union(box(-.035,.12,.035,3.03))
    ground.prism(frame,-.585,-.515,SASH,'double door frame')
    base=box(-HALF,0,HALF,4.49).difference(unary_union(storefronts))
    ground.prism(base,-.32,0,STONE,'pale stone base and shop surrounds')
    ground.prism(box(-HALF-.075,4.41,HALF+.075,4.56),-.13,.19,STONE,'continuous stone fascia')
    name=Polygon([(-2.97,3.07),(2.97,3.07),(2.97,4.35),(2.37,4.38),(2.27,4.48),
                  (.83,4.48),(.66,4.58),(-.65,4.58),(-.81,4.48),(-2.30,4.48),(-2.41,4.39),(-2.97,4.35)])
    ground.prism(name,.004,.137,STONE,'stepped original name panel')
    font=Path(__file__).with_name('fonts')/'YuanmingyuanPlaque.otf'
    for ch,outline in lettering_shapes('真光大樓',2.77,.48,font=font):
        ground.prism(translate(outline,yoff=3.73),.142,.183,METAL,'raised historical name '+ch)
    for side in (-1,1):
        builder.box((side*(HALF-.085),(.02+BACK)/2,26.73/2),(.17,BACK-.02,26.73),CUT,label='street edge section')
    builder.box((0,(.34+BACK)/2,.034),(2*HALF,BACK-.34,.068),CUT,label='floor section')
