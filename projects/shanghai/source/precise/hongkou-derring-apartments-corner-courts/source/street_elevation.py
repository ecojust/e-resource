"""Street elevations of Derring Apartments in its photographed 2021–22 state."""
import math

import numpy as np
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union

from photo_architecture import Facade,opening
from taishan_bricks import BRICK

BASE='Pale cut-stone base'
ROUGH='Ochre roughcast upper walls'
PANEL='Ivory spandrel'
FRAME='Painted dark steel'
GLASS='Grey-blue glazing'
GLAZED='Green glazed ceramic'
CAP='Warm buff mouldings'
METAL='Muted grey sheet metal'
SHADOW='Dark shop recess'
SHUTTER='Silver-grey shutter'
ROOF='Weathered roof slab'
COVER='Pale green courtyard cover'


def panel(f,x,z,w,h,lod):
    f.box(x,z,w,h,.14,.058,PANEL,'Recessed pale spandrels')
    f.box(x,z+h/2-.04,w+.10,.085,.23,.094,CAP,'Spandrel head')
    if lod:return
    for side in (-1,1):
        f.box(x+side*w*.425,z+h*.31,.064,h*.23,.035,.139,CAP,'Spandrel head stops')
    # The source shows an open-ended shallow line with canted ends near the foot.
    pts=[(x-w*.338,z-h*.218),(x-w*.27,z-h*.30),(x+w*.27,z-h*.30),(x+w*.338,z-h*.218)]
    f.prism(LineString(pts).buffer(.022,cap_style=2,join_style=2),.128,.155,CAP,'Spandrel relief')


def window(f,x,lo,hi,width,lod,style,decoration=False):
    sh=box(x-width/2,lo,x+width/2,hi)
    f.prism(sh.buffer(.015,join_style=2),-.286,-.266,GLASS,'Recessed glazing')
    jamb=sh.buffer(-.016,join_style=2)
    bars=[]
    for ratio in ((.5,) if lod else (.33,.66)):
        xx=x-width/2+width*ratio;bars.append(box(xx-.022,lo,xx+.022,hi))
    for ratio in ((.55,) if lod else (.33,.68)):
        zz=lo+(hi-lo)*ratio;bars.append(box(x-width/2,zz-.023,x+width/2,zz+.023))
    panes=sh.buffer(-.083,join_style=2).difference(unary_union(bars))
    f.prism(jamb.difference(panes),-.241,-.135,FRAME,'Steel casements')
    f.box(x,lo-.041,width+.18,.088,.40,.02,CAP,'Projecting sills')
    if decoration:
        rise=.26
        outer=opening(x,hi+.11,width+.32,rise+.16,rise,18 if lod else 32)
        inner=opening(x,hi+.05,width+.11,rise+.11,rise*.76,18 if lod else 32)
        f.prism(outer.difference(inner),-.02,.165,CAP,'Segmental upper window caps')
    return sh


def brick_pier(f,x,width,z0,z1,lod):
    if width<.16:return
    f.box(x,(z0+z1)/2,width,z1-z0,.105,.045,BRICK,'Raised brown-brick pilasters')
    if width>.65:
        f.box(x,(z0+z1)/2,width*.69,z1-z0,.11,.109,BRICK,'Stepped brick faces')
        if not lod:
            for side in (-1,1):
                f.box(x+side*width*.445,(z0+z1)/2,.09,z1-z0,.053,.105,BRICK,'Outer brick arrises')


def portal_shape(x,w,h,arch,segments=20):
    if arch:return opening(x,.025,w,h,arch,segments)
    bevel=min(.23,w*.10)
    return Polygon([(x-w/2,.025),(x+w/2,.025),(x+w/2,h-bevel),(x+w/2-bevel,h),
                    (x-w/2+bevel,h),(x-w/2,h-bevel)])


def southwest_door(f,height,lod):
    """Projecting carved doorframe seen before repairs in the 2019, 2021 and 2022 photographs."""
    width=min(2.73,f.length*.47);head=height*.545
    cut=box(-width/2,.025,width/2,head)
    body=f.wall(.03,height,[cut],.39,BASE)
    piers=box(-.398*f.length,.03,.398*f.length,height-.30)
    sculpture=opening(0,head+.105,width+.10,height*.249,.29,16 if lod else 34)
    # The double door is rectangular. The shallow stone tympanum above it is blind.
    f.prism(piers.difference(cut.union(sculpture)),.002,.238,BASE,'Projecting cut-stone doorcase')
    f.prism(sculpture,.003,.035,BASE,'Blind segmental tympanum')
    f.prism(sculpture.buffer(.083,join_style=2).difference(sculpture),.205,.274,CAP,'Tympanum bead')
    f.prism(cut.buffer(.014,join_style=2),-.335,-.305,GLASS,'Recessed double doors')
    edge=cut.buffer(-.019);panes=cut.buffer(-.083,join_style=2).difference(box(-.035,.02,.035,head))
    f.prism(edge.difference(panes),-.26,-.146,FRAME,'Door frame and meeting stiles')
    for side in (-1,1):
        x=side*.31*f.length
        f.box(x,.235,.163*f.length,.41,.34,.163,BASE,'Wide plinth blocks')
        if not lod:
            f.box(side*.115,1.03,.034,.41,.099,-.072,FRAME,'Paired door pull')
            f.box(x,head+.36,.146*f.length,.043,.026,.25,CAP,'Stone panel margin')
    for zz,hh,dd in [(head+.047,.105,.27),(height-.68,.12,.24),(height-.32,.135,.34),(height-.13,.20,.41)]:
        f.box(0,zz,.82*f.length,hh,dd,.24,CAP,'Portal cornice and lintel')
    # A continuous band of small blind arches survives above the doorway.
    count=11;span=.78*f.length;space=span/count;spring=height-.68
    for i in range(count):
        x=(i-(count-1)/2)*space
        outer=opening(x,spring,space*.93,.29,.183,9 if lod else 18)
        inner=opening(x,spring-.012,space*.66,.211,.126,9 if lod else 18)
        f.prism(outer.difference(inner),.220,.306,CAP,'Blind-arcade frieze over main portal')
    for zz in np.arange(.51,height-.2,.53):
        for side in (-1,1):
            x=side*f.length*.45;f.box(x,zz,f.length*.10,.018,.038,.013,CAP,'Return rustication')
    f.box(width*.80,head-.23,.27,.19,.043,.27,FRAME,'Period plaque backing')


def walk_level(f,kind,bays,base,lod):
    if kind=='southwest':
        southwest_door(f,base,lod);return
    if kind in ('west','northwest'):
        f.wall(.035,base,(),.34,BASE)
        if kind=='west':
            # A black service grille interrupts the otherwise closed street hoarding.
            u=f.length*.28;zw=.74
            f.box(u,zw,2.75,1.4,.085,.055,SHADOW,'Low service grille')
            if not lod:
                for v in np.linspace(.15,1.31,13):f.box(u,v,2.67,.032,.11,.09,FRAME,'Service grille slats')
        f.beam(base-.12,.14,.14,CAP,label='Upper plinth moulding')
        return
    slots=[]
    if kind=='south':
        gap=f.length/len(bays)
        for i,x in enumerate(bays):slots.append((x,gap*.71,base*.79,0,i%4 in (1,2)))
    else:
        slots=[(0.,min(2.78,f.length*.52),base*.79,.57 if kind=='east-cut' else .37,False)]
    holes=[]
    for x,width,ht,arc,shutter in slots:
        shape=portal_shape(x,width,ht,arc,12 if lod else 24);holes.append(shape)
        f.prism(shape.buffer(.013,join_style=2),-.34,-.32,SHUTTER if shutter else GLASS,'Closed shopfront or portal glazing')
        if shutter:
            if not lod:
                for h in np.arange(.17,ht-.18,.16):
                    f.box(x,h,width-.09,.023,.042,-.285,METAL,'Rolled steel shutters')
        else:
            divs=[x] if kind!='south' else [x-width*.25,x,x+width*.25]
            lines=[box(v-.04,.02,v+.04,ht)for v in divs]
            lines.append(box(x-width/2,ht*.77-.035,x+width/2,ht*.77+.035))
            inner=shape.buffer(-.095,join_style=2).difference(unary_union(lines))
            f.prism(shape.buffer(-.02).difference(inner),-.27,-.14,FRAME,'Portal and shopfront joinery')
        if kind!='south':
            trim=shape.buffer(.20,join_style=2).difference(shape).intersection(box(-f.length,0,f.length,base))
            f.prism(trim,-.01,.13,BASE,'Doorway surround')
    wall=f.wall(.035,base,holes,.38,BASE)
    for z in np.arange(.46,base,.43 if not lod else .86):
        joint=wall.intersection(box(-f.length/2,z-.009,f.length/2,z+.009))
        if not joint.is_empty:f.prism(joint,.001,.012,CAP,'Incised base courses')
    f.beam(base-.13,.16,.17,CAP,label='Upper plinth moulding')


def street_wall(b,a,c,label,kind,bays,pier_runs,levels,lod):
    f=Facade(b,a,c,label);lo=np.array(levels['sill']);hi=np.array(levels['head']);base=levels['base']
    all_holes=[];left,right=-f.length/2,f.length/2;regular=1.38
    for j,x in enumerate(bays):
        in_brick=any(u<=x<=v for u,v in pier_runs)
        for floor,(s,h) in enumerate(zip(lo,hi)):
            width=regular if not in_brick else 1.57
            if kind in ('southwest','east-cut','northwest'):width=1.43
            if floor==4 and kind=='southwest':continue
            all_holes.append(window(f,x,s,h,width,lod,kind,in_brick and floor==3 and kind!='southwest'))
            if in_brick and floor<3:panel(f,x,(h+lo[floor+1])/2,width+.11,lo[floor+1]-h-.13,lod)
    # Separate the brick and roughcast fields before triangulation. The window
    # cuts go through both skins at exactly the same coordinates as the glazing.
    ztop=levels['body'];top=levels['regular_top'];field=box(left,base,right,ztop)
    brown=unary_union([box(max(u,left),base,min(v,right),ztop)for u,v in pier_runs])if pier_runs else Polygon()
    holes=unary_union(all_holes)
    for shape,mat in [(field.difference(brown),ROUGH),(field.intersection(brown),BRICK)]:
        if not shape.is_empty:f.prism(shape.difference(holes),-.38,0,mat,'Punched upper wall')
    for u,v in pier_runs:
        within=sorted(x for x in bays if u<=x<=v)
        spaces=[(max(left,u),min(right,v))] if not within else list(zip([max(left,u)]+[x+.81 for x in within],[x-.81 for x in within]+[min(right,v)]))
        for l,r in spaces:
            if r-l>.26:brick_pier(f,(l+r)/2,.84*(r-l),base+.02,ztop-.03,lod)
    if kind=='southwest':
        return f
    crown=box(left,ztop,right,top);f.prism(crown.difference(holes),-.38,0,ROUGH,'Sixth-floor roughcast')
    f.beam(ztop,.135,.105,CAP,label='Brick to roughcast transition')
    for x in bays:
        f.box(x,lo[4]-.12,1.66,.12,.42,.04,CAP,'Upper sash ledges')
    f.beam(top-.62,.125,.08,CAP,label='Upper facade band')
    f.beam(top-.12,.22,.165,CAP,label='Parapet coping')
    return f
