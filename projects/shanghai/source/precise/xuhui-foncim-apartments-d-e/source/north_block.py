"""Foncim D. The street facade faces negative Y. The rear loggias face the courtyard."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from striped_render import MATERIAL, apply_to_parts

SOURCE = Path(__file__).resolve().parent
WALL = MATERIAL
BUFF = 'D buff cement'
LIP = 'D old gold edging'
RED = 'D dark red entrance render'
RECESS = 'D umber reveals'
STEEL = 'D restored light steel casements'
GLASS = 'D desaturated window glass'
SHADE = 'D shaded glazing'
IRON = 'D dark terrace rail'
COVER = 'D dark grey flat roof'
PAVE = 'D fine terrazzo'
PIPE = 'D iron drainpipe'
LOUVRE = 'D ochre louvres'

def pigment(rgb, roughness=.82, metallic=0):
    c = np.asarray(rgb, dtype=float)/255
    return dict(color=np.where(c <= .04045, c/12.92, ((c+.055)/1.055)**2.4).tolist(),
                roughness=roughness, metallic=metallic)

NORTH_PALETTE = {
    BUFF:pigment((208,163,124)), LIP:pigment((174,129,94)), RED:pigment((102,66,58)),
    RECESS:pigment((79,61,53)), STEEL:pigment((161,164,157),.48,.28),
    GLASS:pigment((99,121,136),.28,.22), SHADE:pigment((57,70,73),.34,.18),
    IRON:pigment((69,62,54),.52,.38), COVER:pigment((77,76,72),.94),
    PAVE:pigment((145,133,122)), LOUVRE:pigment((150,108,78)), PIPE:pigment((77,64,56),.62,.26),
}
PLAN = json.loads((SOURCE.parent/'measurements/d-north-plan.json').read_bytes())
HALF = PLAN['length_m']/2
GROUND = PLAN['ground_head_m']
PITCH = PLAN['upper_storey_m']
SILL = GROUND+.79
REAR = 12.72

def facade(b, a, c, label):
    return Facade(b, a, c, 'D '+label)

def sash(f, x, z, width, height, columns, lod, tag, material=GLASS):
    """Steel jambs, transom and vertical meeting stiles share one welded mesh."""
    aperture = box(x-width/2,z,x+width/2,z+height)
    f.prism(aperture.buffer(.015,join_style=2),-.163,-.145,material,tag+' glazing')
    inside = aperture.buffer(-.056,join_style=2)
    bars = [box(x-width/2,z+height*.735-.022,x+width/2,z+height*.735+.022)]
    for k in range(1,columns):
        u = x-width/2+k*width/columns
        bars.append(box(u-.021,z,u+.021,z+height))
    if not lod and width > 1.1:
        bars.append(box(x-width/2,z+.065,x+width/2,z+.083))
    f.prism(aperture.difference(inside.difference(unary_union(bars))),-.113,-.066,STEEL,tag+' steelwork')
    f.box(x,z-.043,width+.095,.076,.148,.008,BUFF,tag+' sill')
    return aperture

def threshold(f, x, width, z, glass, lod):
    """A photographed public entrance is given a short recessed floor and lintel."""
    depth = .92
    f.box(x,.095,width+.22,.19,depth,-depth/2,PAVE,'entrance paving')
    for hand in (-1,1):
        f.box(x+hand*(width/2+.04),z/2,.09,z,depth,-depth/2,RECESS,'entrance reveals')
    f.box(x,z-.045,width+.14,.09,depth,-depth/2,RECESS,'entrance soffit')
    f.box(x,z/2,width,z-.05,.06,-depth,glass,'recessed entrance')
    f.box(x,z*.50,.046,z-.08,.08,-depth+.05,IRON,'door meeting stile')
    f.box(x,z*.76,width,.052,.08,-depth+.05,IRON,'door transom')
    return box(x-width/2,0,x+width/2,z)

def add_screen(f, x, z, w, lod):
    f.box(x,z,w,.54,.25,.12,RECESS,'screen backing')
    for hand in (-1,1):
        f.box(x+hand*(w/2-.021),z,.042,.55,.30,.14,LOUVRE,'screen uprights')
    levels=5 if lod else 9
    for h in np.linspace(-.244,.244,levels):
        f.box(x,z+h,w,.029 if not lod else .047,.047,.285,LOUVRE,'screen louvers')


def roof_terraces(b,zones,lod):
    deck=GROUND+3*PITCH
    lower=unary_union([box(a,y,c,z)for _,a,c,y,z,_ in zones])
    pieces=[]
    for a,c,setback in PLAN['estimated_court_setbacks_m']:
        name,left,right,front,back,roof=next(row for row in zones if row[1]<(a+c)/2<row[2])
        fb=back-setback
        shape=box(a,front,c,fb)
        pieces.append((a,c,front,fb,roof,shape))
        rear=facade(b,(c,fb),(a,fb),'top terrace')
        w=c-a;holes=[]
        if w>3.0:
            holes.append(sash(rear,0,deck+.16,min(2.16,w*.31),2.35,2,lod,'terrace doors',SHADE))
        if w>6.0:
            for side in (-1,1):
                holes.append(sash(rear,side*w*.341,deck+.76,1.18,1.60,2,lod,'top apartment'))
        rear.wall(deck,roof,holes,.23,WALL)
        rear.beam(roof-.055,.13,.31,BUFF,label='terrace eaves')
        b.plan_prism(shape,roof-.13,roof,COVER,'D top roof deck')
    for i,(a,c,front,back,roof,shape) in enumerate(pieces):
        for x,j in [(a,i-1),(c,i+1)]:
            if 0<=j<len(pieces):
                other=pieces[j];y0=other[3]
                if y0>=back-.006:continue
            else:y0=front
            if back-y0>.09:
                b.box((x,(y0+back)/2,(deck+roof)/2),(.19,back-y0,roof-deck),WALL,
                      label='D upper apartment return walls')
    upper=unary_union([r[5]for r in pieces])
    # The western end and the courtyard cutbacks share an open terrace with a low solid guard.
    rim=lower.buffer(.055,join_style=2).difference(lower.buffer(-.13,join_style=2))
    rim=rim.difference(upper.buffer(.20,join_style=2))
    b.plan_prism(rim,deck,deck+.76,BUFF,'D outer terrace parapet')
    b.plan_prism(rim.buffer(.028,join_style=2),deck+.76,deck+.82,LIP,'D terrace coping')
    for lower_z in {row[4]for row in pieces}:
        shell=unary_union([r[5]for r in pieces if r[4]==lower_z])
        curb=shell.difference(shell.buffer(-.14,join_style=2))
        b.plan_prism(curb,lower_z-.005,lower_z+.24,BUFF,'D upper roof parapets')


def street_field(b, index, left, right, y, low, roof, lod):
    f = facade(b, (left,y),(right,y),'street '+index)
    centre=(left+right)/2
    upper=[]
    for i in range(4):
        z=SILL+i*PITCH
        for x,width,lights in PLAN['street_window_centres_width_lights']:
            if i==3 and x>24.60:continue
            if left+.01 < x-width/2 and x+width/2 < right-.01:
                if index=='centre' and 2.4<abs(x)<4.1:
                    door=sash(f,x-centre,z-.71,1.60,2.34,2,lod,'balcony door',SHADE)
                    upper.append(door)
                    continue
                upper.append(sash(f,x-centre,z,width,1.56,lights,lod,'dwelling'))
    upper_shape=box(-f.length/2,low,f.length/2,roof)
    if index=='west':
        upper_shape=upper_shape.difference(box(24.60-centre,GROUND+3*PITCH,f.length/2+.1,roof+.1))
    f.wall(low,roof,upper,.24,WALL,upper_shape)
    holes=[]
    for x,width,kind in PLAN['ground_openings']:
        if left+.01 < x-width/2 and x+width/2 < right-.01:
            u=x-centre
            if kind=='entrance':
                holes.append(threshold(f,u,width,2.54,SHADE,lod))
            else:
                holes.append(sash(f,u,.54,width,2.04,3,lod,'shopfront',SHADE))
    f.wall(.045,low,holes,.28,RED)
    f.beam(low-.11,.16,.18,BUFF,label='ground fascia')
    cap_right=24.60 if index=='west' else right
    u=(left+cap_right)/2-centre
    f.box(u,roof-.055,cap_right-left+.035,.15,.64,.095,BUFF,'projecting eaves')
    f.box(u,roof+.07,cap_right-left+.06,.09,.68,.105,LIP,'upper coping')
    # Horizontal screens below selected windows are visible after the 2020 works.
    for x,i in PLAN['louvres_after_repair']:
        if left+.01<x-.55 and x+.55<right-.01 and not(i==3 and x>24.6):
            add_screen(f,x-centre,SILL+i*PITCH-.45,.99,lod)

def stair_tower(b, x, y, roof, lod, ident):
    """Three separated piers flank narrow glazed stair lights in the street towers."""
    width=3.13;front=y-.96;f=facade(b,(x-width/2,front),(x+width/2,front),'stair '+ident)
    height=roof+1.07
    holes=[threshold(f,0,1.38,2.52,SHADE,lod)]
    for side in (-1,1):
        for i in range(4):
            holes.append(sash(f,side*.575,GROUND-.20+i*PITCH,.40,PITCH-.31,1,lod,'stair light',SHADE))
    f.wall(.06,height,holes,.23,BUFF)
    for u,w,h in [(-1.18,.52,.18),(0,.42,.64),(1.18,.52,.18)]:
        bottom=2.59 if u==0 else .06
        pier_height=height+h-bottom
        f.box(u,bottom+pier_height/2,w,pier_height,.26,.10,BUFF,'vertical pier')
        if not lod:f.box(u-.095,bottom+pier_height/2,.048,pier_height-.13,.055,.255,LIP,'narrow pier edge')
    for hand in (-1,1):
        b.box((x+hand*(width/2-.08),(front+y)/2,height/2),(.16,y-front+.1,height),
              BUFF,label='D stair '+ident+' returns')
    b.box((x,(front+y)/2,height),(width+.05,y-front+.14,.13),LIP,label='D stair '+ident+' roof')

def central_balconies(b,lod):
    # Plan 9 shows an extended centre with splayed shoulders terminating in a short flat nose.
    front=-1.52
    edge=[(-5.24,front),(-5.24,-2.11),(-2.9796,-3.91),(2.9796,-3.91),(5.24,-2.11),(5.24,front)]
    shape=Polygon(edge)
    for i in range(5):
        z=GROUND+i*PITCH
        name='D splayed '+str(i+1)
        b.plan_prism(shape.buffer(.085,join_style=2),z-.22,z,BUFF,name+' balcony slab')
        b.plan_prism(shape.buffer(.105,join_style=2).difference(shape.buffer(.055,join_style=2)),z-.17,z-.08,LIP,name+' rim')
        if i==4:continue
        for j,(a,c) in enumerate(zip(edge[:-1],edge[1:])):
            ff=facade(b,a,c,'balcony '+str(i+1))
            ff.box(0,z+.22,ff.length,.44,.14,.013,BUFF,'solid base')
            for dz,th in ((.19,.038),(.37,.035)):
                ff.box(0,z+dz,ff.length+.015,th,.19,0,LIP,'horizontal moulding')
            sides=6 if lod else 10
            for h in (.64,.83,.99):
                b.tube([ff.point(-ff.length/2,z+h),ff.point(ff.length/2,z+h)],.024,
                       IRON,sides,name+' guardrails')
            for u in np.linspace(-ff.length/2,ff.length/2,max(2,round(ff.length/1.34)+1)):
                b.tube([ff.point(u,z+.40),ff.point(u,z+1)],.024,IRON,sides,name+' balusters')
        for hand in (-1,1):
            b.lathe((hand*3.51,-2.68),[(z,.27),(z+.11,.29),(z+.17,.245),
                    (z+PITCH-.37,.245),(z+PITCH-.24,.30),(z+PITCH-.20,.30)],
                    BUFF,12 if lod else 24,name+' concrete columns')
    for hand in (-1,1):
        b.lathe((hand*2.58,-2.25),[(.03,.38),(.14,.40),(.23,.34),
                (GROUND-.49,.34),(GROUND-.30,.43),(GROUND-.22,.43)],
                BUFF,16 if not lod else 10,'D north ground round columns')

def court_field(b,left,right,y,roof,lod,ident):
    # Each garden elevation is read facing north. Its four main French windows/light groups
    # are separately set into the wall behind the returned balcony front.
    f=facade(b,(right,y),(left,y),'court '+ident)
    mid=(left+right)/2;width=right-left
    holes=[]
    for i in range(3):
        z=SILL+i*PITCH
        for frac,w in ((-.356,1.16),(-.195,.77),(0,3.08),(.198,.78),(.351,1.18)):
            holes.append(sash(f,frac*width,z,w,1.56,max(2,round(w/.70)),lod,'court rooms'))
    deck=GROUND+3*PITCH
    f.wall(GROUND,deck,holes,.24,WALL)
    doors=[threshold(f,0,2.14,2.60,SHADE,lod)]
    for hand in (-1,1):
        doors.append(sash(f,hand*width*.34,.64,2.25,1.78,3,lod,'yard service',SHADE))
    f.wall(.045,GROUND,doors,.27,RED)
    f.beam(deck-.045,.15,.32,BUFF,label='garden terrace deck')
    # The open terraces project at all three units. Two shades of stucco reflect the
    # pronounced layered coping on the garden photographs.
    for i in range(4):
        z=GROUND+i*PITCH
        w=4.76 if ident=='centre' else 4.12
        for hand in (-1,1):
            x=mid+hand*width*.193
            depth=1.05 if ident=='centre' else .87
            outer=box(x-w/2,y-.08,x+w/2,y+depth)
            b.plan_prism(outer,z-.16,z,BUFF,'D court '+ident+' balcony floor')
            if i==3 and ident!='centre':continue
            rail=outer.difference(box(x-w/2+.10,y-.14,x+w/2-.10,y+depth-.115))
            b.plan_prism(rail,z,z+.62,BUFF,'D court '+ident+' parapet')
            for h in (.16,.35,.51):
                b.box((x,y+depth+.018,z+h),(w+.022,.073,.048),LIP,label='D court '+ident+' parapet bands')
            for end in (-1,1):
                b.tube([(x+end*(w/2-.085),y+depth-.056,z+.60),
                        (x+end*(w/2-.085),y+depth-.056,z+.91)],.023,IRON,6,'D court posts')
            b.tube([(x-w/2,y+depth-.054,z+.91),(x+w/2,y+depth-.054,z+.91)],.024,IRON,6,'D court top rail')

def end_wall(b, x, y0, y1, height, lod, side, low=.06):
    a,c=((x,y1),(x,y0)) if x<0 else ((x,y0),(x,y1))
    f=facade(b,a,c,'end '+side);holes=[]
    for i in range(4):
        for frac in (-.28,.16):
            if low<SILL+i*PITCH and SILL+i*PITCH+1.5<height:
                holes.append(sash(f,f.length*frac,SILL+i*PITCH,1.09,1.50,2,lod,'end room'))
    f.wall(low,height,holes,.23,WALL)
    f.beam(height-.06,.15,.33,BUFF,label='end coping')

def build_north(b,lod):
    start=len(b.parts);third=13.22
    zones=[('east',-HALF,-third,0.,REAR,GROUND+PITCH*4-.42),
           ('centre',-third,third,-1.52,REAR-1.15,GROUND+PITCH*4+.12),
           ('west',third,HALF,0.,REAR,GROUND+PITCH*4-.42)]
    for name,left,right,front,back,roof in zones:
        street_field(b,name,left,right,front,GROUND,roof,lod)
        court_field(b,left,right,back,roof,lod,name)
        footprint=box(left,front,right,back)
        b.plan_prism(footprint,.015,.12,PAVE,'D '+name+' ground slab')
        deck=GROUND+3*PITCH
        b.plan_prism(footprint,deck-.15,deck,PAVE,'D '+name+' open top terrace')
        for j in range(1,4):
            z=GROUND+(j-1)*PITCH
            b.plan_prism(footprint.buffer(-.073,join_style=2),z-.15,z,BUFF,'D '+name+' floor slabs')
        # Concrete returns close the changes in plan on both the street and court elevations.
    for hand in (-1,1):
        x=hand*third
        for lo,hi,H in ((-1.52,0,zones[1][-1]),(REAR-1.15,REAR,zones[0][-1])):
            b.box((x,(lo+hi)/2,H/2),(.19,hi-lo,H),WALL,label='D stepped return')
        b.box((x,(REAR-1.15)/2,(zones[1][-1]+zones[0][-1])/2),
              (.17,REAR-1.15,zones[1][-1]-zones[0][-1]),BUFF,label='D raised centre roof upstand')
        end_wall(b,hand*HALF,0,REAR,GROUND+3*PITCH,lod,'east' if hand<0 else 'west')
    roof_terraces(b,zones,lod)
    for name,x,y,height in [('east',-22.20,0,zones[0][-1]),('west',22.36,0,zones[2][-1]),
                             ('centre',0,-1.52,zones[1][-1])]:
        stair_tower(b,x,y,height,lod,name)
    central_balconies(b,lod)
    for x,y in [(-third+.24,REAR-1.15),(third-.24,REAR-1.15),(-5.40,-1.52),(5.40,-1.52)]:
        b.tube([(x,y,.18),(x,y,GROUND+.26),(x+.08,y,GROUND+.53),(x+.08,y,GROUND+PITCH*4-.2)],.077,
               PIPE,8 if lod else 14,'D iron drainpipes')
    apply_to_parts(b.parts[start:],PITCH,SILL)
