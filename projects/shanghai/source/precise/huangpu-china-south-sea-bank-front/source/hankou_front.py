"""Central three bays at 110 Hankou Road, using the conservation team's 2023 photographs."""
from math import cos, pi, sin, tau
from pathlib import Path

from shapely.geometry import LineString, box
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import add_facade_lettering


WALL = 'warm buff washed stone'
TRIM = 'light carved buff stone'
GRANITE = 'gray granite'
DARK_STONE = 'weathered recess'
GLAZING = 'blue grey window glass'
STEEL = 'dark window bars'
GREEN = 'green bronze entrance frames'
BRASS = 'aged brass highlights'
PALETTE = {
    name: {'color': rgb, 'roughness': rough} for name, rgb, rough in [
        (WALL, [.64, .557, .465], .92), (TRIM, [.736, .651, .545], .87),
        (GRANITE, [.55, .536, .506], .89), (DARK_STONE, [.423, .355, .295], .93),
        (GLAZING, [.176, .23, .226], .41), (STEEL, [.183, .171, .143], .76),
        (GREEN, [.15, .227, .197], .69), (BRASS, [.615, .375, .172], .56)]}
AXES = (-6.60, -2.20, 2.20, 6.60)
BAYS = (-4.40, 0.0, 4.40)
WIDTH = 16.15
TOP = 16.55


def fluted_shaft(builder, x, y, lod):
    """Taper the flutes into the neck and foot. Each flute is cut into the solid profile."""
    grooves = 20
    samples = grooves * (3 if lod else 7)
    rings = [(5.84, .656, 0), (5.96, .659, .04), (6.13, .661, .068),
             (8.76, .647, .067), (14.71, .535, .05), (14.85, .534, .029), (14.94, .54, 0)]
    vertices = []
    for z, radius, inset in rings:
        for j in range(samples):
            t = tau * j / samples
            r = radius - inset * (1 - cos(grooves * t)) / 2
            vertices.append((x + r*cos(t), y + r*sin(t), z))
    faces = [tuple(reversed(range(samples))), tuple(range((len(rings)-1)*samples, len(rings)*samples))]
    for level in range(len(rings)-1):
        for j in range(samples):
            first = level * samples + j
            nxt = level * samples + (j + 1) % samples
            faces.append((first, nxt, nxt+samples, first+samples))
    builder.add(vertices, faces, TRIM, 'Giant order / tapered fluted shaft')


def giant_columns(builder, lod):
    segments = 16 if lod else 36
    for x in AXES:
        y = -1.00
        builder.box((x,y,5.35), (1.52,1.50,.18), GRANITE, label='Giant order / square plinth')
        builder.lathe((x,y),[(5.43,.745),(5.51,.745),(5.55,.70),(5.63,.726),
                            (5.72,.71),(5.76,.645),(5.83,.67),(5.87,.661)],
                      TRIM,segments,'Giant order / moulded bases')
        fluted_shaft(builder, x, y, lod)
        builder.lathe((x,y),[(14.92,.54),(15.00,.58),(15.05,.585),(15.071,.559),
                            (15.11,.589),(15.16,.59),(15.25,.663),(15.34,.73)],
                      TRIM,segments,'Giant order / Doric neck and echinus')
        builder.box((x,y,15.43),(1.58,1.58,.18),TRIM,label='Giant order / square abacus')


def entrance_piers(builder, lod):
    for axis in AXES:
        for offset in (-.437, .437):
            x, y = axis + offset, -1.32
            # The restoration close-up shows unfluted shafts, paired directly under the frieze.
            builder.lathe((x,y),[(.10,.356),(.18,.366),(.38,.37),(2.26,.337),
                                (3.64,.314),(3.68,.354),(3.73,.36),(3.81,.403),
                                (3.88,.423)],GRANITE,14 if lod else 28,'Entrance / paired Tuscan shaft')
            builder.box((x,y,3.932),(.88,.86,.104),GRANITE,label='Entrance / square capital slab')


def glazed_leaf_ornaments(face, x, lod):
    """Approximate paired raised gold ornaments visible on the restoration photograph."""
    outlines = []
    for center in (1.46, 2.47):
        # Pointed outline with a circular lower return and narrow side loops.
        silhouette = [(0, .31), (.045, .21), (.098, .165), (.112, .066),
                      (.09, -.014), (.068, -.145), (0, -.25),
                      (-.068, -.145), (-.09, -.014), (-.112, .066),
                      (-.098, .165), (-.045, .21), (0, .31)]
        outlines.append(LineString([(x+dx, center+dz) for dx,dz in silhouette]))
        if not lod:
            for side in (-1, 1):
                for low, high, width in ((-.15, .18, .05), (-.015,.13,.144)):
                    angles = [tau*i/12 for i in range(13)]
                    ring = [(x+side*width*(.58+.42*cos(t)),
                             center+(low+high)/2+(high-low)*sin(t)/2) for t in angles]
                    outlines.append(LineString(ring))
    outlines.append(LineString([(x,1.17),(x,2.79)]))
    front = unary_union([curve.buffer(.012 if lod else .009, quad_segs=2) for curve in outlines])
    face.prism(front,-.128,-.106,BRASS,'paired gilded openwork on closed door leaf')
    swag = LineString([(x-.205,.72),(x-.134,.67),(x,.653),(x+.134,.67),(x+.205,.72)])
    face.prism(swag.buffer(.022,quad_segs=2),-.14,-.115,BRASS,'lower gilt door swag')


def portal(face, x, index, lod):
    low, high, width = .11, 3.62, 2.43
    hole = box(x-width/2,low,x+width/2,high)
    face.prism(hole.buffer(.012,join_style=2),-.32,-.302,GLAZING,'entrance dark backing glass')
    inner = hole.buffer(-.11, join_style=2)
    face.prism(hole.difference(inner),-.273,-.196,GREEN,'entrance outer jambs')
    face.box(x,3.19,width-.10,.155,.09,-.208,GREEN,'overdoor transom')
    if index == 2:
        # The right entrance is open in the dated photo; represent only the recessed closure.
        face.box(x,1.66,.042,2.93,.072,-.247,STEEL,'glass entrance meeting stile')
    else:
        for sign in (-1, 1):
            xc = x + sign*.568
            face.box(xc,.55,1.05,.82,.11,-.20,GREEN,'framed solid lower door panel')
            face.box(xc,2.96,1.05,.10,.11,-.20,GREEN,'bronze top rail')
            for k in (-1,1):
                face.box(xc+k*.48,1.97,.075,2.10,.11,-.20,GREEN,'bronze leaf stile')
            glazed_leaf_ornaments(face, xc, lod)
    face.box(x,.072,width+.19,.118,.40,.01,GRANITE,'single low threshold')
    return hole


def window(face, x, z, height, level, lod):
    width = 2.37
    opening = box(x-width/2,z,x+width/2,z+height)
    face.window(opening, 3 if not lod else 2, 2, STEEL,False,GLAZING,'rectangular recessed street window')
    for side in (-1,1):
        face.box(x+side*1.295,z+height/2,.173,height+.12,.171,.042,TRIM,'narrow projecting jamb')
    face.box(x,z+height+.105,width+.46,.158,.31,.063,TRIM,'hood above rectangular window')
    if level < 2:
        bottom = z + height + .30
        panel = box(x-1.12,bottom,x+1.12,bottom+.49)
        face.prism(panel.difference(panel.buffer(-.066, join_style=2)),.022,.10,TRIM,'recessed rectangular spandrel border')
        # Raised corner bindings are visible in the conservation photographs.
        if not lod:
            for dx in (-1.09,1.09):
                for zz in (bottom+.075,bottom+.40):
                    face.box(x+dx,zz,.16,.12,.11,.117,TRIM,'raised corner stone')
    return opening


def cornice(builder,z,profiles,material,label):
    for rise,height,width,front,back in profiles:
        builder.box((0,(front+back)/2,z+rise),(width,back-front,height),material,label=label)


def facade(builder, lod=False):
    front=Facade(builder,(-WIDTH/2,0),(WIDTH/2,0),'Hankou front')
    holes=[portal(front,x,i,lod) for i,x in enumerate(BAYS)]
    for i,(z,h) in enumerate([(5.49,2.24),(8.88,2.29),(12.18,2.30)]):
        for x in BAYS:
            holes.append(window(front,x,z,h,i,lod))
    front.wall(0,16.29,holes,.52,WALL)
    entrance_piers(builder,lod)
    cornice(builder,0,[(4.016,.109,15.98,-1.99,.56),(4.36,.60,15.91,-1.94,.54),
                       (4.704,.116,16.05,-1.99,.54),(4.826,.145,16.33,-2.06,.54),
                       (4.985,.193,16.60,-2.14,.54),(5.15,.13,16.80,-2.21,.54),
                       (5.254,.095,16.94,-2.26,.54)],GRANITE,'Entrance / layered granite entablature')
    frieze=Facade(builder,(-7.99,-1.945),(7.99,-1.945),'Entrance frieze')
    for i in range(-6,7):
        frieze.box(i*1.18,4.35,.22,.445,.123,.038,GRANITE,'short vertical ornament')
        if not lod:
            for d in [-.065,.065]:
                frieze.box(i*1.18+d,4.35,.032,.39,.13,.059,DARK_STONE,'cut line in ornament')
    for i in range(-14,15):
        builder.box((i*.548,-2.085,4.784),(.297,.335,.13),GRANITE,label='Entrance / broad cornice dentils')
    giant_columns(builder,lod)
    cornice(builder,0,[(15.63,.23,16.04,-1.90,.54),(15.89,.316,16.08,-1.86,.54),
                       (16.138,.16,16.27,-2.00,.54),(16.337,.235,16.54,-2.13,.54),
                       (16.513,.115,16.75,-2.22,.54)],TRIM,'Upper / moulded cornice above original giant order')
    for j in range(-16,17):
        builder.box((j*.49,-1.961,16.188),(.263,.347,.145),TRIM,label='Upper / projecting dentils')
    if not lod:
        font=Path(__file__).parent/'fonts/HankouFrontSubset.otf'
        add_facade_lettering(frieze,'国家绿色发展基金',0,4.37,5.78,.30,.082,.105,BRASS,
                             label='entrance inscription',font=font)
