"""Street-facing architectural study based on Stewart Young collection, Yo-s23."""
from shapely.geometry import box, Polygon
from shapely.ops import unary_union
from photo_architecture import Facade, opening

STONE = 'pale grey facing stone'
PIER = 'light tooled stone'
JOINT = 'recessed stone'
SILL = 'limestone sill'
GLASS = 'period window glass'
FRAME = 'painted steel sash'
DARK = 'dark historical infill'
CUT = 'neutral section'
PALETTE = {
    STONE:{'color':[.58,.565,.525],'roughness':.88},
    PIER:{'color':[.625,.605,.55],'roughness':.87},
    JOINT:{'color':[.40,.39,.36],'roughness':.90},
    SILL:{'color':[.58,.56,.50],'roughness':.82},
    GLASS:{'color':[.135,.18,.195],'metallic':.13,'roughness':.46},
    FRAME:{'color':[.22,.236,.23],'metallic':.18,'roughness':.59},
    DARK:{'color':[.148,.157,.158],'roughness':.88},
    CUT:{'color':[.44,.445,.437],'roughness':.92}
}
HALF = 22.16
CENTRE_EDGE = 7.19
WING_EDGE = 13.05
LEVELS = [5.14,8.20,11.29,14.40,17.55,20.81]
CENTRE = [-6.38,-3.83,-1.28,1.28,3.83,6.38]
WING = [13.80,16.13,18.54,20.95]
BACK = 1.79


def surface(f,x0,z0,x1,z1,back,front,material,label):
    f.prism(box(x0,z0,x1,z1),back,front,material,label)


def historic_window(f,x,z,w,h,lod,attic):
    void=box(x-w/2,z,x+w/2,z+h)
    f.prism(void.buffer(.009,join_style=2),-.298,-.27,GLASS,'inset glazing')
    frame=void.difference(void.buffer(-.057,join_style=2))
    columns=2 if not attic or lod else 3
    bars=[frame]
    for i in range(1,columns):
        u=x-w/2+w*i/columns
        bars.append(box(u-.022,z,u+.022,z+h))
    if not attic:
        for frac in ([.58] if lod else [.32,.66]):
            bars.append(box(x-w/2,z+h*frac-.019,x+w/2,z+h*frac+.019))
    f.prism(unary_union(bars),-.260,-.203,FRAME,'painted steel casement bars')
    surface(f,x-w/2-.035,z-.047,x+w/2+.035,z+.010,-.05,.065,SILL,'shallow sill')
    return void


def facing(f,lo,hi,zmax,field,lod):
    # Shallow, alternating facing joints are discernible in the 2013 street photograph.
    if lod:return
    row=0
    while row*.87<zmax:
        z=row*.87
        for i in range(-1,int((hi-lo)/1.75)+1):
            u=lo+(i+.50*(row%2))*1.75
            x0=max(lo,u+.013);x1=min(hi,u+1.75-.013)
            if x1<=x0:continue
            stone=field.intersection(box(x0,z+.011,x1,min(z+.86,zmax)))
            if stone.area>.018:f.prism(stone,.001,.016,STONE,'staggered facing joints')
        row+=1


def glazed_range(builder,name,lo,hi,front,zmax,columns,lod):
    f=Facade(builder,(lo,front),(hi,front),name);mid=(lo+hi)/2
    local=[u-mid for u in columns];L=(hi-lo)/2
    holes=[]
    for z in LEVELS:
        holes.extend(historic_window(f,x,z,.91,1.79,lod,False)for x in local)
    for i,x in enumerate(local):
        width=1.72 if i not in (0,len(local)-1) else 1.43
        holes.append(historic_window(f,x,25.11,width,1.33,lod,True))
    # The ground tier is treated as a sealed architectural relief of the photographic elevation.
    for x in local:
        if name=='central six bays'and abs(x)<2.1:continue
        panel=box(x-.46,1.25,x+.46,3.16)
        holes.append(panel);f.prism(panel.buffer(.01,join_style=2),-.215,-.18,DARK,'historic base panel')
    if name=='central six bays':
        portal=box(-2.45,.03,2.45,3.55)
        holes.append(portal);f.prism(portal.buffer(.01,join_style=2),-.21,-.18,DARK,'archival central ground-tier panel')
        surface(f,-2.71,3.56,2.71,3.83,-.10,.055,PIER,'central historical lintel')
    field=box(-L,0,L,zmax).difference(unary_union(holes))
    f.prism(field,-.33,0,STONE,'punctured stone face')
    facing(f,-L,L,zmax,field,lod)
    for a,b in zip(local,local[1:]):
        x=(a+b)/2
        # Photo shows a broad unbroken pier separating the narrower window stacks.
        surface(f,x-.44,4.80,x+.44,22.79,-.014,.047,PIER,'shallow uninterrupted pier')
    surface(f,-L,zmax-.10,L,zmax,-.31,.088,SILL,'flat parapet coping')
    builder.box(((lo+hi)/2,(front+.33+BACK)/2,zmax-.12),(hi-lo,BACK-front-.33,.24),CUT,label=name+' upper section')
    builder.box(((lo+hi)/2,BACK-.12,zmax/2),(hi-lo,.24,zmax),CUT,label=name+' rear cut wall')


def raised_band(builder,side,lod):
    x=side*(CENTRE_EDGE+WING_EDGE)/2;w=WING_EDGE-CENTRE_EDGE;front=-.15;top=28.89
    label='east stone band' if side<0 else 'west stone band'
    f=Facade(builder,(x-w/2,front),(x+w/2,front),label)
    long=box(-.663,4.48,.663,24.56)
    cap=opening(0,25.72,1.36,.79,arch=.67,segments=10 if lod else 22)
    base=opening(0,.20,1.05,2.45,arch=.50,segments=10 if lod else 22)
    field=box(-w/2,0,w/2,top).difference(unary_union([long,cap,base]))
    f.prism(field,-.42,0,PIER,'raised stone strip')
    facing(f,-w/2,w/2,top,field,lod)
    for panel,title,d in [(long,'long shaded architectural panel',-.425),(cap,'semicircular upper recess',-.19),(base,'rounded historical base panel',-.19)]:
        f.prism(panel.buffer(.009,join_style=2),d-.025,d,DARK,title)
    for num in range(6):
        level=4.63+num*3.24
        tilt=side*(.52 if num%2==0 else -.52)
        stripe=Polygon([(-.65,level),(.65,level+tilt),(.65,level+tilt+.34),(-.65,level+.34)])
        f.prism(stripe.intersection(long),-.408,-.29,JOINT,'angled archival panels')
    f.prism(base.buffer(.11,join_style=2).difference(base),-.015,.048,SILL,'arch moulding')
    surface(f,-w/2,top-.12,w/2,top,-.4,.072,SILL,'flat raised coping')
    builder.box((x,(front+.42+BACK)/2,top-.13),(w,BACK-front-.42,.26),CUT,label=label+' roof section')
    builder.box((x,BACK-.12,top/2),(w,.24,top),CUT,label=label+' rear section')


def add_frontage(builder,lod):
    glazed_range(builder,'central six bays',-CENTRE_EDGE,CENTRE_EDGE,.09,27.87,CENTRE,lod)
    for side in (-1,1):
        lo,hi=sorted((side*WING_EDGE,side*HALF))
        cols=sorted(side*v for v in WING)
        glazed_range(builder,'east four bays' if side<0 else 'west four bays',lo,hi,.17,27.39,cols,lod)
        raised_band(builder,side,lod)
        builder.box((side*(HALF-.105),(.17+BACK)/2,27.39/2),(.21,BACK-.17,27.39),CUT,label='lateral cut edge')
        builder.box((side*(WING_EDGE-.105),(.27+BACK)/2,28.89/2),(.21,BACK-.27,28.89),CUT,label='band return')
        builder.box((side*(CENTRE_EDGE+.105),(.27+BACK)/2,28.89/2),(.21,BACK-.27,28.89),CUT,label='band return')
    builder.box((0,(.17+BACK)/2,.035),(2*HALF,BACK-.17,.07),CUT,label='ground section')
