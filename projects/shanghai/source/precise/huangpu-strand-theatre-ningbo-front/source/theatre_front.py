"""The photographed Ningbo Road elevation and its southeast chamfer."""
from math import cos, hypot, pi, sin
from pathlib import Path
import numpy as np
from shapely import set_precision
from shapely.affinity import translate
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import lettering_shapes
from brick_mapping import BRICK, LENGTH, END, CHAMFER, brick_uv

HERE = Path(__file__).resolve().parent
RED='Deep red border brick'
STONE='Warm grey moulded stone'
PALE='Light carved stone'
SHADOW='Recessed moulding shadow'
GREEN='Blue green relief tile'
DARK_GREEN='Dark green tile recess'
SASH='Near black window joinery'
GLASS='Grey blue glass'
BRASS='Muted gold letters and handles'
SHOP='Burgundy hotel wall finish'
SHOP_DARK='Dark bronze retail frames'
SHOP_GLASS='Warm ground floor glazing'
BUFF='Plain buff attic brick'
GILT='Gilded cinema inscription'
MOUNT='Aged bronze letter returns'
SIDE_SILL=6.72
SIDE_HEAD=9.76
TOP_SILL=11.79
CENTRE=LENGTH/2
FONT=HERE/'strand-letters.otf'

def material(rgb,roughness=.78,metallic=0.):
    return {'color':rgb,'roughness':roughness,'metallic':metallic}

PALETTE={
    BRICK:{'color':[1.,1.,1.],'roughness':.87,'texture':str(HERE/'strand-diaper-brick.png')},
    RED:material([.39,.18,.125]),STONE:material([.63,.58,.51]),PALE:material([.78,.75,.68]),
    SHADOW:material([.32,.31,.28]),GREEN:material([.17,.30,.26],.55),DARK_GREEN:material([.065,.131,.115]),
    SASH:material([.092,.092,.084],.55),GLASS:material([.152,.225,.255],.32,.17),
    BUFF:material([.59,.46,.32]),GILT:material([.94,.68,.24],.35,.48),
    MOUNT:material([.13,.078,.03],.52,.33),BRASS:material([.72,.54,.25],.45,.47),SHOP:material([.267,.13,.100]),SHOP_DARK:material([.169,.138,.112],.56,.22),
    SHOP_GLASS:material([.347,.279,.179],.35,.15),
}

def arch(u,width,bottom,top,lod):
    r=width/2
    angles=np.linspace(0,pi,16 if lod else 32)
    return Polygon([(u-r,bottom),(u+r,bottom),*((u+r*cos(t),top-r+r*sin(t))for t in angles)])

def ring(face,outline,width,back,front,mat,name):
    face.prism(outline.buffer(width,join_style='mitre').difference(outline),back,front,mat,name)

def glass(face,hole,cols,rows,lod,shop=False,arched=False):
    x0,z0,x1,z1=hole.bounds
    collar=.065 if shop else .049
    frames=[hole.difference(hole.buffer(-collar,join_style='mitre'))]
    for k in range(1,cols):
        u=x0+(x1-x0)*k/cols
        frames.append(box(u-.024,z0,u+.024,z1).intersection(hole))
    for z in rows:
        frames.append(box(x0,z-.026,x1,z+.026).intersection(hole))
    if arched and shop:
        u=(x0+x1)/2;zc=z1-(x1-x0)/2;r=(x1-x0)/2
        for ang in (pi/4,3*pi/4):
            frames.append(LineString([(u,zc),(u+.98*r*cos(ang),zc+.98*r*sin(ang))]).buffer(.019).intersection(hole))
    face.prism(hole,-.253,-.232,SHOP_GLASS if shop else GLASS,'Recessed glazing')
    face.prism(unary_union(frames),-.212,-.141,SHOP_DARK if shop else SASH,'Sash and transoms')
    return hole

def horizontal(face,width,u,height,depth,thickness,mat,label):
    face.box(u,height,width,thickness,depth,depth*.38,mat,label)

def twisted(face,u,bottom,top,r,lod):
    # Two continuous shallow strands wrap the engaged stone shaft.
    center_depth=-r*.32
    edge=lambda z,a:face.point(u+r*cos(a),z,center_depth+r*sin(a))
    face.builder.tube([edge(bottom,0)-face.t*r,edge(top,0)-face.t*r],r*.89,PALE,8 if lod else 12,face.label+'/Stone shaft')
    course=max(4,int((top-bottom)/(.45 if r>.15 else .24)))
    for j in range(2):
        pts=[]
        for n in range(course*(5 if lod else 9)+1):
            f=n/(course*(5 if lod else 9));a=2*pi*course*f+j*pi
            pts.append(edge(bottom+(top-bottom)*f,a))
        face.builder.tube(pts,r*.15,STONE,4 if lod else 5,face.label+'/Spiral stone flutes')
    for z in (bottom+.07,top-.07):
        face.box(u,z,r*2.52,.14,r*1.52,r*.30,PALE,'Shaft base and abacus')

def leaves(face,u,z,size,lod):
    # Paired scrolls and an oval cartouche rise above the lower paired windows.
    angles=np.linspace(0,2*pi,12 if lod else 20)
    outer=Polygon([(u+.28*size*cos(a),z+.35*size*sin(a))for a in angles[:-1]])
    face.prism(outer,.025,.108,PALE,'Oval cartouche')
    ring(face,outer,.045*size,.051,.18,STONE,'Cartouche rim')
    for side in (-1,1):
        for direction in (-1,1):
            pts=[]
            for t in np.linspace(0,1,7 if lod else 12):
                angle=side*direction*t*1.8*pi;r=size*(.18-.13*t)
                pts.append(face.point(u+side*(.60-.14*t)*size+r*cos(angle),z+direction*.14*size+r*sin(angle),.14))
            face.builder.tube(pts,.039*size,PALE,4 if lod else 6,face.label+'/Cartouche scrolls')

def relief_band(face,u,z0,z1,width,lod):
    face.box(u,(z0+z1)/2,width+.16,z1-z0+.10,.12,.045,PALE,'Pale stripe shoulders')
    face.box(u,(z0+z1)/2,width,z1-z0,.13,.101,DARK_GREEN,'Green relief field')
    step=.50;count=round((z1-z0)/step)
    for j in range(count):
        z=z0+(z1-z0)*(j+.5)/count
        for side in (-1,1):
            points=[face.point(u+side*width*(.34*cos(t)),z+.21*sin(t),.183)for t in np.linspace(-pi/2,pi/2,5 if lod else 9)]
            face.builder.tube(points,.025,GREEN,4 if lod else 5,face.label+'/Interlaced glazed tile')
        if not lod:
            face.line((u-.09,z-.08,.182),(u+.09,z+.08,.182),.020,GREEN,4,'Small glazed tile lozenges')

def triple_window(face,u,lod):
    cuts=[]
    mid=arch(u,1.39,TOP_SILL,13.96,lod)
    cuts.append(glass(face,mid,2,[13.25],lod,arched=True))
    ring(face,mid,.108,.012,.12,PALE,'Round central window arch')
    for s in (-1,1):
        x=u+s*1.12;side=box(x-.35,TOP_SILL,x+.35,13.34)
        cuts.append(glass(face,side,1,[],lod));horizontal(face,.86,x,13.37,.25,.11,PALE,'Companion square lintels')
        twisted(face,u+s*.76,TOP_SILL,13.27,.095,lod)
    horizontal(face,3.34,u,TOP_SILL-.065,.23,.132,STONE,'Triplet window sill')
    return cuts

def principal(face,lod):
    x=CENTRE;holes=[]
    for off in (-1.32,0,1.32):
        u=x+off;h=box(u-.53,6.59,u+.53,10.53);holes.append(glass(face,h,1,[9.96],lod))
    upper=arch(x,3.96,12.20,15.42,lod);holes.append(glass(face,upper,2,[13.45],lod,arched=True))
    panel=box(x-2.59,6.50,x+2.59,15.79)
    face.prism(panel.difference(unary_union(holes)),.005,.096,STONE,'Carved portal panel and mullions')
    ring(face,upper,.18,.035,.173,PALE,'Pale semicircular archivolt')
    dark_arch=upper.buffer(-.03).difference(upper.buffer(-.20))
    face.prism(dark_arch,-.135,-.062,DARK_GREEN,'Recessed dark arch band')
    for k in range(21 if not lod else 13):
        t=pi*(k+.5)/(21 if not lod else 13);u=x+2.15*cos(t);z=13.44+2.15*sin(t)
        face.box(u,z,.095,.079,.071,.182,PALE,'Archivolt leaf bosses')
    for off in (-2.45,2.45):
        twisted(face,x+off,6.57,13.43,.095,lod)
    for z,depth,thick in ((10.56,.21,.17),(11.78,.25,.19),(12.64,.25,.12)):
        horizontal(face,4.27,x,z,depth,thick,PALE,'Portal balustrade and ledge')
    for u in np.linspace(x-1.91,x+1.91,13 if lod else 17):
        for z,rad in ((11.97,.069),(12.12,.091),(12.32,.062),(12.48,.094)):
            face.builder.tube([face.point(u,z-.095,.139),face.point(u,z+.095,.139)],rad,PALE,6 if lod else 8,face.label+'/Turned gallery balusters')
    leaves(face,x,15.51,.52,lod)
    return holes

def hotel_door(face,u,width,height,lod):
    hole=arch(u,width,.13,height,lod)
    glass(face,hole,2,[height-width/2,1.02],lod,shop=True,arched=True)
    ring(face,hole,.095,.003,.15,SHOP_DARK,'Rounded entrance reveal')
    for sign in (-1,1):
        face.line((u+sign*.09,.88,-.114),(u+sign*.09,1.59,-.114),.023,BRASS,6,'Door pulls')
    return hole

def street_level(face,front,lod):
    L=LENGTH if front else CHAMFER;holes=[]
    if front:
        for a,b in ((.37,3.40),(3.66,6.61),(7.13,9.78),(10.03,12.66)):
            opening=box(a,.17,b,3.65);holes.append(glass(face,opening,2,[2.85],lod,shop=True))
        for a,b in ((.12,6.82),(6.94,13.03)):
            face.box((a+b)/2,4.36,b-a,.97,.27,.05,SHOP_DARK,'Current retail fascia')
        x=17.22
        for pos in (14.61,19.73):
            h=arch(pos,.70,.17,3.46,lod);holes.append(glass(face,h,1,[2.03,2.95],lod,shop=True,arched=True))
        holes.append(hotel_door(face,x,2.60,4.52,lod))
        face.box(x,4.84,3.82,.16,.90,.29,SHOP_DARK,'Canopy above hotel entrance')
    else:
        holes.append(hotel_door(face,CHAMFER/2,2.54,4.28,lod))
    face.prism(box(0,.025,L,6.18).difference(unary_union(holes)),-.52,-.006,SHOP if not front else SHOP_DARK,'Enclosed street wall')
    if front:
        face.prism(box(13.21,.035,L,6.10).difference(unary_union(holes)),-.004,.015,SHOP,'Burgundy hotel entrance wall')
    return holes

def mouldings(face,length,lod):
    x=length/2
    for z,h,d,mat in [(5.97,.12,.27,SHADOW),(6.11,.23,.36,STONE),(6.37,.42,.42,PALE),(6.64,.105,.25,STONE),
                      (16.04,.18,.24,STONE),(16.23,.15,.36,PALE),(16.57,.19,.51,SHADOW),(16.85,.23,.61,STONE),(17.12,.19,.66,PALE),
                      (17.34,.18,.62,STONE)]:
        horizontal(face,length+.10,x,z,d,h,mat,'Continuous street mouldings')
    for n in range(max(2,round(length/.49))):
        u=length*(n+.5)/round(length/.49)
        face.box(u,16.40,.20,.15,.33,.17,PALE,'Cornice dentils')
    pitch=.77
    for j in range(round(length/pitch)):
        center=(j+.5)*length/round(length/pitch)
        pts=[]
        for t in np.linspace(-pi*.30,pi*1.66,9 if lod else 15):
            f=(t+pi*.30)/(pi*1.96);r=.17-.092*f
            pts.append(face.point(center+r*cos(t)+.10*(f-.5),6.37+r*sin(t),.371))
        face.builder.tube(pts,.026,SHADOW,4 if lod else 6,face.label+'/Wave frieze scrolls')

def decorate_text(face,text,u,z,w,h,lod,name,depth,material):
    for _,g in lettering_shapes(text,w,h,font=FONT):
        zshape=set_precision(translate(g.simplify(.0019 if lod else .0009),xoff=u,yoff=z),.0002)
        if material == GILT:
            # Exposed dark bronze edges are visible below the raised gilded strokes.
            face.prism(zshape.buffer(.028,quad_segs=2),.004,depth+.012,MOUNT,name+' returns')
        face.prism(zshape,depth,depth+.088,material,name)

def attic(face,length,lod,front):
    setback=.59;holes=[]
    if front:
        for u in (3.65,CENTRE,17.12):
            # The high strip shows three grouped flat-headed windows in the oblique street photograph.
            outline=box(u-1.36,19.13,u+1.36,21.40)
            face.prism(outline,-setback-.20,-setback-.12,GLASS,'Attic grouped glazing')
            frame=outline.difference(outline.buffer(-.09))
            bars=[frame]+[box(u+off-.04,19.15,u+off+.04,21.38)for off in (-.46,.46)]
            face.prism(unary_union(bars),-setback-.11,-setback-.02,SASH,'Attic window frames');holes.append(outline)
    face.prism(box(.04,17.01,length-.04,23.23).difference(unary_union(holes)),-1.08,-setback,BRICK if front else BUFF,'Setback attic wall')
    for z,h,d in [(23.18,.16,.50),(23.39,.22,.62),(23.54,.09,.71)]:
        face.box(length*.5,z,length+.04,h,d,-setback-.12,STONE,'Attic coping and drip edge')

def add_building(builder,lod=False):
    road=Facade(builder,(-1.,0),(1.,0),'Ningbo')
    dx,dy=(END[0]-LENGTH)/CHAMFER,END[1]/CHAMFER
    turn=Facade(builder,(LENGTH-dx,-dy),(LENGTH+dx,dy),'Chamfer')
    for face,length,front in ((road,LENGTH,True),(turn,CHAMFER,False)):
        street_level(face,front,lod);openings=[]
        if front:
            openings+=principal(face,lod)
            for u in (3.76,17.05):
                for off in (-.87,.87):
                    opening=box(u+off-.58,SIDE_SILL,u+off+.58,SIDE_HEAD);openings.append(glass(face,opening,1,[SIDE_HEAD-.70],lod))
                    ring(face,opening,.118,.004,.07,RED,'Rectangular brick jambs')
                leaves(face,u,10.57,.91,lod);openings.extend(triple_window(face,u,lod))
            for u in (1.05,7.02,13.78,19.83):relief_band(face,u,6.66,15.93,.48,lod)
            for u in (.28,7.48,13.32,20.53):twisted(face,u,6.66,15.95,.146,lod)
            for u in (0.70,7.42,13.42,20.11):face.box(u,11.28,.14,9.27,.082,.022,RED,'Continuous red edging')
            decorate_text(face,'亚朵酒店',17.22,6.08,2.68,.41,lod,'Hotel lettering',.398,SASH)
        else:
            for u in (.23,length-.23):twisted(face,u,6.64,15.95,.14,lod)
            for i,ch in enumerate('新光影艺苑'):
                size=1.78 if i<2 else 1.07
                decorate_text(face,ch,length*.5,14.83-i*1.72,size,size*.91,lod,'Chamfer cinema lettering',.115,GILT)
        face.prism(box(0,6.16,length,16.14).difference(unary_union(openings)),-.52,0.,BRICK,'Two colour patterned street masonry')
        mouldings(face,length,lod);attic(face,length,lod,front)
    for part in builder.parts:
        if part['material']==BRICK:
            part['texcoords']=[(u,1-v)for u,v in (brick_uv(part['label'],p)for p in part['vertices'])]
