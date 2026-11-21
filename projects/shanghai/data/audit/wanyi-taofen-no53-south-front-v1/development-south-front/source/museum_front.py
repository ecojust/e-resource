"""Model the numbered western frontage of the Wanyi Fang museum, as published July 2026."""
from pathlib import Path
import json
import math
from random import Random
from shapely import affinity
from shapely.geometry import Point, Polygon, box
from photo_architecture import Facade
from sign_lettering import lettering_shapes

HERE = Path(__file__).resolve().parent
PLASTER = 'Yellow-grey pebble dash'
GRAIN = 'Pale aggregate highlights'
EDGE = 'Quiet cream cornice'
BASE = 'Brown red stone plinth'
DARK = 'Soot black gate iron'
HINGE = 'Satin wrought metal'
GOLD = 'Gilt museum lettering'
GREEN = 'Old dark green window paint'
ADDRESS = 'Green numbered enamel'
GLASS = 'Green reflected window glass'
INNER = 'Shaded window backing'
TIMBER = 'Warm wood door'
PAVE = 'Light court pavement'
TILE = 'Oxide brown interlocking clay'
TILE_DARK = 'Dark clay laps'
GUTTER = 'Dark painted rainwater iron'
CANOPY = 'Pale painted canopy frame'
CLEAR = 'Translucent canopy glazing'
PALETTE = {material: {'color':color, 'roughness':roughness} for material,color,roughness in [
    (PLASTER,[.57,.53,.39],.95),(GRAIN,[.65,.61,.48],.94),(EDGE,[.77,.755,.66],.85),
    (BASE,[.29,.146,.107],.85),(DARK,[.048,.047,.041],.76),(HINGE,[.105,.109,.098],.64),
    (GOLD,[.69,.44,.13],.45),(GREEN,[.135,.206,.157],.69),(ADDRESS,[.12,.36,.235],.57),
    (GLASS,[.19,.26,.265],.43),(INNER,[.087,.093,.080],.96),(TIMBER,[.33,.21,.135],.82),
    (PAVE,[.53,.53,.475],.94),(TILE,[.43,.225,.162],.92),(TILE_DARK,[.317,.159,.119],.94),
    (GUTTER,[.11,.095,.084],.74),(CANOPY,[.67,.70,.67],.58),(CLEAR,[.65,.76,.74],.36)]}
PALETTE[CLEAR]['alpha']=.24

def shape_rect(center, bottom, width, height):
    return box(center-width/2,bottom,center+width/2,bottom+height)


def grit(face, surface, seed, lod, offset=0):
    rng=Random(seed)
    vertices=[]; facets=[]
    x0,z0,x1,z1=surface.bounds
    for _ in range(round(surface.area*(5 if lod else 130))):
        x,z=rng.uniform(x0,x1),rng.uniform(z0,z1)
        if not surface.contains(Point(x,z)):continue
        a=rng.uniform(.009,.023);b=rng.uniform(.009,.026);i=len(vertices)
        vertices.extend([face.point(x-a,z,offset+.001),face.point(x-.1*a,z-b,offset+.002),
                         face.point(x+a,z+.36*b,offset+.001),face.point(x,z+.28*b,offset+rng.uniform(.005,.011))])
        facets.extend([(i,i+1,i+3),(i+1,i+2,i+3)])
    if vertices:face.builder.add(vertices,facets,GRAIN,face.label+'/Cast aggregate')


def moulding(face, rect, depth, face_depth, thick, material, label):
    face.prism(rect.difference(rect.buffer(-thick,join_style=2)),depth,face_depth,material,label)


def label_text(face, text, x, z, width, height, depth, material, lod):
    for index,(ch,geom) in enumerate(lettering_shapes(text,width,height,font=HERE/'fonts/WanyiMuseum.otf')):
        form=geom.simplify(.006 if lod else .002,preserve_topology=True)
        face.prism(affinity.translate(form,xoff=x,yoff=z),depth,depth+.015,material,'Letter '+ch+' '+str(index+1))


def shallow_glazing(face,center,bottom,width,height,columns,rows,label):
    aperture=shape_rect(center,bottom,width,height)
    face.prism(aperture,-.275,-.244,INNER,label+' shadow')
    face.prism(aperture.buffer(-.030,join_style=2),-.205,-.189,GLASS,label+' glass')
    moulding(face,aperture,-.185,-.078,.046,GREEN,label+' sash')
    for n in range(1,columns):
        face.box(center-width/2+width*n/columns,bottom+height/2,.032,height-.075,.085,-.125,GREEN,label+' mullions')
    for n in range(1,rows):
        face.box(center,bottom+height*n/rows,width-.071,.027,.084,-.125,GREEN,label+' rails')
    return aperture


def casement(builder, x, y, z, width, height, angle, label, rows=2):
    """Open leaf, glazed in its own actual oblique plane."""
    stop=(x+width*math.cos(angle),y+width*math.sin(angle))
    f=Facade(builder,(x,y),stop,label)
    aperture=shape_rect(0,z,f.length,height)
    f.prism(aperture,-.018,.004,GLASS,'inset glass')
    moulding(f,aperture,-.03,.04,.047,GREEN,'leaf frame')
    for k in range(1,rows):
        f.box(0,z+height*k/rows,f.length,.029,.059,.016,GREEN,'cross rails')


def south_house(builder,width,lod):
    face=Facade(builder,(-width/2,0),(width/2,0),'53 house')
    # All horizontal distances are fractions of the photographed western bay.
    lower=[(-.30,.119),(-.007,.365),(.325,.113)]
    holes=[]
    for i,(relative,span)in enumerate(lower):
        x=relative*width;ww=span*width
        holes.append(shape_rect(x,2.65,ww,.37))
        shallow_glazing(face,x,2.65,ww,.37,2 if i==1 else 1,1,'Lower transom '+str(i+1))
        if i!=1:
            holes.append(shape_rect(x,.52,ww,1.99))
            shallow_glazing(face,x,.52,ww,1.99,1,2,'Ground side window '+str(i+1))
    door_w=.365*width;door_x=-.007*width
    door=shape_rect(door_x,.16,door_w,2.35);holes.append(door)
    face.prism(door,-.32,-.285,INNER,'Ground door shadow')
    face.prism(door.buffer(-.047,join_style=2),-.265,-.205,TIMBER,'Timber door')
    moulding(face,door,-.185,-.052,.07,TIMBER,'Door reveal frame')
    # Dragon's dated open-gate photograph shows two low rounded steps below the inner door.
    for label, radius_x, radius_y, bottom, top in (
        ('Lower rounded threshold', door_w*.65, .57, .018, .087),
        ('Upper rounded threshold', door_w*.54, .38, .087, .16),
    ):
        step = affinity.scale(Point(0,0).buffer(1,resolution=18 if not lod else 9),xfact=radius_x,yfact=radius_y)
        front_half = step.intersection(box(-radius_x,-radius_y,radius_x,0.))
        builder.prism(affinity.translate(front_half,xoff=door_x),bottom,top,lambda x,y,z:(x,y,z),PAVE,'53 house/'+label)
    face.box(door_x,1.30,.051,2.17,.036,-.175,TIMBER,'Door meeting stile')
    for k in (-1,1):
        opening=shape_rect(door_x+k*.21*door_w,1.06,.36*door_w,1.25)
        face.prism(opening,-.200,-.174,GLASS,'Door upper glazing')
        moulding(face,opening.buffer(.028,join_style=2),-.182,-.14,.037,TIMBER,'Door glazing bead')
    upper_x=-.005*width;upper_w=.639*width; sill=4.15; head=5.80
    holes.append(shape_rect(upper_x,sill,upper_w,head-sill))
    shallow_glazing(face,upper_x,sill,upper_w,head-sill,4,1,'Second floor window')
    face.box(upper_x,head-.28,upper_w,.050,.095,-.106,GREEN,'Upper cross rail')
    casement(builder,upper_x-upper_w*.26,-.125,sill+.05,upper_w*.24,head-sill-.34,-.93,'53 open left sash')
    casement(builder,upper_x+upper_w*.23,-.125,sill+.05,-upper_w*.23,head-sill-.34,.65,'53 open right sash')
    face.box(upper_x,sill-.058,upper_w+.13,.097,.199,.049,EDGE,'Upper projecting sill')
    material=face.wall(0,6.36,holes=holes,thickness=.19,material=PLASTER)
    grit(face,material.buffer(-.045),301,lod)
    face.box(0,3.33,width,.046,.082,-.007,EDGE,'Rendered floor break')
    return face


def forecourt(builder,width,depth,lod):
    face=Facade(builder,(-width/2,-depth),(width/2,-depth),'53 court')
    # The eastern gate pier at no.53 is also the dividing line with no.54.
    west=-.455*width; left_jamb=.190*width; right_jamb=.476*width
    panels=(west+.13,left_jamb-.16)
    wall=box(panels[0],.0,panels[1],2.20)
    face.prism(wall,-.22,.00,PLASTER,'Street wall')
    grit(face,wall.buffer(-.045),995,lod)
    face.box(sum(panels)/2,.125,panels[1]-panels[0],.25,.26,.004,BASE,'Street plinth')
    face.box(sum(panels)/2,2.21,panels[1]-panels[0]+.03,.085,.27,.006,EDGE,'Street coping')
    for i,(x,ww,top) in enumerate([(west,.29,2.47),(left_jamb,.33,2.51),(right_jamb,.34,2.52)]):
        body=shape_rect(x,0,ww,top-.12)
        face.prism(body,-.30,.085,PLASTER,'Pier '+str(i+1))
        grit(face,body.buffer(-.05),500+i,lod,.085)
        face.box(x,.129,ww+.014,.258,.40,-.093,BASE,'Stone feet')
        face.box(x,top-.105,ww+.052,.099,.42,-.090,EDGE,'Pier caps')
        crown=Polygon([(x-ww/2,top-.058),(x-ww/2+.022,top+.036),(x,top+.107),(x+ww/2-.022,top+.036),(x+ww/2,top-.058)])
        face.prism(crown,-.254,.060,EDGE,'Shallow pitched cap')
    a=left_jamb+.168;b=right_jamb-.173; span=b-a; mid=(a+b)/2
    face.box(mid,1.088,span,2.14,.067,-.082,DARK,'Dark iron gate leaf')
    for i in range(1,6):
        face.box(a+span*i/6,1.11,.009,2.02,.012,-.042,HINGE,'Iron vertical joints')
    for z in (.12,.25,2.09):
        face.box(mid,z,span-.03,.036,.028,-.034,HINGE,'Gate horizontal edges')
    panel_mid=(panels[0]+panels[1])/2
    panel_w=(panels[1]-panels[0])*.91
    face.box(panel_mid,1.79,panel_w,.467,.055,.019,EDGE,'Museum lettering ground')
    label_text(face,'韬奋纪念馆',panel_mid,1.79,panel_w*.89,.295,.059,GOLD,lod)
    face.box(left_jamb,1.88,.223,.157,.018,.102,ADDRESS,'Green address plate')
    label_text(face,'53',left_jamb,1.88,.16,.103,.116,EDGE,lod)
    face.box(mid,1.64,span*.50,.292,.022,-.032,GOLD,'Gate notice backing')
    face.box(mid+.013,1.64,span*.34,.253,.017,-.015,EDGE,'Paper on notice')
    floor=box(-width/2,-depth-.11,width/2,.03)
    builder.prism(floor,-.015,.026,lambda x,y,d:(x,y,d),PAVE,'53 court/Paving')
    # Transparent lean-to at the left of the three ground-floor transoms.
    left=-width*.465;right=-width*.17; front=-depth+.28
    verts=[(left,front,2.40),(right,front,2.40),(right,-.13,2.79),(left,-.13,2.79)]
    builder.add(verts,[(0,1,2,3)],CLEAR,'53 awning/Transparent sheet')
    for first,last in ((0,1),(1,2),(2,3),(3,0)):
        builder.tube([verts[first],verts[last]],.028,CANOPY,7,'53 awning/Light frame')
    for x in [left,right]:
        builder.tube([(x,-.23,2.42),(x,front+.24,2.40),(x,-.17,2.73)],.019,CANOPY,7,'53 awning/Braced side')


def roof_and_dormer(builder,width,lod):
    west=-width/2; east=width/2
    eaves=6.36; slope=.72; front=-.28; back=3.31
    def zroof(y):return eaves+(y-front)*slope
    dormer_west=-width*.026; dormer_front=.99
    footprint=Polygon([(west,front),(east,front),(east,dormer_front),(dormer_west,dormer_front),
                       (dormer_west,back),(west,back)])
    builder.prism(footprint,-.13,0,lambda x,y,d:(x,y,zroof(y)+d),TILE_DARK,'53 roof/Clay roof deck')
    # Interlocking short clay units. Rows thicken at the downslope lip, with staggered head joints.
    course=.175 if not lod else .28
    tile_width=.162 if not lod else .263
    verts=[];faces=[]
    for row in range(math.ceil((back-front)/course)):
        y0=front+row*course;y1=min(y0+course,back)
        max_x=east if y0 < dormer_front else dormer_west
        for i in range(-1,math.ceil(width/tile_width)+1):
            x0=max(west,west+(i+.5*(row%2))*tile_width)
            x1=min(max_x,west+(i+1+.5*(row%2))*tile_width-.006)
            if x1-x0<.022:continue
            ymax=min(y1,dormer_front) if x0>=dormer_west else y1
            if ymax-y0<.015:continue
            split=x0+(x1-x0)*.30;n=len(verts)
            verts.extend([(x0,y0,zroof(y0)+.013),(split,y0,zroof(y0)+.048),(x1,y0,zroof(y0)+.021),
                          (x0,ymax,zroof(ymax)+.008),(split,ymax,zroof(ymax)+.036),(x1,ymax,zroof(ymax)+.011)])
            faces.extend([(n,n+1,n+4,n+3),(n+1,n+2,n+5,n+4)])
    builder.add(verts,faces,TILE,'53 roof/Staggered pantile rows')
    face=Facade(builder,(west,0),(east,0),'53 roof')
    face.box(0,eaves-.075,width,.14,.29,.092,EDGE,'Eave fascia')
    face.box(0,eaves+.035,width,.09,.135,.226,GUTTER,'Horizontal gutter')
    pipex=west+.069
    builder.tube([(pipex,-.226,eaves+.04),(pipex,-.226,eaves-.11),
                  (pipex,-.09,eaves-.29),(pipex,-.09,.18)],.045,GUTTER,8 if lod else 14,'53 roof/West drainpipe')
    # The outer party wall is higher than the surrounding tiles and curls upwards at its shoulder.
    points=[(front-.04,eaves-.09),(front-.04,eaves+.24),(.08,zroof(.08)+.28),
            (.26,zroof(.26)+.18),(.46,zroof(.46)+.19),(.89,zroof(.89)+.36),
            (1.48,zroof(1.48)+.50),(2.41,zroof(2.41)+.62),(2.65,zroof(2.65)+.53),
            (2.78,zroof(2.78)+.28),(back,zroof(back)+.24),(back,zroof(back)-.11)]
    party=Polygon(points)
    builder.prism(party,west,west+.15,lambda y,z,x:(x,y,z),EDGE,'53 roof/Curved party coping')
    dormer=Facade(builder,(dormer_west,dormer_front),(east,dormer_front),'53 dormer')
    x=.003*width; sill=zroof(dormer_front)+.096; head=8.55
    win_w=width*.278; hole=shape_rect(x,sill,win_w,head-sill)
    wall=dormer.wall(zroof(dormer_front)-.010,8.88,[hole],.14,PLASTER)
    grit(dormer,wall.buffer(-.045),470,lod)
    shallow_glazing(dormer,x,sill,win_w,head-sill,2,3,'Green dormer window')
    for sign in [-1,1]:
        leaf_x=dormer.center[0]+x+sign*(win_w/2-.015)
        ang=(-1 if sign<0 else 1)*1.14
        casement(builder,leaf_x,dormer_front-.06,sill+.018,-sign*win_w*.46,head-sill-.035,ang,'53 outward dormer '+str(sign),rows=3)
    dormer.box(-.0175,8.889,dormer.length+.035,.082,.244,.049,EDGE,'Dormer fascia')
    dormer.box(-.035,8.969,dormer.length+.07,.079,.249,.058,GUTTER,'Dormer eave edge')
    # The 53 study ends on the division below the shared dormer, as seen above the two gate pillars.
    cheek=Polygon([(dormer_front,zroof(dormer_front)),(dormer_front,8.93),(back,9.19),(back,zroof(back))])
    builder.prism(cheek,dormer_west-.027,dormer_west+.083,lambda y,z,x:(x,y,z),PLASTER,'53 dormer/West cheek')
    slab=box(dormer_west-.044,dormer_front-.105,east,back)
    builder.prism(slab,-.055,.0,lambda x,y,d:(x,y,8.978+.095*(y-dormer_front)+d),TILE_DARK,'53 dormer/Shallow top')
    center_fin=Facade(builder,(east-.20,-.005),(east,-.005),'53 roof division')
    center_fin.box(0,6.28,.18,.66,.193,.055,EDGE,'Short projecting corbel')
    for i in range(3):
        center_fin.box(0,5.96+.083*i,.12+i*.017,.045,.064+i*.024,.041,EDGE,'Corbel step')
    fin_profile=Polygon([(front,eaves),(front,eaves+.44),(.45,zroof(.45)+.42),
                         (dormer_front,zroof(dormer_front)+.36),(dormer_front,zroof(dormer_front)-.01)])
    builder.prism(fin_profile,east-.18,east,lambda y,z,x:(x,y,z),EDGE,'53 roof division/Short fin')


def add_building(builder,lod=False):
    dimensions=json.loads((HERE/'dimensions.json').read_bytes())
    width=dimensions['western_house_frontage_m'];depth=dimensions['front_wall_to_house_m']
    south_house(builder,width,lod)
    roof_and_dormer(builder,width,lod)
    forecourt(builder,width,depth,lod)
