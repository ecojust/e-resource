"""East portico, adjoining round oriel, and two-storey side wall at 759 Kangding Road."""
from math import sin,cos,pi,tau
from pathlib import Path
import sys
from shapely.geometry import Polygon,box,Point
from shapely.ops import unary_union
SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade,opening
from render_finish import ATLAS,stone_uv

WALL='warm pebble render';STONE='pale moulded stone';EDGE='weathered limestone';DARK='shadow in carved stone'
WOOD='reddish brown joinery';GLASS='smoked glass';STEP='grey stone plinth';SOFFIT='cream porch soffit'
PALETTE={k:{'color':list(color),'roughness':rough}for k,color,rough in [
 (WALL,(1,1,1),.93),(STONE,(.77,.748,.684),.78),(EDGE,(.615,.594,.522),.82),
 (DARK,(.38,.365,.315),.91),(WOOD,(.291,.172,.121),.58),(GLASS,(.19,.225,.217),.26),
 (STEP,(.37,.365,.33),.9),(SOFFIT,(.745,.714,.632),.85)]}
PALETTE[WALL]['texture']=str(ATLAS)
LOW=-9.75; HIGH=4.1
WALL_HEIGHT=9.47
BOW=-7.8; ROSE=-5.66; PEDIMENT=-4.60; DOOR=-1.05
SPAN=[(-3.36,0),(-3.52,-1.61),(3.14,-2.36),(3.36,0)]

def straight(builder):
    return Facade(builder,(LOW,0),(HIGH,0),'side wall')

def prism(face,a,b,z0,z1,d0,d1,mat,name):
    face.prism(box(a,z0,b,z1),d0,d1,mat,name)

def cornice(builder,x0,x1,y0,y1,low,tiers,material,name):
    base=box(x0,y0,x1,y1)
    for i,(rise,projection) in enumerate(tiers):
        builder.plan_prism(base.buffer(projection,join_style=2),low,low+rise,material,f'{name} tier {i+1}')
        low+=rise

def surround(face,shape,back,front,width,material,label):
    border=shape.buffer(width,join_style=2).difference(shape)
    face.prism(border,back,front,material,label)

def baluster(builder,x,y,z,segment_count,label):
    profile=[(0,.115),(.065,.115),(.09,.083),(.14,.071),(.21,.100),(.29,.105),
             (.36,.079),(.46,.053),(.52,.056),(.56,.083),(.599,.088),(.637,.074),
             (.66,.098),(.704,.098)]
    builder.lathe((x,y),[(z+h,r) for h,r in profile],STONE,segment_count,label)

def pillar(builder,x,y,idx,lod):
    name=f'porch pier {idx}'
    for i,(z,h,size)in enumerate([(0,.12,.67),(.12,.115,.61),(.235,.10,.56),(.335,.135,.51),
                                (.47,2.9,.45),(3.37,.075,.5),(3.445,.12,.56),(3.565,.14,.60),(3.705,.07,.65)]):
        builder.box((x,y,z+h/2),(size,size,h),STONE if i>1 else STEP,label=f'{name} block {i+1}')
    for sign in [-1,1]:
        face=Facade(builder,(x+sign*.225,y+sign*.225),(x-sign*.225,y+sign*.225),name+' fascia')
        for zz in [.61,3.16]:
            corn=box(-.155,zz,.155,zz+.185)
            face.prism(corn.difference(corn.buffer(-.028,join_style=2)),.002,.019,EDGE,'square return motif')
            fan=[(-.101,zz+.049),(.005,zz+.144),(.101,zz+.049),(.007,zz+.095)]
            face.prism(Polygon(fan),.003,.022,STONE,'carved diamond')
        for u in [-.147,.147]:prism(face,u-.019,u+.019,.84,3.10,.003,.023,EDGE,'narrow vertical arris')
        for side in [-1,1]:
            # Carved scroll brackets below the forward beam, in the plane of the fascia.
            points=[]
            for j in range(13 if lod else 25):
                f=j/(12 if lod else 24);t=2.4*pi*f
                points.append(face.point(side*(.163+.21*f+.105*(1-f)*cos(t)),3.57+.105*(1-f)*sin(t)+.12*f,.085))
            builder.tube(points,.032,STONE,5 if lod else 9,name+' curled corbel')
    return name

def garden_porch(builder,lod):
    outer=Polygon(SPAN)
    builder.plan_prism(outer.buffer(.048,join_style=2),0,.115,STEP,'one stone landing')
    for i,(x,y) in enumerate([(-3.16,-1.43),(2.91,-2.10)],1):pillar(builder,x,y,i,lod)
    for j,(lo,hi,projection,mat) in enumerate([(3.77,3.88,.035,EDGE),(3.88,4.09,.075,STONE),
                                       (4.09,4.15,.095,DARK),(4.15,4.23,.13,STONE),(4.23,4.31,.18,EDGE)]):
        builder.plan_prism(outer.buffer(projection,join_style=2),lo,hi,mat,'terrace beam and soffit '+str(j+1))
    count=10 if lod else 16
    for k in range(3):
        a,b=SPAN[k],SPAN[k+1]; f=Facade(builder,a,b,'porch terrace rail')
        n=[3,11,4][k]
        for z0,z1,w,m in [(4.31,4.43,.19,STONE),(5.11,5.18,.195,STONE),(5.18,5.24,.245,EDGE)]:
            f.box(0,(z0+z1)/2,f.length,z1-z0,w,-.048,m,'coping')
        if k in (0,1,2):
            for i in range(n):
                pt=f.point((i+.5)*f.length/n-f.length/2,0,-.055)
                baluster(builder,*pt[:2],4.42,count,f'porch row {k+1} bottle')
    for i,(x,y) in enumerate(SPAN[1:3],1):
        builder.box((x,y,4.77),(.40,.39,.85),STONE,label=f'terrace carved block {i}')
        face=Facade(builder,(x-.2,y-.195),(x+.2,y-.195),'terrace carved panels')
        ring=Point(0,4.8).buffer(.13,quad_segs=6 if lod else 14)
        surround(face,ring,.004,.023,.021,EDGE,'corner rose ring')
        for j in range(6):
            a=tau*j/6
            petal=Polygon([(0,4.8),(.068*cos(a)-.032*sin(a),4.8+.068*sin(a)+.032*cos(a)),(.115*cos(a),4.8+.115*sin(a)),(.068*cos(a)+.032*sin(a),4.8+.068*sin(a)-.032*cos(a))])
            face.prism(petal,.014,.035,EDGE,'carved corner petals')

def grille(face,shape,columns,heights,label):
    x0,z0,x1,z1=shape.bounds
    outer=shape.buffer(-.006,join_style=2);inner=outer.buffer(-.068,join_style=2)
    lines=[box(x0+(x1-x0)*i/columns-.024,z0,x0+(x1-x0)*i/columns+.024,z1)for i in range(1,columns)]
    lines += [box(x0,z-.021,x1,z+.021)for z in heights if z0<z<z1]
    face.prism(shape.buffer(.006,join_style=2),-.175,-.158,GLASS,label+' recessed panes')
    face.prism(outer.difference(inner.difference(unary_union(lines))),-.145,-.079,WOOD,label+' wood sash')

def oriel(builder,lod):
    # The ground-floor wood lights follow the round face below the projecting balcony.
    radius=2.22; half_angle=.825; cx=BOW; cy=1.46
    def polar(t):return (cx+radius*sin(t),cy-radius*cos(t))
    seg=14 if lod else 30
    pts=[polar(-half_angle+2*half_angle*i/seg)for i in range(seg+1)]
    curve=Polygon(pts+[(pts[-1][0],.55),(pts[0][0],.55)])
    for lo,hi,d,m in [(0,.17,.08,STEP),(.17,.33,.045,EDGE),(.33,1.00,0.,WALL),(.99,1.11,.07,STONE),
                       (3.36,3.49,.08,STONE),(3.49,3.70,.13,EDGE),(3.70,3.79,.16,STONE),
                       (3.79,3.99,.09,WALL),(3.99,4.09,.16,STONE)]:
        builder.plan_prism(curve.buffer(d,join_style=1,quad_segs=4 if lod else 8),lo,hi,m,'oriel continuous curved moulding')
    bays=5
    for j in range(bays):
        a=-half_angle+2*half_angle*j/bays
        b=-half_angle+2*half_angle*(j+1)/bays
        f=Facade(builder,polar(a),polar(b),f'bow light {j+1}')
        f.prism(box(-f.length/2,1.105,f.length/2,3.36),-.075,-.06,GLASS,'round oriel glazing')
        for k in [-1,1]:
            f.box(k*(f.length/2-.031),2.23,.062,2.25,.08,.012,WOOD,'radial casing')
        for z,h in [(1.14,.055),(1.35,.046),(2.98,.07),(3.15,.04),(3.335,.05)]:
            f.box(0,z,f.length,h,.07,.012,WOOD,'transom')
        for k in [-1,1]:f.box(k*f.length*.23,3.16,.027,.28,.044,.012,WOOD,'small rectangular top light')
    for j in range(13):
        p=polar(-half_angle+2*half_angle*(j+.5)/13);baluster(builder,*p,4.08,9 if lod else 14,'bow balcony bottle')
    for j in range(seg):
        f=Facade(builder,pts[j],pts[j+1],'bow balcony rail')
        f.box(0,4.83,f.length+.015,.145,.205,0,STONE,'curved stone coping')

def flower(face,u,z,lod):
    r=.43;disc=Point(u,z).buffer(r,quad_segs=12 if lod else 24)
    face.prism(disc,.003,.024,STONE,'round rosette field')
    for rad,th,dep in [(.435,.030,.083),(.35,.018,.052),(.094,.03,.094)]:
        obj=Point(u,z).buffer(rad,quad_segs=12 if lod else 24)
        face.prism(obj.difference(obj.buffer(-th)),.024,dep,EDGE,'rosette moulding')
    for i in range(8):
        t=tau*i/8
        def pt(rr,ac):return (u+rr*cos(t)-ac*sin(t),z+rr*sin(t)+ac*cos(t))
        shell=[pt(.09,0),pt(.16,-.055),pt(.285,-.065),pt(.327,0),pt(.279,.062),pt(.16,.052)]
        face.prism(Polygon(shell),.025,.049,STONE,'flower petal')
        vs=[face.point(x,h,.049) for x,h in shell]+[face.point(*pt(.224,0),.097)]
        face.builder.add(vs,[(j,(j+1)%6,6)for j in range(6)],EDGE,'flower carved ridges')

def add_geometry(builder,lod):
    offset=(LOW+HIGH)/2
    f=straight(builder)
    def at(x):return x-offset
    openings=[];wins=[]
    door=opening(at(DOOR),.115,1.43,2.87,.715,16 if lod else 34);openings.append(door)
    surround(f,door,-.22,.086,.13,STONE,'round door archivolt')
    grille(f,door,2,[.50,2.23,2.47],'entry')
    for v in [-.30,.30]:
        for z in [.71,1.51]:
            panel=box(at(DOOR)+v-.23,z-.22,at(DOOR)+v+.23,z+.22)
            f.prism(panel,-.078,-.068,WOOD,'recessed door panel')
            f.prism(panel.difference(panel.buffer(-.035)), -.068,-.035,WOOD,'door panel bead')
    for x,base,w,h,arc in [(PEDIMENT,.83,1.05,2.20,0),(PEDIMENT,5.11,1.04,2.35,0),
                           (BOW,4.07,1.72,3.33,0),(-.85,4.31,1.42,3.07,0),(2.45,4.31,1.26,3.05,0)]:
        shape=opening(at(x),base,w,h,arc);openings.append(shape);wins.append((shape,base,h))
    bow_cut=box(at(BOW)-1.57,1.10,at(BOW)+1.57,3.37);openings.append(bow_cut)
    f.wall(.02,WALL_HEIGHT,openings,thickness=.48,material=WALL)
    for shape,base,h in wins:
        grille(f,shape,2,[base+.30*h,base+.75*h,base+.88*h],'side window')
        surround(f,shape,-.02,.062,.087,STONE,'window surround')
        low,_,hi,_=shape.bounds
        prism(f,low-.15,hi+.15,base-.115,base-.018,-.028,.105,STONE,'projecting sill')
    u=at(PEDIMENT)
    for side in [-1,1]:
        a=u+side*.65;b=u+side*.24
        f.prism(Polygon([(a,3.17),(a,3.25),(b,3.47),(b,3.38)]),-.028,.11,STONE,'split triangular hood')
    flower(f,at(ROSE),3.64,lod)
    for p_x in [-6.05,-5.57]:
        prism(f,at(p_x)-.14,at(p_x)+.14,1.15,2.81,.003,.029,STONE,'raised narrow panel beneath flower')
    for z,th,d in [(.19,.19,.10),(.4,.09,.072),(8.29,.15,.093),(8.52,.12,.14),(8.71,.15,.19),(8.90,.13,.255),(9.06,.09,.29)]:
        f.box(0,z,f.length,th,d*2,0,EDGE if z in (.19,8.71) else STONE,'sidewall horizontal moulding')
    for j in range(15):
        x=LOW+.17+j*(HIGH-LOW-.40)/14
        f.box(at(x),8.61,.18,.22,.17,.085,STONE,'eave dentil')
    for j in range(15):
        z=.54+j*.53
        prism(f,-f.length/2,-f.length/2+.43+(.14 if j%2 else 0),z,z+.48,.001,.084,STONE,'alternating corner quoins')
    # Short return at the south corner. The separate curved south loggia remains outside the slice.
    side=Facade(builder,(LOW,1.66),(LOW,0),'southern corner return')
    side.wall(.02,WALL_HEIGHT,thickness=.29,material=WALL)
    side.box(0,8.92,side.length,.17,.29,.07,STONE,'cornice return')
    builder.plan_prism(box(LOW,0,HIGH,1.66),9.31,9.47,EDGE,'narrow rear junction slab')
    garden_porch(builder,lod);oriel(builder,lod)
    for part in builder.parts:
        if part['material']==WALL:part['texcoords']=[(u,1-v)for u,v in (stone_uv(*p)for p in part['vertices'])]
