"""The glazed east gable and its short north eave at 159 Yanqing Road.

Coordinates precede the assembly's uniform scale. The east wall faces -Y
and the north wall +X. A replacement base height translates all components.
"""
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from garden_finishes import IVORY_RENDER
from residence_materials import CLAY, LEAD, SHADE, SILL, finish

STEEL = 'Yanqing 159 | weathered graphite attic steel'
GLASS = 'Yanqing 159 | blue grey attic glass'
BOARD = 'Yanqing 159 | dark gable boarding'
GREEN = 'Yanqing 159 | dark green attic return sash'
PALETTE = {
    STEEL: finish((77,78,72), .71),
    GLASS: finish((93,108,115), .37),
    BOARD: finish((84,87,80), .86),
    GREEN: finish((55,73,65), .70),
}


def attic_outline(layout=None):
    options = layout or {}
    bottom = options.get('base_z', 5.27)
    return {
        'east_extent': [-2.70, 0.], 'north_extent': [0., 3.40],
        'base_z': bottom, 'gable_spring_z': bottom + 1.23,
        'east_eaves_x': [-2.86, .16], 'ridge_x': -1.39,
        'ridge_top_z': bottom + 2.31, 'roof_y': [-.17, 3.49],
    }


def attic_openings(layout=None):
    base = attic_outline(layout)['base_z']
    return {
        'east_glazed_band': (-2.60, base+.065, -.055, base+1.23),
        'north_paired_light': (1.11, base+.06, 1.87, base+.84),
        'north_end_light': (2.72, base+.06, 3.28, base+1.03),
    }


def add_corner_attic(b, lod=False, layout=None):
    dimensions = attic_outline(layout)
    base = dimensions['base_z']
    spring = dimensions['gable_spring_z']
    ridge_x = dimensions['ridge_x']
    left, right = dimensions['east_extent']
    front, back = dimensions['north_extent']
    low_x, high_x = dimensions['east_eaves_x']
    fore_y, back_y = dimensions['roof_y']
    ridge_z = dimensions['ridge_top_z']-.035
    holes = attic_openings(layout)
    for key, value in PALETTE.items():
        b.palette.setdefault(key,value)

    def east(x, z, outward):
        return x, -outward, z

    def north(y, z, outward):
        return outward, y, z

    def solid(profile, inside, outside, mapper, material, label):
        b.prism(profile,inside,outside,mapper,material,'159 northeast attic | '+label)

    def rectangular_light(bounds, mapper, columns, rows, material, label, alternating=False):
        u0,z0,u1,z1 = bounds
        jamb = .024
        panes = []
        x = u0+jamb
        stems = [(.026 if alternating and i%2==0 else .012) for i in range(1,columns)]
        clear = (u1-u0-2*jamb-sum(stems))/columns
        # The single east transom is above mid-height in both dated views.
        divisions = [z0+jamb]+[z0+(z1-z0)*v for v in rows]+[z1-jamb]
        for i in range(columns):
            for j,(a,c) in enumerate(zip(divisions,divisions[1:])):
                pane = box(x, a+(.006 if j else 0), x+clear, c-(.006 if j+2<len(divisions) else 0))
                panes.append(pane)
                solid(pane,-.026,-.017,mapper,GLASS,label+' glazing')
            x += clear + (stems[i] if i<len(stems) else 0.)
        solid(box(*bounds).difference(unary_union(panes)), -.037,-.003,mapper,material,
              label+' perimeter, mullions and transoms')

    east_hole = holes['east_glazed_band']
    north_holes = [holes['north_paired_light'],holes['north_end_light']]
    solid(box(left,base,right,spring).difference(box(*east_hole)), -.085,.0,east,
          BOARD,'east sill and end posts')
    solid(box(front,base,back,spring-.015).difference(unary_union([box(*h) for h in north_holes])),
          -.082,0.,north,IVORY_RENDER,'north cream wall with two openings')
    rectangular_light(east_hole,east,12,[.59],STEEL,'east six double lights',True)
    rectangular_light(north_holes[0],north,3,[.32,.66],GREEN,'first north light')
    rectangular_light(north_holes[1],north,2,[.54],GREEN,'partly screened north light')
    gable = Polygon([(left,spring),(right,spring),(ridge_x,ridge_z-.10)])
    solid(gable,-.09,.0,east,BOARD,'triangular boarded gable')
    if not lod:
        # Slender strips follow vertical lines visible on the triangular infill.
        for i in range(1,13):
            x = left + (right-left)*i/13
            strip = gable.intersection(box(x-.006,spring+.02,x+.006,ridge_z))
            if not strip.is_empty:
                solid(strip,0,.005,east,STEEL,'gable vertical joint')
    solid(box(left,base-.012,right+.012,base+.047),-.07,.044,east,SILL,'east sill lip')
    solid(box(front,base-.012,back,base+.047),-.05,.048,north,SILL,'north sill lip')
    # These unobtrusive closure planes meet the rest of the building.
    solid(box(front,base,back,spring-.015),left,left+.07,north,SHADE,'inner side closure')
    solid(Polygon([(left,base),(right,base),(right,spring),(ridge_x,ridge_z-.10),(left,spring)]),
          -back,-back+.07,east,SHADE,'rear cut')

    def chord(xa,za,xb,zb,thickness):
        return Polygon([(xa,za),(xb,zb),(xb,zb-thickness),(xa,za-thickness)])

    eave_z = spring+.025
    for ex in (low_x,high_x):
        top = chord(ex,eave_z,ridge_x,ridge_z,.074)
        solid(top,-back_y,-fore_y,east,CLAY,'pitched clay roof')
        underside = chord(ex,eave_z-.074,ridge_x,ridge_z-.074,.030)
        solid(underside,-back_y,-fore_y,east,IVORY_RENDER,'pale roof soffit')
        fascia = chord(ex,eave_z+.014,ridge_x,ridge_z+.014,.069)
        solid(fascia,-fore_y,-fore_y+.024,east,LEAD,'gable rake edge')
        if not lod:
            for t in (.20,.40,.60,.80):
                xa = ex+(ridge_x-ex)*t
                za = eave_z+(ridge_z-eave_z)*t
                xb = xa+.018*(ridge_x-ex)
                zb = za+.018*(ridge_z-eave_z)
                solid(chord(xa,za+.012,xb,zb+.012,.011),-back_y,-fore_y,east,
                      CLAY,'roof course lap')
    solid(box(fore_y,eave_z-.042,back_y,eave_z+.025),high_x,high_x+.027,north,
          LEAD,'north barge and drip')
    solid(box(fore_y,eave_z-.042,back_y,eave_z+.025),low_x-.027,low_x,north,
          LEAD,'inner eave edge')
    solid(Polygon([(ridge_x-.055,ridge_z-.014),(ridge_x,ridge_z+.035),
                   (ridge_x+.055,ridge_z-.014),(ridge_x,ridge_z-.035)]),
          -back_y,-fore_y,east,CLAY,'ridge cap')
