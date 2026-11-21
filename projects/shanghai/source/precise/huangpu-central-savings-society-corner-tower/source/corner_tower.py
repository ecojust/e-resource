"""Tianjin Road at Jiangxi Middle Road. Local X runs toward the northern wing.

The documented street corner, its stepped shoulders and short street returns
are modeled. No detail is inferred for the building behind the cut plane.
All lengths in metres; the calibrated window/door positions are observations
from two street images. Depths, glass colour and obscured joints are estimates.
"""
from pathlib import Path
import json
import math

import numpy as np
from shapely import set_precision
from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from sign_lettering import lettering_shapes

SOURCE = Path(__file__).resolve().parent
FRAME = json.loads((SOURCE / 'frontage-registration.json').read_bytes())
HALF = FRAME['corner_face_width_m']/2
STONE = 'Warm grey dressed stone'
LIGHT = 'Light arris and crown'
JOINT = 'Weathered stone joint'
SHADE = 'Recessed ashlar'
SPANDREL = 'Fluted spandrel'
WINDOW = 'Smoked blue steel sash glazing'
STEEL = 'Oxidised window frames'
IRON = 'Dark patterned metal leaves'
LOCK = 'Metal raised medallions'
SHADOW = 'Entrance interior shade'
NAME = 'Gilded bank name'
MATERIALS = {
    STONE: {'color': [.669,.622,.559], 'roughness': .83},
    LIGHT: {'color': [.740,.696,.610], 'roughness': .78},
    JOINT: {'color': [.555,.508,.444], 'roughness': .88},
    SHADE: {'color': [.489,.467,.405], 'roughness': .91},
    SPANDREL: {'color': [.604,.562,.488], 'roughness': .83},
    WINDOW: {'color': [.292,.361,.392], 'roughness': .33, 'metallic': .14},
    STEEL: {'color': [.210,.228,.233], 'roughness': .63, 'metallic': .22},
    IRON: {'color': [.158,.175,.166], 'roughness': .66, 'metallic': .38},
    LOCK: {'color': [.274,.287,.260], 'roughness': .58, 'metallic': .40},
    SHADOW: {'color': [.065,.071,.070], 'roughness': .98},
    NAME: {'color': [.632,.509,.293], 'roughness': .60, 'metallic': .32},
}
SILLS = [8.45,11.30,14.48,17.86,20.94,24.18,27.53,29.62]
LIGHT_HEIGHTS = [1.73,1.90,1.91,1.91,1.94,1.97,1.49,1.69]
WINDOW_AXES = [-1.07,0,1.07]


def pane(face, x, sill, width, height, divisions, rows, lod, label):
    aperture = box(x-width/2,sill,x+width/2,sill+height)
    back = -.36
    bars = [box(x-width/2+width*i/divisions-.029,sill,
                x-width/2+width*i/divisions+.029,sill+height)
            for i in range(1,divisions)]
    bars += [box(x-width/2,sill+height*j/rows-.027,
                 x+width/2,sill+height*j/rows+.027)
             for j in range(1,rows)]
    rim = aperture.difference(aperture.buffer(-.047, join_style=2))
    frame = unary_union([rim,*bars])
    face.prism(aperture.buffer(.008,join_style=2),back-.02,back,WINDOW,label+' glass')
    face.prism(frame,back+.015,back+.066,STEEL,label+' steel')
    if not lod:
        face.box(x,sill-.030,width+.070,.056,.19,.012,STONE,label+' sill')
    return aperture


def courses(face, surface, width, top, lod):
    """Staggered mortar at the exposed outside piers, interrupted by all cuts."""
    strips=[]
    if lod:
        return
    for row in range(1,math.ceil(top/.50)):
        z=row*.50
        strips.append(box(-width/2,z-.008,width/2,z+.008))
        x=-width/2+(row%2)*.57
        while x<width/2:
            strips.append(box(x-.007,z,x+.007,min(top,z+.50)))
            x+=1.14
    if strips:
        engraving=unary_union(strips).intersection(surface)
        face.prism(engraving,.002,.009,JOINT,'ashlar courses')


def gate(face,lod):
    """Each Art Deco leaf has paired angular openings and a round central boss."""
    for sign in (-1,1):
        center=sign*.804
        half=.775
        zlo,zhi=.50,5.93
        stock=box(center-half,zlo,center+half,zhi)
        holes=[]
        for base,n,step in [(1.19,5,.295),(3.99,5,.307)]:
            for j in range(n):
                for c in range(4):
                    cx=center+(c-1.5)*.337
                    cz=base+j*step
                    # The two lobes taper towards the narrow bridge. The grille
                    # cuts go through the metal itself, with a dark backstop.
                    for flank in (-1,1):
                        holes.append(Polygon([(cx+flank*.030,cz-.018),(cx+flank*.125,cz-.115),
                                              (cx+flank*.125,cz+.115),(cx+flank*.030,cz+.018)]))
        for flank in (-1,1):
            for j in range(2):
                cx=center+flank*.513;cz=3.053+j*.253
                cell=box(cx-.120,cz-.136,cx+.120,cz+.136)
                islands=Point(cx-.014,cz+.002).buffer(.098,quad_segs=4)
                holes.append(cell.difference(islands))
        face.prism(stock.difference(unary_union(holes)),-.48,-.397,IRON,'patterned gate leaves')
        rim=stock.difference(stock.buffer(-.043,join_style=2))
        face.prism(rim,-.395,-.366,LOCK,'metal door frame')
        disk=Point(center,3.15).buffer(.208,quad_segs=12 if lod else 23)
        face.prism(disk,-.394,-.363,IRON,'round door panels')
        face.prism(disk.difference(disk.buffer(-.031)),-.360,-.333,LOCK,'round panel rims')
    face.box(0,3.28,3.23,5.67,.052,-.652,SHADOW,'dark lining behind gate')
    # A separate narrow panel above the touching leaves remains legible despite
    # wires in the two present-day photographs.
    transom=box(-1.60,5.98,1.60,6.29)
    lights=[box(-1.51+i*.315,6.06,-1.32+i*.315,6.21)for i in range(10)]
    face.prism(transom.difference(unary_union(lights)),-.46,-.38,IRON,'perforated transom')
    face.box(0,6.16,3.23,.36,.052,-.65,SHADOW,'transom lining')
    for k in range(4):
        front=.66-k*.156
        face.box(0,(k+1)*.058,3.53,(k+1)*.116,front+.04,(front-.04)/2,
                 LIGHT if k==3 else STONE,'stone doorstep')


def front(builder,lod):
    f=Facade(builder,(-HALF,0),(HALF,0),'SE tower')
    holes=[box(-1.68,.008,1.68,6.34)]
    for row,(sill,h) in enumerate(zip(SILLS,LIGHT_HEIGHTS)):
        for x in WINDOW_AXES:
            holes.append(pane(f,x,sill,.78,h,1,5 if row>=6 else 4,lod,'three stacked windows'))
        upper=SILLS[row+1] if row+1<len(SILLS) else 33.97
        panelh=upper-(sill+h)-.09
        for x in WINDOW_AXES:
            if panelh>.16:
                f.box(x,sill+h+.04+panelh/2,.785,panelh,.065,-.012,SPANDREL,'spandrel panels')
                for dx in (-.256,-.126,0,.126,.256):
                    f.box(x+dx,sill+h+.06+panelh/2,.032,panelh-.06,.034,.033,
                          LIGHT,'spandrel grooves')
            if not lod:
                for dx in (-.31,-.155,0,.155,.31):
                    f.prism(Polygon([(x+dx-.048,sill+h-.016),(x+dx+.048,sill+h-.016),
                                     (x+dx,sill+h-.104)]),-.046,.048,SHADE,'window head fluting')
    profile=Polygon([(-HALF,0),(HALF,0),(HALF,34.35),(2.87,34.66),(1.64,34.66),
                     (1.52,34.24),(.86,34.24),(.72,34.40),(-.72,34.40),(-.86,34.24),
                     (-1.52,34.24),(-1.64,34.66),(-2.87,34.66),(-HALF,34.35)])
    skin=profile.difference(unary_union(holes))
    f.prism(skin,-.51,0,STONE,'pierced tower wall')
    courses(f,skin.difference(box(-1.52,6.55,1.52,34.7)),2*HALF,34.66,lod)
    for sign in (-1,1):
        x=sign*.537
        # From ground level to sky the two projecting stone fins follow the
        # dividing piers. Both rise beyond the separate corner shoulders.
        outline=Polygon([(x-.144,8.16),(x+.144,8.16),(x+.144,35.26),
                         (x+.085,35.26),(x+.085,35.64),(x-.085,35.64),
                         (x-.085,35.26),(x-.144,35.26)])
        f.prism(outline,-.015,.201,STONE,'tall stepped stone fins')
        f.box(x,21.46,.165,26.17,.074,.216,LIGHT,'projecting fin faces')
        for z,width,h in [(33.61,.184,.73),(34.22,.157,.65),(34.81,.130,.54),(35.33,.095,.42)]:
            f.box(x,z,width,h,.066,.256,LIGHT,'stepped fin tips')
        for z in np.arange(8.84,35.4,.65):
            if not lod:
                f.box(x,z,.244,.019,.025,.214,JOINT,'fin block joints')
    for i in range(-4,5):
        x=i*.23
        if abs(x)<.82:
            f.box(x,34.51,.103,.36,.23,-.035,LIGHT,'crown crenellations')
    for side in (-1,1):
        x=side*2.07
        f.box(x,3.23,.78,6.33,.215,.051,STONE,'broad entrance jambs')
        f.box(side*1.733,3.22,.092,6.38,.232,.071,LIGHT,'door reveal arrises')
        for y in (.45,1.34,2.29,3.26,4.22,5.15,6.11):
            f.box(x,y,.78,.014,.012,.163,JOINT,'jamb block joints')
        for k in range(6):
            f.box(side*(1.85+k*.173),33.10,.074,.265,.097,.016,SHADE,'shoulder dentils')
        f.box(side*2.31,33.33,.98,.072,.135,.011,LIGHT,'shoulder incised string')
    f.box(0,6.52,4.91,.247,.328,.078,LIGHT,'projecting entrance lintel')
    f.box(0,6.344,4.01,.105,.261,.044,SHADE,'lintel soffit')
    gate(f,lod)
    # The name is the tenant photographed on the 2015-uploaded street front.
    # The much earlier black-and-white image has a differently lettered fascia.
    sign=box(-2.48,6.70,2.48,8.14)
    f.prism(sign,-.010,.014,STONE,'stone lintel face')
    for axis in (-1.65,-.56,.56,1.65):
        f.box(axis,7.66,.143,.92,.052,.027,STONE,'lintel stepped returns')
    for i,(char,shape)in enumerate(lettering_shapes('中國光大銀行',4.30,.62,
                                                  font=SOURCE/'street-inscription.otf')):
        glyph=set_precision(translate(shape,yoff=7.19).simplify(.003 if lod else .001,
                            preserve_topology=True),.0001)
        f.prism(glyph,.054,.080,NAME,'later lettering '+str(i+1))
    return profile


def square_tier_wall(f,lod,start,end,height,holes,level):
    left,right=-f.length/2,f.length/2
    panel=box(left,level,right,height)
    exposed=panel.difference(unary_union(holes))
    f.prism(exposed,-.405,0,STONE,'recessed street wall')
    courses(f,exposed,width=f.length,top=height,lod=lod)


def short_wing(builder,a,b,lod,label):
    """The first short stretch beyond the tall corner turns away on each street."""
    total=np.linalg.norm(b-a)
    v=(b-a)/total
    inner_joint=.88
    tier_join=3.65
    cuts=[0,inner_joint,tier_join,total]
    heights=(34.35,25.55,20.15)
    sections=[]
    for k,(s0,s1,height) in enumerate(zip(cuts,cuts[1:],heights)):
        p0=a+v*s0;p1=a+v*s1
        # On the western street the counterclockwise outer wall runs from
        # the farther return toward the tower. On the east it runs away.
        f=Facade(builder,*((p0,p1)if label=='Jiangxi'else(p1,p0)),label+str(k+1))
        windows=[]
        if k:
            width=f.length-.32
            windows.append(pane(f,0,1.48,width,2.56,3 if k==1 else 2,2,lod,'lower street lights'))
            windows.append(pane(f,0,4.68,width,1.82,3 if k==1 else 2,2,lod,'upper street lights'))
            f.box(0,4.38,width+.14,.175,.156,-.033,SPANDREL,'street beam')
            for i,(sill,h)in enumerate(zip(SILLS[:6],LIGHT_HEIGHTS)):
                if sill+h+.26>height:break
                windows.append(pane(f,0,sill,width,h,3 if k==1 else 2,2,lod,'ribbon windows'))
        square_tier_wall(f,lod,s0,s1,height,windows,0)
        f.box(0,height-.091,f.length,.164,.23,-.048,LIGHT,'flat parapet')
        sections.append(p1)
    return sections


def add_building(builder,distant):
    profile=front(builder,distant)
    a,b,north,west=np.asarray(FRAME['outline_xy'],float)
    left=short_wing(builder,a,west,distant,'Tianjin')
    right=short_wing(builder,b,north,distant,'Jiangxi')
    entire=Polygon([a,b,north,west])
    # The adjoining original block remains in the city beyond this section.
    # Only the outer storeys seen in both street photographs have openings.
    tier2=entire.intersection(box(left[1][0],-1,right[1][0],10))
    tier1=entire.intersection(box(left[0][0],-1,right[0][0],10))
    for label,outline,bottom,top,exposed in [('street wing',entire,0,20.15,tier2),
                                           ('upper shoulder',tier2,20.15,25.55,tier1),
                                           ('tower return',tier1,25.55,34.35,None)]:
        coords=list(outline.exterior.coords)
        if not outline.exterior.is_ccw:
            coords=list(reversed(coords))
        for p0,p1 in zip(coords,coords[1:]):
            mid=LineString([p0,p1]).interpolate(.5,normalized=True)
            # Both wings and the central ground opening already have true
            # reveals. End walls inside this boundary are neutral section caps.
            if abs(mid.y)<.001:continue
            if min(LineString([a,west]).distance(mid),LineString([b,north]).distance(mid))<.008:continue
            f=Facade(builder,p0,p1,label)
            f.wall(bottom,top,thickness=.11,material=SHADE)
        roof=outline.difference(exposed)if exposed is not None else outline
        builder.plan_prism(roof,top-.12,top,STONE,label+' roof shoulder')
    for sign in (-1,1):
        # One masonry crown pier at the edge of each side of the front.
        builder.box((sign*2.39,.42,34.47),(1.54,.85,.39),STONE,label='crown/shoulder coping')
    builder.plan_prism(entire,-.015,.018,SHADE,'street frontage/grade')
