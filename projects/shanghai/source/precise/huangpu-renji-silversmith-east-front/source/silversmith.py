"""Model the three-bay east front of the Renji jewelry shop in metres.

X runs along Zhonghua Road toward Fangbang Road, Y toward the back. The high
pavilion in the early photograph has disappeared. The red roof visible behind
the parapet belongs to a separate glazed light well outside this section.
"""
from pathlib import Path
import json
import math

import numpy as np
from shapely.affinity import scale, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade

SOURCE = Path(__file__).resolve().parent
FRAME = json.loads((SOURCE / 'frontage-registration.json').read_bytes())
HALF = 5.82
PLASTER = 'Pale weathered shop stucco'
STONE = 'Cream stone and mouldings'
HONEY = 'Ochre relief highlights'
DARK_STONE = 'Grey recessed stone'
SASH = 'Dark red timber sash'
GLASS = 'Smoky glass'
BOARD = 'Boarded street opening'
METAL = 'Southern shutter'
CANAL = 'Dull street plinth'
SECTION = 'Cut surface'
MATERIALS = {
    PLASTER: {'color': [.733,.710,.622], 'roughness': .9},
    STONE: {'color': [.771,.692,.510], 'roughness': .83},
    HONEY: {'color': [.717,.566,.312], 'roughness': .78},
    DARK_STONE: {'color': [.445,.424,.344], 'roughness': .91},
    SASH: {'color': [.212,.115,.079], 'roughness': .70},
    GLASS: {'color': [.157,.193,.197], 'roughness': .35, 'metallic': .13},
    BOARD: {'color': [.439,.310,.200], 'roughness': .88},
    METAL: {'color': [.458,.469,.440], 'roughness': .77, 'metallic': .10},
    CANAL: {'color': [.544,.533,.486], 'roughness': .94},
    SECTION: {'color': [.536,.523,.464], 'roughness': .94},
}


def segment(half_width, spring, rise, divisions):
    """Photographed shallow circular head defined by its span and rise."""
    radius=(half_width**2+rise**2)/(2*rise)
    arc=math.asin(half_width/radius)
    return [(radius*math.sin(a),spring+rise-radius+radius*math.cos(a))
            for a in np.linspace(-arc,arc,divisions+1)]


def arch_band(half_width, spring, rise, thickness, divisions):
    upper=segment(half_width,spring,rise,divisions)
    return Polygon([*upper,*[(x,z-thickness)for x,z in reversed(upper)]])


def shape_at(shape, x, z):
    return translate(shape,xoff=x,yoff=z)


def course(face,x,z,w,h,depth,material,label):
    face.box(x,z,w,h,depth+.045,(depth-.045)/2,material,label)


def rectangle_window(face,x,sill,width,height,columns,rows,label,boarded=False,front=-.18):
    rect=box(x-width*.5,sill,x+width*.5,sill+height)
    fill=BOARD if boarded else GLASS
    face.prism(rect.buffer(.011,join_style=2),front-.07,front-.025,fill,label+' infill')
    if boarded:
        parts=[box(x-width*.5+width*i/4-.010,sill,x-width*.5+width*i/4+.010,sill+height)
               for i in range(1,4)]
        frame=unary_union(parts)
        face.prism(frame,front-.023,front-.012,SASH,label+' board seams')
        return rect
    edges=rect.difference(rect.buffer(-.054,join_style=2))
    bars=[box(x-width*.5+width*i/columns-.026,sill,x-width*.5+width*i/columns+.026,sill+height)
          for i in range(1,columns)]
    bars += [box(x-width*.5,sill+height*j/rows-.022,x+width*.5,sill+height*j/rows+.022)
             for j in range(1,rows)]
    face.prism(unary_union([edges,*bars]),front-.007,front+.045,SASH,label+' sash')
    return rect


def leaf(face,x,z,width,height,angle,d,sign,label):
    # A rolled acanthus tip stands free of the ground. It tapers at both ends.
    contour=[(0,0),(-.24,.16),(-.48,.46),(-.27,.40),(-.44,.73),(-.20,.61),
             (-.22,.84),(.04,1.0),(.08,.70),(.25,.77),(.22,.59),
             (.39,.62),(.27,.39),(.41,.42),(.25,.18)]
    a=math.radians(angle);co,si=math.cos(a),math.sin(a)
    outline=Polygon([(x+sign*(u*width*co-v*height*si),z+u*width*si+v*height*co)
                     for u,v in contour])
    face.prism(outline,d,d+.044,HONEY,label)


def curls(face,x,z,scale_factor,d,up,distant,label):
    """Two mirrored foliate stems taken from the scroll and hanging oval panels."""
    for s in (-1,1):
        points=[]
        for a in np.linspace(-1.21,4.95,12 if distant else 24):
            r=scale_factor*(.238-.0255*(a+1.21))
            points.append((x+s*(.165*scale_factor+r*math.cos(a)),
                           z+up*(.27*scale_factor+r*math.sin(a)),d+.040))
        face.builder.tube([face.point(*p)for p in points],.043*scale_factor,
                          HONEY,6 if distant else 8,face.label+'/'+label+' scroll')
        for i,ang in enumerate((9,43) if distant else (7,34,62)):
            leaf(face,x+s*(.05+.078*i)*scale_factor,z+up*.07*scale_factor,
                 .19*scale_factor,.29*scale_factor,up*ang,d+.008,s,label+' leaves')


def roundel(face,x,z,scale_factor,d,distant):
    disk=scale(Point(0,0).buffer(1,quad_segs=6 if distant else 12),
               xfact=.172*scale_factor,yfact=.22*scale_factor)
    face.prism(shape_at(disk,x,z),d,d+.075,STONE,'oval bosses')
    face.prism(shape_at(disk.difference(disk.buffer(-.038*scale_factor)),x,z),
               d+.074,d+.109,HONEY,'boss rims')
    curls(face,x,z-.50*scale_factor,scale_factor*.75,d,1,distant,'hanging foliage')
    for s in (-1,1):
        leaf(face,x+s*.060*scale_factor,z-.32*scale_factor,
             .18*scale_factor,.30*scale_factor,s*8,d+.002,s,'pendant leaves')


def stepped_window_frame(face,x,sill,w,h,distant,label):
    y1=sill+h
    outer=box(x-w/2-.115,sill-.065,x+w/2+.115,y1+.085)
    aperture=box(x-w/2,sill,x+w/2,y1)
    face.prism(outer.difference(aperture),-.020,.077,STONE,label+' jambs')
    course(face,x,sill-.103,w+.30,.12,.252,STONE,label+' sill')
    course(face,x,sill-.172,w+.205,.065,.170,STONE,label+' sill fillet')
    hood=Polygon([(x-w/2-.14,y1+.05),(x+w/2+.14,y1+.05),(x+w/2+.26,y1+.27),
                  (x-w/2-.26,y1+.27)])
    face.prism(hood,.030,.227,STONE,label+' lintel')
    if not distant:
        for d in np.linspace(-w*.45,w*.45,8):
            course(face,x+d,y1+.118,.075,.103,.253,HONEY,label+' dentils')
    plaque=box(x-w*.243,sill-.476,x+w*.243,sill-.259)
    face.prism(plaque,.002,.102,STONE,label+' apron tablet')
    inset=plaque.difference(plaque.buffer(-.036,join_style=2))
    face.prism(inset,.102,.126,HONEY,label+' tablet frame')
    for sign in (-1,1):
        course(face,x+sign*w*.325,sill-.265,w*.115,.12,.126,STONE,label+' apron corbels')
        leaf(face,x+sign*w*.09,sill-.438,.18,.15,40,.111,sign,label+' apron scroll')


def high_crown(face,distant):
    # The side walls rise in steps and ogee scrolls into a flat coped tablet.
    z0=12.26
    contour=[(2.64,z0),(2.64,13.81),(2.34,13.81),(2.31,14.22),(2.17,14.25),
             (2.04,14.32),(1.91,14.51),(1.75,14.74),(1.74,14.96),
             (1.55,14.96),(1.52,15.35),(1.49,15.90),(1.54,16.12)]
    peak=Polygon([(-x,z)for x,z in contour]+list(reversed(contour)))
    face.prism(peak,-.38,-.005,PLASTER,'scroll-topped parapet')
    course(face,0,16.12,3.14,.145,.22,STONE,'flat crest coping')
    course(face,0,16.016,3.00,.073,.140,HONEY,'crest lower fillet')
    course(face,0,15.02,2.88,.64,.088,STONE,'unlettered shop tablet')
    for s in (-1,1):
        for x,z,w in [(2.46,13.80,.44),(2.02,14.40,.55),(1.67,14.93,.36)]:
            course(face,s*x,z,w,.102,.145,STONE,'stepped crest ledges')
        curls(face,s*1.09,15.56,.76,.020,1,distant,'crest foliage')
        curls(face,s*1.91,14.48,.48,.011,1,distant,'side volutes')
        for rot in (7,37,63):
            leaf(face,s*1.09,15.62,.31,.44,rot,.045,s,'crest acanthus')
    # The alternating solid fillets are separate from the blind panel behind.
    for radius,z,rise,thick,back,front,mat in [
        (2.62,12.48,1.41,.151,-.010,.474,STONE),
        (2.53,12.44,1.29,.098,.010,.307,HONEY),
        (2.48,12.36,1.24,.088,.014,.194,STONE)]:
        face.prism(arch_band(radius,z,rise,thick,18 if distant else 34),
                   back,front,mat,'three moulded archivolts')
    if not distant:
        for px,pz in segment(2.39,12.41,1.18,23)[1:-1]:
            course(face,px,pz-.095,.064,.054,.134,HONEY,'arch soffit dentils')


def roof_rail(builder,face,sign,distant):
    xa,xb=2.72,5.11
    for z,thick,depth in [(12.47,.20,.38),(12.63,.08,.30),(13.57,.13,.35)]:
        course(face,sign*(xa+xb)/2,z,xb-xa+.06,thick,depth,STONE,'balcony parapet ledges')
    for x in np.linspace(xa+.18,xb-.18,6):
        stock=[(12.66,.103),(12.73,.107),(12.77,.075),(12.95,.060),
               (13.09,.119),(13.24,.100),(13.35,.056),(13.44,.067),(13.50,.088)]
        builder.lathe((sign*x,-.060),stock,STONE,8 if distant else 14,'east rail/turned balusters')
    center=sign*5.34
    course(face,center,13.40,.58,1.51,.22,PLASTER,'outer parapet pier')
    course(face,center,13.56,.245,.662,.243,DARK_STONE,'recessed pier panel')
    course(face,center,14.038,.71,.140,.30,STONE,'pier coping')
    crest=segment(.331,14.081,.160,12 if distant else 20)
    face.prism(translate(Polygon([*crest,(.331,14.068),(-.331,14.068)]),xoff=center),
               -.21,.21,STONE,'pier fan cap')


def central_lights(face,distant,holes):
    # The small side openings, wider centre light and the second row below
    # remain recessed behind the arch. The 2015 upper casement is open, the
    # later photo shows a dark red cross frame in the same opening.
    for x,w in [(0,1.00),(-1.74,.51),(1.74,.51)]:
        holes.append(rectangle_window(face,x,10.094,w,1.04,2 if x==0 else 1,2,'upper arch lights'))
    for x,w in [(-1.31,.49),(1.31,.49)]:
        holes.append(rectangle_window(face,x,7.945,w,1.31,1,2,'bow sidelights'))
    w=.90;cur=segment(w,9.31,.352,16 if distant else 28)
    opening=Polygon([(-w,7.92),(w,7.92),*reversed(cur)])
    holes.append(opening)
    face.prism(opening.buffer(.012,join_style=2),-.25,-.204,GLASS,'central arched glazing')
    mullions=[box(x-.027,7.92,x+.027,9.24)for x in (-.44,0,.44)]
    grille=unary_union([opening.difference(opening.buffer(-.056)),
                        box(-w,8.70,w,8.75),box(-w,9.23,w,9.30),*mullions]).intersection(opening)
    face.prism(grille,-.183,-.128,SASH,'arched timber sash')
    holes.append(rectangle_window(face,0,6.47,.94,1.09,2,2,'lower central light'))
    course(face,0,7.865,3.45,.113,.262,STONE,'bow sill')
    for sign in (-1,1):
        course(face,sign*.956,8.650,.124,1.416,.209,STONE,'slender central mullions')
    # Photographs show the arch flattening into two short horizontal returns.
    crest=arch_band(.985,9.53,.376,.123,18 if distant else 30)
    for sign in (-1,1):
        end=box(.975,9.407,1.69,9.530) if sign==1 else box(-1.69,9.407,-.975,9.530)
        crest=crest.union(end)
    face.prism(crest,-.009,.278,STONE,'central window raised hood')
    face.prism(Polygon([(-.133,9.97),(.133,9.97),(.092,9.77),(-.092,9.77)]),
               .216,.355,HONEY,'hood keystone')


def shop_level(face,distant,holes):
    # In 2021 the protected shop was closed. The temporary green panels do
    # not establish the original shape of the entrance or its old inscription.
    holes.append(rectangle_window(face,0,.06,1.77,2.40,2,3,'closed street doors',front=-.245))
    course(face,0,1.277,1.76,2.40,-.008,PLASTER,'closed shop front leaves')
    for x in (-.441,.441):
        course(face,x,1.30,.845,2.29,.015,METAL,'plain shop leaf')
    course(face,0,2.714,2.96,.36,.055,PLASTER,'plain entrance surround')
    for x in (-1.22,1.22):
        course(face,x,1.385,.48,2.67,.055,PLASTER,'entrance jamb')
    shutter=box(-4.66,.055,-2.94,2.835)
    holes.append(shutter)
    face.prism(shutter.buffer(.01,join_style=2),-.224,-.157,METAL,'southern shutter')
    for y in np.arange(.19,2.75,.19 if distant else .115):
        face.box(-3.8,y,1.67,.028,.025,-.132,METAL,'shutter seams')
    for z in (1.13,1.82,2.60,3.42):
        closed_panels=[(-5.74,-4.71),(-2.88,-1.53),(1.54,5.74)]
        for a,b in closed_panels:
            course(face,(a+b)/2,z,b-a,.030,.012,DARK_STONE,'shopfront horizontal joints')
    for z,h,d in [(4.66,.094,.096),(4.82,.128,.193),(4.976,.084,.26)]:
        course(face,0,z,11.70,h,d,STONE,'shop fascia courses')
    for x in (-5.37,-4.13,-2.57,-1.34,0,1.34,2.57,4.13,5.37):
        course(face,x,4.52,.094,.29,.116,DARK_STONE,'fascia bracket')
    face.prism(arch_band(1.60,4.975,1.07,.120,15 if distant else 29),-.010,.184,STONE,'lower gable above shop')
    course(face,0,5.87,.31,.193,.209,STONE,'shop arch crown block')


def east_front(builder,distant):
    face=Facade(builder,(-HALF,0),(HALF,0),'east')
    holes=[]
    shop_level(face,distant,holes)
    central_lights(face,distant,holes)
    for sign in (-1,1):
        for index,(sill,w,h) in enumerate([(6.60,1.36,1.66),(9.99,1.42,1.46)]):
            x=sign*3.773
            holes.append(rectangle_window(face,x,sill,w,h,2,3,'wing windows',
                                          boarded=sign==1 and index==0))
            stepped_window_frame(face,x,sill,w,h,distant,'wing surrounds')
        for x,width in [(2.39,.43),(5.34,.44)]:
            course(face,sign*x,8.69,width,7.42,.089,PLASTER,'long flat pilasters')
            course(face,sign*x,11.70,width+.16,.14,.172,STONE,'pilaster cap')
            roundel(face,sign*x,11.37,.91,.095,distant)
        for x in (2.36,5.36):
            course(face,sign*x,12.37,.83,.138,.428,STONE,'springing cap lower')
            course(face,sign*x,12.465,.92,.074,.510,STONE,'springing cap nosing')
        for z,h,d in [(5.24,.078,.137),(12.20,.14,.19),(12.37,.13,.34),(12.47,.067,.40)]:
            centre=sign*(2.11+HALF)/2
            course(face,centre,z,HALF-2.11,h,d,STONE,'wing cornice')
        roof_rail(builder,face,sign,distant)
    wall=box(-HALF,.025,HALF,12.29).difference(unary_union(holes))
    face.prism(wall,-.375,-.004,PLASTER,'street elevation')
    high_crown(face,distant)


def street_returns(builder,distant):
    south,north,back_north,back_south=FRAME['outline_xy']
    # The current street-side photographs show the first pair of upper windows
    # behind the northern corner. The building continues behind this measured slice.
    face=Facade(builder,north,back_north,'north return')
    holes=[]
    for i,(sill,height) in enumerate([(6.64,1.62),(10.0,1.45)]):
        w=.86 if i==0 else .83
        holes.append(rectangle_window(face,.43,sill,w,height,2,3,'short return windows',i==0))
        stepped_window_frame(face,.43,sill,w,height,distant,'return stone')
    face.prism(box(-face.length/2,.026,face.length/2,12.29).difference(unary_union(holes)),
               -.263,-.002,PLASTER,'return wall')
    for z,h,d in [(4.66,.094,.12),(4.82,.128,.17),(4.976,.084,.22),(12.20,.14,.16),(12.37,.13,.24)]:
        course(face,0,z,face.length,h,d,STONE,'turning eaves')
    side=Facade(builder,back_south,south,'south limit')
    side.prism(box(-side.length*.5,.025,side.length*.5,12.28),-.20,-.002,PLASTER,'plain end')
    # The mouldings on a splayed return reach slightly beyond its nominal
    # section. The narrow solid sleeve spans that difference to the city cap.
    north_joint=[back_north[0]+.033,back_north[1]+.158]
    south_joint=[back_south[0]+.009,back_south[1]+.158]
    back=Facade(builder,north_joint,south_joint,'back limit')
    back.prism(box(-back.length/2,.025,back.length/2,12.275),-.12,0,SECTION,'section wall')
    footprint=Polygon([south,north,back_north,north_joint,south_joint,back_south])
    for start,end in ((back_north,north_joint),(south_joint,back_south)):
        joint=Facade(builder,start,end,'joint')
        joint.prism(box(-joint.length/2,.025,joint.length/2,12.28),
                    -.064,-.006,SECTION,'short return end')
    builder.plan_prism(footprint,.00,.025,CANAL,'east shop/ground')
    roof=footprint.intersection(box(-10,.420,10,north_joint[1]+.01))
    builder.plan_prism(roof,12.12,12.284,SECTION,'east shop/section top')


def add_building(builder,distant):
    street_returns(builder,distant)
    east_front(builder,distant)
