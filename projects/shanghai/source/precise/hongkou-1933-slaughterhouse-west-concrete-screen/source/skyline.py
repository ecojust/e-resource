"""Stepped cornice, triangular patterned heads, tall entrance piers and the terrace edge."""
import math
import numpy as np
from shapely.geometry import LineString,Polygon,box
from aggregate_finish import CAST
from pierced_screens import EDGE,SHADE,METAL
from street_arcade import DRESS,SOFFIT


def regular_head(f,p,lod):
    top=p['ordinary_sill']+12*p['screen_pitch'];parapet=p['height_regular_parapet']
    # The two leaves share a head: sawtooth frieze both sides of a raised fan capital.
    f.prism(box(-f.length/2,top,f.length/2,parapet),-.55,.042,CAST,'Parapet band')
    f.beam(top+.06,.13,.16,DRESS,label='Continuous pierced-window drip')
    span=2*(1.23*p['screen_pitch']+p['pair_axis']/2)
    f.box(0,top+.32,span,.39,.089,.104,DRESS,'Toothed head strip')
    for i in range(16):
        l=(i-8)*span/16;r=l+span/16;mid=(l+r)/2
        f.prism(Polygon([(l+.013,top+.46),(mid,top+.21),(r-.013,top+.46)]),
                .147,.177,CAST,'Triangular low relief')
    for z,w,h,d,mat in [(top-.075,.62,.095,.13,DRESS),(top+.045,.75,.093,.21,DRESS),(top+.16,.67,.098,.17,SHADE),(top+.275,.68,.10,.21,DRESS)]:
        f.box(0,z,w,h,d,.15,mat,'Central mullion impost')
    fan=Polygon([(-.34,top+.32),(.34,top+.32),(.42,top+.62),(.23,top+.77),(0,top+.79),(-.23,top+.77),(-.42,top+.62)])
    f.prism(fan,.076,.207,CAST,'Fan-shaped central crown')
    for u in (-.25,.25):
        f.prism(LineString([(0,top+.36),(u,top+.727)]).buffer(.020,cap_style=2),.203,.223,SHADE,'Fan incisions')


def curved_piers(f,bottom,top,lod):
    # The central upright and its two pairs of flanking uprights cast separate
    # vertical shadows. Fit their rounded fronts between the pierced strips.
    for u,w in ((0,.585),(-1.67,.70),(1.67,.70),(-3.31,.79),(3.31,.79)):
        arc=np.linspace(0,math.pi,9 if lod else 21)
        section=[(u-w/2,.14),(u+w/2,.14)]+[(u+w/2*math.cos(a),.175+.237*math.sin(a))for a in arc]
        v=[f.point(x,z,d)for z in (bottom,top) for x,d in section]
        n=len(section)
        faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
        faces.extend((i,i+n,(i+1)%n+n,(i+1)%n)for i in range(n))
        f.builder.add(v,faces,CAST,f.label+'/Rounded concrete piers')


def central_coping(f,z,cw,lod):
    # A continuous bullnose runs across the high central roof edge.
    arc=np.linspace(-math.pi/2,math.pi/2,9 if lod else 21)
    cross=[(-.59,z-.48)]+[(.19+.335*math.cos(t),z-.25+.25*math.sin(t))for t in arc]+[(-.59,z)]
    n=len(cross)
    v=[f.point(u,zz,d)for u in (-cw/2,cw/2)for d,zz in cross]
    faces=[tuple(range(n)),tuple(range(2*n-1,n-1,-1))]
    faces+= [(i,i+n,(i+1)%n+n,(i+1)%n)for i in range(n)]
    f.builder.add(v,faces,CAST,f.label+'/Bullnose roof coping')
    # Parallel slats are visible beyond either end of the coping in both front photographs.
    for u in (-cw/2-.59,cw/2+.59):
        for d in np.linspace(.05,-2.84,10):
            f.box(u,z-.19,1.18,.045,.062,d,METAL,'Roof canopy slats')
        for v in (-.48,.48):
            f.box(u+v,z-.21,.056,.081,3.04,-1.39,METAL,'Roof canopy runners')


def centre_head(f,p,lod):
    top=p['central_sill']+13*p['central_pitch'];z=p['height_entrance_cap'];cw=p['entrance_cap_width']
    f.prism(box(-f.length/2,top,f.length/2,z-.78),-.67,.24,CAST,'Entrance attic')
    curved_piers(f,p['central_sill'],top,lod)
    central_coping(f,z,cw,lod)
    for zz,ww,hh,pr,mat in [(z-.80,cw+.36,.22,.38,DRESS),(z-.57,cw+.16,.25,.32,CAST),(z-.37,cw+.07,.13,.31,SHADE)]:
        f.box(0,zz,ww,hh,pr+.57,pr*.5-.17,mat,'Rounded stepped entrance coping')
    for x in (-p['centre_ring_separation']/2,p['centre_ring_separation']/2):
        for z1,t in [(top-.01,.095),(top+.20,.08),(top+.34,.09)]:
            f.box(x,z1,1.03,t,.30,.285,DRESS,'Stepped ring-column heads')
    f.prism(Polygon([(-.26,top+.35),(0,top+.031),(.26,top+.35),(.14,top+.35),(0,top+.177),(-.14,top+.35)]),.252,.292,EDGE,'Central chevron')


def side_louvres(f,u,bottom,top,lod):
    width=.59
    f.prism(box(u-width/2,bottom,u+width/2,top),-.46,-.43,SHADE,'Louvre recess')
    step=(top-bottom)/26
    boundary=box(u-width/2,bottom,u+width/2,top)
    for i in range(27):
        z=bottom+i*step
        slat=Polygon([(u-width/2,z+.19),(u+width/2,z-.12),(u+width/2,z-.12+.13),(u-width/2,z+.32)]).intersection(boundary)
        if slat.area>.003:f.prism(slat,-.285,-.075,DRESS,'Diagonal concrete louvres')


def terrace(f,p,lod):
    z=p['height_regular_parapet'];w=f.length;d=.75
    for h in (.04,.46):
        f.box(0,z+h,w,.044,.041,-d,METAL,'Slender terrace rail')
    for x in np.linspace(-w/2+.08,w/2-.08,max(3,round(w/1.45))+1):
        f.box(x,z+.239,.039,.49,.037,-d,METAL,'Terrace rail uprights')
