"""Splayed corner entrance, stepped parapet and an upper paired-arch loggia."""
import math
import numpy as np
from shapely.geometry import LineString,Polygon,box
from shapely.ops import unary_union

from photo_architecture import opening
from street_elevation import BASE,BRICK,CAP,FRAME,GLASS,GLAZED,PANEL,ROUGH,SHADOW


def southwest_crown(f,levels,lod):
    z=levels['sixth'];body=levels['body'];top=levels['regular_top']
    half=f.length/2;ledge=z-.36;opening_w=1.08;side=.62;h=1.76
    holes=[opening(x,z,opening_w,h,.46,15 if lod else 34) for x in (-side,side)]
    # Raised central shoulder and shallow gable rise above the two side wings.
    outline=Polygon([(-half,body), (half,body),(half,top-.35),
                     (half*.88,top-.35),(half*.88,top-.03),(half*.69,top-.03),
                     (half*.69,top+.24),(0,top+.60),(-half*.69,top+.24),
                     (-half*.69,top-.03),(-half*.88,top-.03),(-half*.88,top-.35),(-half,top-.35)])
    left=box(-half,body,-1.43,top+.8);right=box(1.43,body,half,top+.8)
    f.prism(outline.difference(unary_union(holes)), -.42,0,ROUGH,'Raised splayed parapet')
    for region in [left,right]:
        shape=outline.intersection(region).intersection(box(-half,body-.01,half,z+.61))
        if not shape.is_empty:f.prism(shape,-.015,.055,BRICK,'Brown brick wing of balcony')
    for x,shape in zip((-side,side),holes):
        f.prism(shape.buffer(.015,join_style=2),-.88,-.85,GLASS,'Glazed back of upper loggia')
        f.prism(shape.buffer(.132).difference(shape),-.05,.19,CAP,'Twin rounded arch bands')
        if not lod:
            for a in np.linspace(.14,math.pi-.14,9):
                yy=z+h-.46
                inner=(x+.56*math.cos(a),yy+.46*math.sin(a))
                outer=(x+.67*math.cos(a),yy+.56*math.sin(a))
                f.prism(LineString([inner,outer]).buffer(.012,cap_style=2),.191,.203,ROUGH,'Loggia arch joints')
        f.box(x,z+.55,.047,1.07,.062,-.78,FRAME,'Balcony rear glazing bar')
    for x in (-1.26,0.,1.26):
        f.box(x,z+.65,.14,1.33,.20,.091,CAP,'Loggia column cores')
        if not lod:
            helix=[]
            for step in range(21):
                q=step/20;ang=q*math.tau*2.25
                helix.append(f.point(x+.093*math.cos(ang),z+.15+q*1.05,.10+.08*math.sin(ang)))
            f.builder.tube(helix,.030,CAP,7,f.label+'/Spiral column mouldings')
        f.box(x,z+1.27,.25,.105,.28,.085,PANEL,'Loggia capital')
    f.box(0,ledge,3.13,.22,1.21,.414,CAP,'Balcony slab')
    f.box(0,ledge-.17,2.82,.13,.86,.27,BASE,'Balcony soffit')
    for x in (-1.43,0,1.43):
        f.box(x,ledge+.46,.17,.77,.23,.93,PANEL,'Balustrade posts')
    f.box(0,ledge+.78,3.06,.12,.29,.92,CAP,'Upper rail')
    f.box(0,ledge+.18,3.06,.13,.22,.92,CAP,'Lower rail')
    for x in (-.73,.73):
        for dx in np.linspace(-.48,.48,7 if not lod else 5):
            f.box(x+dx,ledge+.48,.061,.51,.078,.92,GLAZED,'Green glazed balustrade details')
        if not lod:
            for zz in (ledge+.35,ledge+.58):f.box(x,zz,1.20,.045,.074,.92,GLAZED,'Green ceramic ties')
    for x in (-1.50,1.50):
        f.box(x,ledge+.75,.15,.13,.86,.56,CAP,'Side rails')
    field=outline.difference(outline.buffer(-.092,join_style=2)).intersection(box(-half,top-.39,half,top+.70))
    f.prism(field,-.035,.087,CAP,'Stepped crown coping')


def projecting_balcony(f,x,z,lod):
    f.box(x,z,2.41,.18,1.14,.36,CAP,'Projecting balcony slabs')
    for d in (.02,.85):
        if d>.5:f.box(x,z+.72,2.38,.063,.065,d,FRAME,'Balcony handrail')
    for a in (-1.13,1.13):
        f.box(x+a,z+.72,.065,.064,.89,.44,FRAME,'Balcony side rails')
    for u in np.linspace(-1.13,1.13,11 if not lod else 5):
        f.box(x+u,z+.40,.037,.65,.05,.85,FRAME,'Balcony guard uprights')
