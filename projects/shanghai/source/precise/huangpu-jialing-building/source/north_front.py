"""Nanjing Road north end, after the dated street photograph and the footprint edge."""
from math import cos,sin,pi
from shapely.geometry import Polygon,box,Point,LineString
from shapely.ops import unary_union
from photo_architecture import Facade

WALL='grey-brown rendered masonry'
BASE='pale grey granite'
PLINTH='dark polished granite'
GLASS='blue-grey glazing'
METAL='painted steel frame'
BRONZE='patinated bronze relief'
JOINT='recessed masonry joint'
OCHRE='ochre parapet panels'
CREAM='sandstone spandrel ornament'
NEUTRAL='plain section'
PALETTE={WALL:{'color':[.54,.48,.42],'roughness':.88},BASE:{'color':[.64,.61,.58],'roughness':.79},
 PLINTH:{'color':[.27,.245,.23],'roughness':.56},GLASS:{'color':[.225,.284,.302],'metallic':.15,'roughness':.32},
 METAL:{'color':[.24,.24,.225],'metallic':.30,'roughness':.48},BRONZE:{'color':[.34,.275,.20],'metallic':.47,'roughness':.55},
 JOINT:{'color':[.365,.335,.30],'roughness':.93},OCHRE:{'color':[.63,.394,.235],'roughness':.86},
 CREAM:{'color':[.76,.66,.52],'roughness':.81},NEUTRAL:{'color':[.40,.37,.34],'roughness':.9}}
HALF=8.75
BACK=2.03
WINDOWS=[-5.65,-2.28,-.83,.72,2.18,5.85]
LEVELS=[10.46,13.62,16.79,19.97,23.14,26.31]
CROWN=[(-HALF,-2.78,29.81),(-2.78,2.75,30.63),(2.75,HALF,29.81)]


def window(f,x,z,w,h):
    p=box(x-w/2,z,x+w/2,z+h)
    d=.30
    f.prism(p.buffer(.01,join_style=2),-d-.02,-d,GLASS,'steel window panes')
    bars=unary_union([p.difference(p.buffer(-.044,join_style=2)),box(x-.026,z,x+.026,z+h*.76),
        box(x-w/2,z+.75*h-.027,x+w/2,z+.75*h+.027)])
    f.prism(bars,-d+.009,-d+.055,METAL,'mullions and transom')
    f.prism(box(x-w/2-.038,z-.043,x+w/2+.038,z+.012),-.018,.042,WALL,'shallow cement sills')
    return p


def bronze_panel(f,x,z,w,h,lod):
    outline=box(x-w/2,z,x+w/2,z+h)
    f.prism(outline,-.145,-.10,PLINTH,'dark recessed side panels')
    rim=outline.buffer(-.022,join_style=2).difference(outline.buffer(-.10,join_style=2))
    f.prism(rim,-.093,-.050,BRONZE,'bronze panel frames')
    details=[]
    for i in range(1,7):
        zz=z+i*h/7
        details.append(box(x-w*.41,zz-.016,x+w*.41,zz+.016))
    for cy,rad in [(z+h*.51,w*.265),(z+h*.69,w*.14),(z+h*.31,w*.145)]:
        ring=Point(x,cy).buffer(rad,quad_segs=12 if lod else 20).boundary.buffer(.021,quad_segs=2)
        details.append(ring)
        if not lod:
            for k in range(8):
                ang=k*pi/4
                details.append(Point(x+cos(ang)*rad*.58,cy+sin(ang)*rad*.58).buffer(rad*.092,quad_segs=3))
    if not lod:
        for zz in [z+h*.17,z+h*.83]:
            for s in [-1,1]:
                details.append(Polygon([(x,zz+.11),(x+s*.18,zz+.03),(x+s*.27,zz+.12),(x+s*.13,zz-.06),(x,zz-.11)]))
    f.prism(unary_union(details),-.070,-.033,BRONZE,'raised rings and crossbars')
    return outline


def frieze(f,left,right,height,lod):
    h=height;w=right-left
    f.prism(box(left,h-.74,right,h-.105),.022,.092,OCHRE,'ochre frieze panels')
    f.prism(box(left,h-.805,right,h-.72),.018,.155,WALL,'lower frieze moulding')
    f.prism(box(left,h-.14,right,h+.02),.018,.168,WALL,'parapet coping')
    count=round(w/.62);marks=[]
    for i in range(count):
        u=left+w*i/count;v=left+w*(i+1)/count;c=(u+v)/2;s=v-u
        marks.append(Polygon([(u,h-.66),(u+s*.14,h-.50),(c,h-.275),(v-s*.12,h-.49),(v,h-.62),
            (v-s*.11,h-.66),(c,h-.434),(u+s*.12,h-.64)]))
        if not lod:marks.append(Polygon([(c-.053,h-.67),(c,h-.55),(c+.053,h-.67),(c,h-.73)]))
    f.prism(unary_union(marks),.093,.124,CREAM,'pointed parapet motifs')


def add_front(builder,lod):
    # Outward is local −Y, toward the pedestrian street. +X follows the building edge westwards.
    f=Facade(builder,(-HALF,.10),(HALF,.10),'north wall')
    opening=[]
    for col,x in enumerate(WINDOWS):
        side=col in [0,5];width=1.23 if side else 1.03
        for j,base in enumerate(LEVELS):
            z=base+(.28 if side else 0);h=1.65
            opening.append(window(f,x,z,width,h))
            if j+1==len(LEVELS):continue
            if not lod:
                for sx in [-.43,-.34,.34,.43]:
                    f.prism(box(x+sx-.010,z+h+.06,x+sx+.010,z+3.10),.007,.021,JOINT,'reeded window spandrels')
        for edge in [-1,1]:
            u=x+edge*(width/2+.073)
            f.prism(box(u-.022,10.42,u+.022,28.36),.003,.078,WALL,'recess borders')
    upper=unary_union([box(lo,10.17,hi,z)for lo,hi,z in CROWN]);f.prism(upper.difference(unary_union(opening)),-.34,0,WALL,'north wall with six window stacks')
    for x in [-1.56,-.055,1.47]:
        verts=[(x-.14,10.06),(x+.14,10.06),(x+.14,30.62),(x+.061,30.83),(x-.055,30.94),(x-.14,30.77)]
        f.prism(Polygon(verts),.012,.29,WALL,'three projecting roof fins')
        if not lod:f.prism(box(x-.022,10.19,x+.022,30.67),.292,.313,WALL,'rib faces')
    for lo,hi,h in CROWN:frieze(f,lo+.035,hi-.035,h,lod)
    base=Facade(builder,(-HALF,.00),(HALF,.00),'granite base')
    door=box(-2.83,.04,2.83,8.05);cut=[door]
    for x in [-5.79,6.0]:
        cut.append(bronze_panel(base,x,1.58,1.31,3.15,lod));cut.append(bronze_panel(base,x,6.13,1.34,1.87,lod))
        reeds=[]
        for i in range(6):
            u=x-.53+i*.21;reeds.append(box(u-.025,4.97,u+.025,5.90))
        base.prism(unary_union(reeds),.006,.053,BRONZE,'short fluted bronze spandrels')
    stone=box(-HALF,0,HALF,10.27).difference(unary_union(cut))
    base.prism(stone,-.37,0,BASE,'granite storefront and square-cut banking portal')
    for lo,hi in [(-HALF,-4.48),(4.45,HALF)]:
        base.prism(box(lo,.06,hi,1.53),.006,.074,PLINTH,'polished lower stone plinth')
        base.prism(box(lo,8.76,hi,9.50),.011,.067,PLINTH,'dark upper band')
    for z in [2.91,5.90,8.13,9.83]:
        cuts=stone.intersection(box(-HALF,z-.012,HALF,z+.012));base.prism(cuts,.002,.013,JOINT,'fine granite joints')
    for side in [-1,1]:
        x=side*2.78;builder.box((x,.79,4.08),(.10,1.57,7.96),BASE,label='portal return')
    builder.box((0,.79,8.04),(5.64,1.57,.11),BASE,label='portal soffit')
    inner=Facade(builder,(-HALF,1.54),(HALF,1.54),'recessed banking entrance')
    inner.prism(box(-2.76,.52,2.76,8.02),-.044,-.008,GLASS,'entrance glazing')
    bars=[box(-2.75,5.43,2.75,5.57),box(-2.75,3.72,2.75,3.84)]
    for u in [-2.63,-1.32,-.12,1.36,2.63]:bars.append(box(u-.042,.51,u+.042,7.96))
    inner.prism(unary_union(bars),.005,.069,METAL,'entrance door stiles and transoms')
    for i in range(4):
        y=.20+i*.29;h=.135*(i+1)
        builder.box((0,(y+1.54)/2,h/2),(5.48,1.54-y,h),PLINTH,label='granite entrance steps')
    for lo,hi,h in CROWN:
        builder.box(((lo+hi)/2,(.44+BACK)/2,h-.095),(hi-lo,BACK-.44,.19),NEUTRAL,label='upper cut surface')
        builder.box(((lo+hi)/2,BACK-.10,h/2),(hi-lo,.20,h),NEUTRAL,label='rear cut surface')
    for x in [-HALF+.058,HALF-.058]:builder.box((x,BACK/2,29.8/2),(.116,BACK,29.8),NEUTRAL,label='edge section')
    builder.box((0,(1.55+BACK)/2,.034),(2*HALF,BACK-1.55,.068),NEUTRAL,label='ground section')
    # The western corner meets a lower attached city mesh. Taper the terminal 1.75 m
    # toward the surveyed party line instead of pushing a rectangular cut through it.
    for part in builder.parts:
        def fit_west_return(vertex):
            x,y,z=vertex
            fraction=min(1.0,max(0.0,(x-7.0)/(HALF-7.0)))
            return x-fraction*(.37+.17*max(0.,y)),y,z
        part['vertices']=[fit_west_return(v) for v in part['vertices']]
