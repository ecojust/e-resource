"""The short Hengshan frontage, the north corner and 50 m east street face in metres."""

import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening

PARAMETERS = json.loads(Path(__file__).with_name('parameters.json').read_text())
WALL = 'warm ochre roughcast'
TRIM = 'ivory cement'
ROSE = 'pale modeled flower plaster'
BASE = 'cool stone plinth'
GLASS = 'blue gray street glazing'
WOOD = 'dark painted window frames'
IRON = 'deep green metal'
SHADE = 'recessed vestibule'
PALETTE = {
    WALL: {'color': [.61, .435, .29], 'roughness': .88},
    TRIM: {'color': [.83, .78, .67], 'roughness': .76},
    ROSE: {'color': [.91, .865, .76], 'roughness': .83},
    BASE: {'color': [.31, .325, .32], 'roughness': .83},
    GLASS: {'color': [.19, .26, .30], 'roughness': .36, 'metallic': .08},
    WOOD: {'color': [.09, .115, .115], 'roughness': .61},
    IRON: {'color': [.072, .129, .106], 'roughness': .61},
    SHADE: {'color': [.115, .133, .125], 'roughness': .95},
    'shop glazing': {'color': [.174, .213, .224], 'roughness': .32},
    'roof coping': {'color': [.57, .53, .45], 'roughness': .85},
    'roof bitumen': {'color': [.345, .335, .31], 'roughness': .91},
    'section wall': {'color': [.40, .38, .345], 'roughness': .91},
    'address plate green': {'color': [.06, .23, .135], 'roughness': .47},
    'address enamel white': {'color': [.95, .92, .80], 'roughness': .46},
}
SHOP = PARAMETERS['shop_and_lobby_m']
PITCH = PARAMETERS['storey_height_m']
TOP = PARAMETERS['wing_roof_m']
CROWN = PARAMETERS['tip_crown_m']
DEPTH = PARAMETERS['slice_depth_m']
DOOR = PARAMETERS['gao_an_gate_offset_m']


def unit(a):
    return a / np.linalg.norm(a)


def section_lines():
    """Street line, then the common mitred offsets on the building side of each corner."""
    source=np.array(PARAMETERS['frame']['frozen_local_m'])
    west, right, _, left, east=source[:5]
    west=right+unit(west-right)*PARAMETERS['hengshan_corner_length_m']
    # A shallow flat chamfer approximates the curved northern face recorded as two short edges.
    outer=np.array([east,left+[0,-.44],right+[0,-.44],west])
    tangents=[unit(v) for v in np.diff(outer,axis=0)]
    normals=[np.array([-v[1],v[0]])for v in tangents]
    miters=[normals[0]]
    for a,b in zip(normals,normals[1:]):
        half=unit(a+b);miters.append(half/np.dot(half,a))
    miters.append(normals[-1])
    return outer,np.array(miters)


def section_footprint(depth=DEPTH, street_overhang=0):
    outer,miters=section_lines()
    return Polygon([*(outer-street_overhang*miters),*reversed(outer+depth*miters)])


def wall(f, miters, holes):
    """Use a common inner corner at each junction to avoid superposed exterior triangles."""
    left,right=miters
    def point(u,z,d):
        t=(u+f.length/2)/f.length
        p=f.point(u,z)
        p[:2]-=d*((1-t)*left+t*right)
        return p
    bounds=box(-f.length/2,0,f.length/2,TOP)
    f.builder.prism(bounds.difference(unary_union(holes)),-.35,0,point,WALL,f.label+'/pier and spandrel wall')


def sash(f,u,z,w,h,leaves=2,transoms=True,depth=0,label='street casement',glass=GLASS):
    x0=u-w/2;x1=u+w/2
    pane=box(x0,z,x1,z+h)
    f.prism(pane.buffer(.007,join_style='mitre'),depth-.225,depth-.204,glass,label+'/glazing')
    inner=pane.buffer(-.080,join_style='mitre');bars=[]
    for j in range(1,leaves):
        x=x0+j*w/leaves;bars.append(box(x-.023,z,x+.023,z+h))
    if transoms:
        bars.append(box(x0,z+h*.72-.022,x1,z+h*.72+.022))
    cage=pane.buffer(-.014,join_style='mitre').difference(inner.difference(unary_union(bars)))
    f.prism(cage,depth-.18,depth-.103,WOOD,label+'/frames')
    f.box(u,z-.043,w+.085,.08,.16,.014+depth,TRIM,label+'/sill')


def oriel(f,u,z,w,h,storey,depth=.62,label='oriel'):
    """Three glazed planes and an independent solid spandrel return into the true opening."""
    cut=w*.19
    line=[(-w/2,-.085),(-w/2+cut,depth),(w/2-cut,depth),(w/2,-.085)]
    pts=[f.point(u+v,0,d)[:2]for v,d in line]
    # The back of the projecting sill intersects the wall inside its recess.
    poly=Polygon(pts+[f.point(u+w/2,0,-.12)[:2],f.point(u-w/2,0,-.12)[:2]])
    bottom=SHOP+.13 if storey==0 else z-(PITCH-h)
    f.builder.plan_prism(poly,bottom,z,WALL,label=f.label+'/'+label+'/spandrel')
    f.builder.plan_prism(poly.buffer(.055,join_style='mitre'),z-.105,z-.038,TRIM,label=f.label+'/'+label+'/white drip')
    for i,(a,b)in enumerate(zip(pts,pts[1:])):
        side=Facade(f.builder,a,b,f.label+'/'+label+('/front' if i==1 else '/splay'))
        aperture=opening(0,z+.10,side.length-.14,h-.18)
        side.prism(box(-side.length/2,z,side.length/2,z+h).difference(aperture),-.12,0,WALL,'narrow joinery reveals')
        sash(side,0,z+.10,side.length-.14,h-.18,2 if i==1 else 1,True,.055,'sash')
    if storey==0:
        for j in range(3):
            nested=poly.buffer(-.13*(2-j),join_style='mitre')
            f.builder.plan_prism(nested,bottom-.50+j*.16,bottom-.32+j*.16,WALL,label=f.label+'/'+label+'/stepped underside')
    if storey==9:
        f.builder.plan_prism(poly,z+h,z+h+.11,'roof coping',label=f.label+'/'+label+'/top closure')


def flowers(f,u,z,width,height,lod,panel='spandrel'):
    edge=[(-.45,0),(-.29,.14),(-.36,.28),(-.50,.38),(-.42,.48),(-.50,.62),(-.38,.75),(-.36,.88),(-.46,1)]
    v=[(u+x*width,z+y*height)for x,y in edge]
    poly=Polygon(v+[(2*u-x,y)for x,y in reversed(v)])
    if panel=='lintel':
        poly=box(u-width/2,z,u+width/2,z+height)
        label='48/rectangular entrance relief'
    elif panel=='crown':label='corner/crown relief'
    else:label='48/waisted floral spandrel'
    f.prism(poly,-.014,.042,TRIM,label+'/plaster panel')
    # Coiled rosettes with shallow petals, individually modelled from the district detail photograph.
    for px,py,r in [(-.19,.73,.17),(.13,.86,.14),(.07,.52,.19),(-.17,.32,.15),(.16,.15,.14)]:
        rr=r*min(width,height*1.65);ox=u+px*width;oz=z+py*height
        sides=15 if lod else 35
        spiral=[]
        for j in range(sides+1):
            t=(j/sides)*math.tau*1.48;rad=rr*(.085+.77*j/sides)
            spiral.append((ox+rad*math.cos(t),oz+rad*.77*math.sin(t)))
        ridge=LineString(spiral).buffer(.020 if lod else .023,quad_segs=2 if lod else 5)
        f.prism(ridge,.041,.090,ROSE,label+'/rose coils')
        if not lod:
            for angle in (-.8,1.35,2.9):
                leaf=Polygon([(ox+rr*math.cos(angle+t)*s,oz+rr*math.sin(angle+t)*s*.64)for t,s in [(0,.68),(.29,.93),(0,1.17),(-.29,.92)]])
                f.prism(leaf,.042,.071,ROSE,label+'/leaf tips')


def number_plate(f,u,z,lod):
    f.box(u,z,.39,.25,.05,.035,'address plate green','48/green address plate')
    four=[[(0,.16),(0,.02)],[(0,.16),(-.084,.078),(.026,.078)]]
    eight=[[(.058,.088),(.026,.12),(.042,.153),(.09,.154),(.107,.117),(.058,.088),(.025,.061),(.038,.03),(.091,.027),(.111,.059),(.058,.088)]]
    for letter,dx in [(four,-.043),(eight,.006)]:
        for line in letter:
            shape=LineString([(u+x+dx,z+y-.086)for x,y in line]).buffer(.009,quad_segs=2)
            f.prism(shape,.061,.070,'address enamel white','48/address digits')


def door(f,u,lod):
    w=2.43;h=2.25
    f.box(u,h/2,w,h,.12,-1.05,SHADE,'48/vestibule rear')
    for sign in [-1,1]:
        f.box(u+sign*.59,h*.5,1.17,h,.075,-.94,IRON,'48/two green street door leaves')
        for j in range(4 if lod else 8):
            f.box(u+sign*(.10+j*(.90/(3 if lod else 7))),h*.5,.028,h*.78,.044,-.874,WOOD,'48/door strips')
    for side in [-1,1]:
        f.box(u+side*1.245,1.43,.13,2.86,1.10,-.53,TRIM,'48/deep vestibule jamb')
        for off in (1.43,1.92,2.47):
            f.box(u+side*off,1.66,.205,3.32,.18,.04,TRIM,'48/vertical entrance piers')
    f.box(u,3.24,5.38,.26,1.25,.455,TRIM,'48/canopy slab')
    for width,top in ((5.20,3.69),(4.32,4.02),(3.43,4.36),(2.46,4.72),(1.52,5.03),(.50,5.30)):
        for sign in (-1,1):
            f.box(u+sign*(width/2-.12),(top+3.38)/2,.24,top-3.38,.24,.045,TRIM,'48/stepped Deco frame uprights')
        # Short links between adjacent uprights keep the recessed cement panels visible.
        if width>.51:
            for sign in [-1,1]:
                f.box(u+sign*(width/2-.27),top-.07,.54,.14,.23,.045,TRIM,'48/stepped header')
        else:f.box(u,top-.07,.51,.14,.23,.045,TRIM,'48/central header')
    flowers(f,u,2.25,2.34,.89,lod,'lintel')
    number_plate(f,u-1.17,1.72,lod)


def crown(f,lod):
    heights=[1.03,1.55,2.14,2.74,3.23,2.74,2.14,1.55,1.03]
    for i,rise in enumerate(heights):
        u=(i-4)*.476
        f.box(u,TOP+rise*.5,.46,rise,.47,.015,TRIM,'corner/stepped crown fins')
        f.box(u,TOP+.51,.18,1.03,.08,.279,WALL,'corner/shadow channels')
    f.box(0,TOP+.035,4.63,.16,.61,.022,TRIM,'corner/crown foot')
    # Central plaque is recessed between the pale vertical fins seen from the junction.
    f.box(0,TOP+.96,1.00,.72,.085,.317,WALL,'corner/crown plaque')
    flowers(f,0,TOP+.68,.64,.57,lod,'crown')


def build_side(f,miter,kind,lod):
    east=kind=='east';front=kind=='tip'
    openings=[];pending=[]
    def add(u,z,width,height,style):
        openings.append(opening(u,z,width,height));pending.append((u,z,width,height,style))
    def along(distance):
        return f.length/2-distance if east else -f.length/2+distance
    if east:
        sequence=[(2.32,'flat'),(5.59,'oriel'),(9.11,'flat'),(12.86,'oriel'),(16.42,'flat'),(20.03,'flat'),(23.71,'oriel'),(26.98,'oriel'),(DOOR,'rose'),(35.82,'oriel'),(39.05,'flat'),(42.25,'oriel'),(45.52,'flat'),(48.37,'flat')]
    elif front:sequence=[(-2.91,'small'),(0,'center'),(2.91,'small')]
    else:sequence=[(2.29,'flat'),(5.64,'oriel'),(9.00,'flat'),(12.58,'oriel'),(15.82,'flat')]
    for loc,style in sequence:
        u=loc if front else along(loc)
        for i in range(10):
            z=SHOP+i*PITCH+.70;h=1.54 if style=='small' else 1.66
            projected=(style=='oriel' or style=='center') and i<8
            width=(.94 if style=='small' else 2.81 if style=='center' else 2.28 if style=='oriel' else 1.57 if style=='rose' else 1.40)
            if style=='rose' and i==0:z+=.83;h-=.83
            add(u,z,width,h,('oriel',i)if projected else 'flat')
            if projected and i==7:pending.append((u,z+h,width,.08,'oriel cap'))
            if style=='rose' and i>0:flowers(f,u,z-1.16,1.46,1.04,lod)
    if front:
        for u in [-2.78,0,2.78]:add(u,.34,2.44,2.70,'shop')
    elif east:
        for dist,style in sequence:
            if style=='rose':continue
            if abs(dist-DOOR)<3.55:continue
            add(along(dist),1.05,1.08 if style=='flat' else 1.40,1.36,'low')
        openings.append(opening(along(DOOR),0,2.45,2.85))
    else:
        for dist in [1.72,4.40,7.24,14.6,17]:add(along(dist),.37,1.84,2.52,'shop')
        # Simplified shopfront recess on the photographed corner return; other numbered entrances remain outside the study.
        openings.append(opening(along(10.72),0,2.22,2.68))
    wall(f,miter,openings)
    for u,z,w,h,style in pending:
        if isinstance(style,tuple):
            oriel(f,u,z,w,h,style[1],.67 if front else .62)
        elif style=='oriel cap':
            f.box(u,z+h/2,w+.07,h,.66,.23,'roof coping','upper oriel termination')
        elif style=='shop':
            sash(f,u,z,w,h,2,True,label='corner commercial glazing',glass='shop glazing')
        else:sash(f,u,z,w,h,1 if w<1.1 else 2,style!='low',label='upper flat casements' if style=='flat' else 'ground casements')
    ground=box(-f.length/2+.042,0,f.length/2-.042,.76).difference(unary_union(openings))
    f.prism(ground,-.012,.030,BASE,'cool low plinth')
    f.beam(TOP-.09,.18,.12,'roof coping',width=f.length-.10,label='roof parapet coping')
    if east:door(f,along(DOOR),lod)
    else:
        f.beam(3.52,.56,.24,TRIM,width=f.length-.08,label='commercial fascia')
        if not front:f.box(along(10.72),1.33,2.19,2.66,.10,-.58,SHADE,'Hengshan corner/shadowed shop entrance')
    if front:crown(f,lod)


def add_apartment(b,lod):
    outer,miters=section_lines()
    names=['Gaoan facade','north corner','Hengshan return']
    for i,k in enumerate(['east','tip','west']):
        face=Facade(b,outer[i],outer[i+1],names[i])
        build_side(face,miters[i:i+2],k,lod)
    section=section_footprint()
    b.plan_prism(section,.02,.095,'section wall',label='section/low base')
    b.plan_prism(section,TOP-.21,TOP-.08,'roof bitumen',label='section/flat roof strip')
    inner=outer+DEPTH*miters
    for i in range(len(outer)-1):
        f=Facade(b,inner[i+1],inner[i],'section/interior cut')
        f.wall(.025,TOP-.18,thickness=.11,material='section wall')
    for i,label in ((0,'Gaoan Road end cut'),(-1,'Hengshan Road end cut')):
        f=Facade(b,outer[i],inner[i],'section/'+label)
        f.wall(.025,TOP-.17,thickness=.11,material='section wall')
