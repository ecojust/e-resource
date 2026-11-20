"""The surviving five bays and upper setbacks along Middle Sichuan Road."""
import math
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening
from postal_geometry import fluted_column
from ornament import capital,shell_pediment,STONE,LIGHT,SAND

GREY='scored grey cement blocks'
JOINT='deep ashlar joints'
STEEL='black steel mullions'
GLASS='smoky blue street glass'
PANEL='ebonised metal spandrels'
BRONZE='patinated bronze metal'
SHADOW='recessed vestibule shadow'
ROOF='grey asphalt flat roof'
TREAD='dark granite entrance treads'
PALETTE={
    STONE:{'color':[.694,.650,.554],'roughness':.88},LIGHT:{'color':[.79,.746,.63],'roughness':.83},
    SAND:{'color':[.696,.634,.51],'roughness':.87},GREY:{'color':[.585,.564,.49],'roughness':.92},
    JOINT:{'color':[.417,.404,.356],'roughness':.95},STEEL:{'color':[.117,.141,.143],'roughness':.51,'metallic':.42},
    GLASS:{'color':[.196,.262,.278],'roughness':.29,'metallic':.31},PANEL:{'color':[.163,.170,.159],'roughness':.61,'metallic':.35},
    BRONZE:{'color':[.234,.188,.135],'roughness':.59,'metallic':.48},SHADOW:{'color':[.089,.091,.081],'roughness':.9},
    ROOF:{'color':[.378,.372,.338],'roughness':.93},TREAD:{'color':[.386,.388,.36],'roughness':.83}}
HALF=12.3095
PITCH=HALF*2/5
AXES=tuple(i*PITCH for i in (-2,-1,0,1,2))
BELT=20.55
TOP=28.77
REAR=2.65


def glazed(f,ap,columns,rows,lod,kind='steel windows',d=-.32,field=GLASS):
    x0,z0,x1,z1=ap.bounds
    f.prism(ap.buffer(.013,join_style=2),d-.025,d,field,kind+' glass')
    inset=ap.buffer(-.078,join_style=2)
    bars=[box(u-.023,z0,u+.023,z1)for u in np.linspace(x0,x1,columns+1)[1:-1]]
    bars.extend(box(x0,h-.023,x1,h+.023)for h in np.linspace(z0,z1,rows+1)[1:-1])
    grid=ap.buffer(-.020,join_style=2).difference(inset.difference(unary_union(bars)))
    f.prism(grid,d+.053,d+.126,STEEL,kind+' sash')


def rustication(f,wall,lod):
    # Large running blocks retain the actual five arch cuts; recessed joints have
    # a measurable width. Crossing a voussoir never fills the aperture.
    rise=.68 if lod else .49
    z=.14
    n=0
    while z<5.25:
        width=2.0 if lod else 1.52
        x=-HALF-(width/2 if n%2 else 0.)
        while x<HALF-.022:
            x0,x1=max(-HALF,x+.022),min(HALF,x+width-.022)
            if x1-x0>.04:
                area=box(x0,z+.022,x1,min(z+rise-.024,5.27)).intersection(wall)
                if area.area>.01:f.prism(area,-.02,.059,GREY,'scored ashlar facing')
            x+=width
        z+=rise;n+=1


def portal_arch(f,u,w,lod):
    h=1.03; spring=3.12
    for j in range(9 if lod else 13):
        n=9 if lod else 13
        a,b=math.pi*j/n+.008,math.pi*(j+1)/n-.008
        ss=np.linspace(a,b,3 if lod else 5)
        outer=[(u+(w/2+.31)*math.cos(t),spring+(h+.32)*math.sin(t))for t in ss]
        inner=[(u+(w/2+.015)*math.cos(t),spring+(h+.012)*math.sin(t))for t in reversed(ss)]
        f.prism(Polygon(outer+inner),.06,.18,STONE,'individual arch voussoirs')
    for side in (-1,1):
        x=u+side*(w/2+.155)
        for j in range(4 if lod else 6):
            count=4 if lod else 6;height=(spring-.16)/count
            f.box(x,.16+(j+.5)*height,.29,height-.031,.175,.085,GREY,'rusticated arch jambs')
        f.box(x,spring,.43,.13,.26,.12,LIGHT,'arch spring imposts')


def entrance(f,ap,lod):
    x0,z0,x1,z1=ap.bounds
    f.prism(ap,-1.41,-1.37,SHADOW,'deep central vestibule')
    # The 2020 front view shows the door and its ascending dark threshold behind
    # the street arches. The old four-leaf revolving door is not assumed extant.
    for j in range(5):
        y=.08+j*.22;top=(j+1)*.106
        f.box(0,top/2,3.18,top,.225,-y-.11,TREAD,'five recessed stone treads')
    for side in (-1,1):
        u=side*.70
        f.box(u,1.74,1.37,2.38,.092,-1.23,BRONZE,'paired entrance doors')
        for z,h in ((.94,.38),(1.62,.63),(2.38,.67)):
            f.box(u,z,1.13,h,.045,-1.15,GLASS if z>1. else PANEL,'recessed door panels')
        f.box(u-side*.45,1.45,.041,.32,.068,-1.09,BRONZE,'door pulls')
        f.box(side*(x1+.002),1.77,.15,3.30,1.16,-.67,GREY,'deep door reveals')
    glazed(f,opening(0,2.96,2.76,1.10,arch=.70,segments=10 if lod else 20),3,2,lod,'arched door transom',d=-1.23)
    f.box(0,3.14,3.12,.13,1.13,-.63,GREY,'vestibule head')


def cornices(f):
    for z,h,pr,mat in ((.15,.21,.13,GREY),(4.73,.15,.26,LIGHT),(5.06,.14,.21,SAND),
                        (5.29,.15,.24,STONE),(7.47,.17,.25,STONE),(7.76,.15,.29,LIGHT),
                        (19.61,.17,.20,STONE),(20.10,.29,.30,LIGHT),(20.40,.15,.42,STONE)):
        f.beam(z,h,pr,mat,width=f.length,label='profiled street cornices')


def front(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'East street elevation')
    # The attic setbacks are built as separate solid planes above this full street wall.
    ground=[opening(u,.24,3.13 if u else 3.26,3.91,arch=1.03,segments=12 if lod else 24)for u in AXES]
    short=[opening(u,5.58,3.24,1.45)for u in AXES]
    tall=[opening(u,8.03,3.35 if u else 3.50,11.41)for u in AXES]
    wall=f.wall(0,BELT,[*ground,*short,*tall],thickness=.40,material=STONE)
    rustication(f,wall,lod)
    for u,arch,small,high in zip(AXES,ground,short,tall):
        portal_arch(f,u,arch.bounds[2]-arch.bounds[0],lod)
        if u==0:entrance(f,arch,lod)
        else:
            glazed(f,arch,3 if lod else 5,3 if lod else 5,lod,'arched shop windows')
            f.box(u,.70,3.06,.80,.09,-.08,GREY,'original shop window lower panels')
        glazed(f,small,2 if lod else 3,2,lod,'second-storey sash')
        glazed(f,high,3 if lod else 5,8 if lod else 13,lod,'three-storey sash')
        for z in (11.56,15.55):
            f.box(u,z,high.bounds[2]-high.bounds[0]-.055,.62,.083,-.139,PANEL,'dark intermediate spandrels')
        f.box(u,7.92,3.59,.14,.22,.035,SAND,'tall window thresholds')
    cornices(f)
    for side in (-1,1):
        # Two subsidiary flat pilasters retain carved crowns; the monumental
        # central pair show carved, fluted round shafts with a projecting balcony below.
        for n,x in enumerate((PITCH*1.5,HALF-.42)):
            u=side*x;w=1.02 if n==0 else .66
            f.box(u,13.52,w,11.75,.215,.044,GREY,'subsidiary pilasters')
            if n==0:capital(f,u,18.47,1.12,lod)
            if not lod:
                for z in (9.79,12.79,15.79,18.46):
                    f.box(u,z,w-.18,.012,.018,.157,SAND,'subtle facing panel joints')
        x=side*PITCH/2
        b.lathe((x,-.32),[(6.61,.32),(6.79,.41),(6.99,.49),(7.28,.53),(7.41,.59),(7.58,.61),(7.69,.57)],
                STONE,16 if lod else 32,'Central axis/present rounded brackets')
        fluted_column(b,(x,-.32),7.65,19.61,r=.485,lod=lod,label='Central axis/fluted attached shaft')
        # The central Corinthian capitals articulate the face and the two side returns.
        cf=Facade(b,(x-.72,-.68),(x+.72,-.68),'Central axis')
        capital(cf,0,18.70,1.26,lod)
        for sign in (-1,1):
            sf=Facade(b,(x+sign*.45,-.32-sign*.37),(x+sign*.45,-.32+sign*.37),'Central column flanks')
            capital(sf,0,18.73,.78,lod)
    f.box(0,7.30,5.22,.37,1.03,.31,STONE,'current balcony and corbel ends')
    f.box(0,7.56,5.28,.22,1.12,.32,LIGHT,'balcony edge cap')
    f.box(0,7.77,5.17,.29,.15,.797,STONE,'low stone balcony parapet')
    for x in (-2.52,2.52):f.box(x,7.77,.14,.29,.69,.51,STONE,'balcony parapet returns')
    f.box(0,19.88,5.69,.42,1.07,.23,LIGHT,'middle axis entablature')
    for x in (-2.46,2.46):
        f.box(x,20.01,.31,.49,.14,.78,SAND,'entablature carved tablets')
        f.box(x,20.01,.16,.27,.059,.895,STONE,'tablet inner moulding')
    capital_edge=Facade(b,(-HALF,-.48),(HALF,-.48),'Central pediment')
    shell_pediment(capital_edge,0,20.34,lod)


def upper_wing(b,start,end,depth,base,top,glazing,lod):
    f=Facade(b,(start,depth),(end,depth),'Upper terrace')
    # The upper two storeys have punched windows within broad stone spandrels.
    # Their openings are much shorter than the curtain-like ribbons below.
    opening_bottom=base+(1.01 if base>24 else .83)
    opening_height=1.86 if base>24 else 1.70
    openings=[opening(u-(start+end)/2,opening_bottom,3.05 if len(glazing)>1 else 2.95,opening_height)for u in glazing]
    f.wall(base,top,openings,thickness=.33,material=GREY)
    for shape in openings:glazed(f,shape,2 if lod else 3,2,lod,'rectangular upper windows')
    # The incomplete inner faces terminate at the retained native roof; no roof
    # equipment from the neighbouring properties is included in this section.
    f.beam(top-.115,.20,.22,LIGHT,width=f.length,label='attic square coping')
    for ap in openings:
        x0,z0,x1,z1=ap.bounds
        f.box((x0+x1)/2,z0-.053,x1-x0+.15,.106,.18,.047,STONE,'shallow attic sills')
        f.box((x0+x1)/2,z1+.047,x1-x0+.17,.088,.12,.020,STONE,'flush attic lintels')
    for sign in (-1,1):
        f.box(sign*(f.length/2-.14),(base+top)/2,.24,top-base-.30,.074,.009,STONE,'setback corner bands')
    f.beam(base+.20,.11,.135,STONE,width=f.length,label='ledge at attic base')
    return f


def upper(b,lod):
    edges=(-HALF,-1.5*PITCH,1.5*PITCH,HALF)
    for z0,z1,depth_end,depth_middle in ((BELT,24.53,.12,.72),(24.53,TOP,.36,1.02)):
        for i,glazing in enumerate(([AXES[0]],list(AXES[1:4]),[AXES[4]])):
            f=upper_wing(b,edges[i],edges[i+1],depth_middle if i==1 else depth_end,z0,z1,glazing,lod)
        for side in (-1,1):
            x=side*1.5*PITCH
            f=Facade(b,(x,depth_end),(x,depth_middle),'Attic/setback return')
            f.wall(z0,z1,thickness=.15,material=GREY)
        # The flat strips behind the visible setback are individualized by level.
        plan=Polygon([(-HALF,depth_end),(-1.5*PITCH,depth_end),(-1.5*PITCH,depth_middle),
                      (1.5*PITCH,depth_middle),(1.5*PITCH,depth_end),(HALF,depth_end),(HALF,REAR),(-HALF,REAR)])
        b.plan_prism(plan,z1-.11,z1,ROOF,'Terraces/flat roof strips')
    b.box((0,1.03,TOP-.05),(3*PITCH,.22,.25),LIGHT,label='Terraces/central attic cap')
    for x in (-HALF+.08,HALF-.08):
        b.box((x,REAR/2,BELT/2),(.16,REAR,BELT),GREY,label='Section/plain side edges')
        for z0,z1,d in ((BELT,24.53,.12),(24.53,TOP,.36)):
            b.box((x,(REAR+d)/2,(z0+z1)/2),(.16,REAR-d,z1-z0),GREY,label='Section/upper side edges')
    b.box((0,REAR-.07,TOP/2),(2*HALF,.14,TOP),GREY,label='Section/plain rear cut face')
    b.plan_prism(box(-HALF,0,HALF,REAR),BELT-.11,BELT,ROOF,'Terraces/front cornice roof edge')
    # Both the 1937 front and the aerial 2020 photograph show the central pole.
    # The flag shown on the 1937 event photograph belongs to that dated view.
    b.tube([(0,.78,22.67),(0,.78,31.68)],.071,BRONZE,7 if lod else 12,'Crown/flagstaff')


def add_geometry(b,lod):
    front(b,lod)
    upper(b,lod)
