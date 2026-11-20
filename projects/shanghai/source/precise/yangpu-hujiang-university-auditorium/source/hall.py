"""The southeast long hall within the two-wing Hu-chiang University complex."""
import json
import math
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade
from tracery import (BASE, BRICK, FRAME, JOINT, RIDGE, STONE, TILE,
                     gable_lights, recessed_portal, rectangle, roundel, twin_lancet)

PARAMS = json.loads(Path(__file__).with_name('parameters.json').read_bytes())
LENGTH = PARAMS['length_m']
HALF = PARAMS['gable_width_m'] / 2
EAVE = PARAMS['building_height_m']['eaves']
APEX = PARAMS['building_height_m']['gable_apex']
BELT = PARAMS['building_height_m']['lower_belt']
RIDGE_H = PARAMS['building_height_m']['roof_ridge']


def wall(f, silhouette, holes, lod):
    masonry = f.wall(0,APEX,holes,.35,BRICK,outline=silhouette)
    plinth = masonry.intersection(box(-f.length/2,0,f.length/2,.38))
    f.prism(plinth,-.14,.095,BASE,'exposed foundation')
    f.beam(BELT,.19,.145,STONE)
    f.beam(BELT+.15,.09,.09,STONE)
    if not lod:
        # Bed joints remain visible as shadowed horizontal brick courses at close range.
        bands = [box(-f.length/2,z-.008,f.length/2,z+.008) for z in np.arange(.50,APEX,.157)]
        bed = masonry.intersection(unary_union(bands))
        f.prism(bed,.0008,.0038,JOINT,'brickwork courses')


def gable(f, lod, northeast):
    width = f.length / 2
    holes = [gable_lights(f,lod,PARAMS),recessed_portal(f,lod,PARAMS)]
    for sign in (-1,1):
        holes.append(rectangle(f,sign*6.52,.82,1.08,2.84,lod,1))
        holes.append(rectangle(f,sign*6.49,5.79,.99,4.60,lod,1))
    holes.append(rectangle(f,0,16.73,.57,1.33,lod,1))
    shape = Polygon([(-width,0),(width,0),(width,EAVE),(0,APEX),(-width,EAVE)])
    wall(f,shape,holes,lod)
    rake = LineString([(-width+.08,EAVE+.03),(0,APEX-.03),(width-.08,EAVE+.03)])
    f.prism(rake.buffer(.104,cap_style=2,join_style=2),-.31,.139,STONE,'pale gable rake')
    # The archive view resolves a second, smaller inset immediately below the apex.
    if northeast:
        f.box(0,18.83,.35,.42,.072,.012,STONE,'small upper gable stone')
    f.box(0,16.62,.86,.105,.32,.056,STONE,'vent lintel mould')


def buttress(f, u):
    f.box(u,6.99,.37,13.64,.30,.050,BRICK,'brick wall pilaster')
    f.box(u,13.19,.49,1.28,.46,.105,STONE,'stone eave corbel')
    shoulder = Polygon([(u-.265,13.81),(u+.265,13.81),(u+.265,14.04),
                        (u,14.32),(u-.265,14.04)])
    f.prism(shoulder,-.13,.30,STONE,'sloped pilaster cap')


def long_wall(f, lod, southeast):
    holes = []
    if southeast:
        # The first two upper bays are oculi; repeat the exposed pointed bays beyond them.
        y_positions = [3.11,8.12,13.42,18.76,24.10,29.44,34.36]
        for number, y in enumerate(y_positions):
            u = LENGTH/2-y
            holes.append(rectangle(f,u,.80,2.73,2.49,lod,3))
            holes.append(roundel(f,u,lod) if number < 2 else twin_lancet(f,u,lod))
        pilasters = [0,5.62,10.77,16.09,21.43,26.77,32.12,37.2]
        for y in pilasters:
            buttress(f, LENGTH/2-y if 0 < y < LENGTH else math.copysign(LENGTH/2-.14,LENGTH/2-y))
    else:
        # Only the three exposed western bays remain outside the joint to the White Chapel.
        for y in [21.49,27.64,33.91]:
            u = y-LENGTH/2
            holes.append(rectangle(f,u,.80,2.73,2.49,lod,3))
            holes.append(twin_lancet(f,u,lod))
        for y in [18.65,24.62,30.75,36.92]:
            buttress(f,y-LENGTH/2)
    wall(f,box(-LENGTH/2,0,LENGTH/2,EAVE),holes,lod)
    f.beam(EAVE-.04,.13,.121,STONE)


def roof(b, lod):
    # Give each rake a real, closed tile slab. Main roof lies beneath the two masonry gables.
    half_eaves = HALF+.19
    for sign in (-1,1):
        underside = EAVE-.18
        cross = Polygon([(0,RIDGE_H-.22),(sign*half_eaves,underside),
                         (sign*half_eaves,underside+.19),(0,RIDGE_H)])
        b.prism(cross,.15,LENGTH-.15,lambda x,z,d:(-x,d,z),TILE,'Roof/pitched tile slab')
        dz = RIDGE_H-(underside+.19)
        for i in range(1,16 if lod else 37):
            ratio = i/(16 if lod else 37)
            x = -sign*ratio*half_eaves
            z = RIDGE_H-ratio*dz+.020
            b.box((x,LENGTH/2,z),(.092,LENGTH-.44,.060),RIDGE,label='Roof/course lip')
    b.tube([(0,.18,RIDGE_H+.03),(0,LENGTH-.18,RIDGE_H+.03)],
           .143,RIDGE,8 if lod else 12,'Roof/ridge tiles')


def model(b, lod):
    plan = box(-HALF,0,HALF,LENGTH)
    b.plan_prism(plan,0,.105,BASE,'Ground/hall plinth')
    gable(Facade(b,(-HALF,0),(HALF,0),'Northeast gable'),lod,True)
    gable(Facade(b,(HALF,LENGTH),(-HALF,LENGTH),'Southwest gable'),lod,False)
    long_wall(Facade(b,(-HALF,LENGTH),(-HALF,0),'Southeast wall'),lod,True)
    long_wall(Facade(b,(HALF,0),(HALF,LENGTH),'Northwest wall'),lod,False)
    roof(b,lod)
    assert all(len(part['label'].encode('utf-8')) <= 63 for part in b.parts)
