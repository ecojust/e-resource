"""Courtyard entrance recorded before conservation, in 2020 and again in 2024."""
import math

import numpy as np
import shapely
from shapely.geometry import LineString, Point, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening

STONE = 'carved pale stone'
JOINT = 'warm grey mortar'
BRICK = 'mauve facing brick'
DARK = 'smoked brown facing brick'
MID = 'grey facing brick'
TERRA = 'ochre plinth'
LIGHT = 'ivory stone cladding'
STEEL = 'blackened steel sash'
GLASS = 'cool blue-grey glazing'
RAIL = 'graphite railings'
ROOF = 'grey roof membrane'
PALETTE = {
    STONE: {'color': [.78, .755, .694], 'roughness': .81},
    LIGHT: {'color': [.83, .817, .763], 'roughness': .79},
    JOINT: {'color': [.495, .453, .426], 'roughness': .92},
    BRICK: {'color': [.431, .353, .342], 'roughness': .9},
    DARK: {'color': [.324, .281, .267], 'roughness': .88},
    MID: {'color': [.412, .389, .359], 'roughness': .90},
    TERRA: {'color': [.47, .409, .324], 'roughness': .86},
    STEEL: {'color': [.141, .157, .157], 'metallic': .46, 'roughness': .54},
    GLASS: {'color': [.211, .268, .287], 'metallic': .31, 'roughness': .32},
    RAIL: {'color': [.163, .155, .149], 'metallic': .49, 'roughness': .51},
    ROOF: {'color': [.355, .352, .319], 'roughness': .95},
}
HALF = 24.740526 / 2
TOWER = 2.56
PORTAL = 3.02
EAVES = 26.0
TOWER_TOP = 30.18
WING_WINDOW_ROWS = (4.80, 8.37, 11.96, 15.53, 19.10, 22.67)


def brick_bond(face, elevation, reduced):
    """Recess the mortar and punctuate the facing with the observed repeated dark headers."""
    step, rise = (.53, .26) if reduced else (.273, .137)
    parts = {m: ([], []) for m in (BRICK, DARK, MID)}
    shapely.prepare(elevation)
    for row, z in enumerate(np.arange(3.84, EAVES - .1, rise)):
        left = -face.length / 2
        while left < face.length / 2:
            x0 = max(-face.length / 2, left - (row % 2) * step / 2) + .009
            x1 = min(face.length / 2, left + step - (row % 2) * step / 2) - .009
            top = min(z + rise - .01, EAVES - .09)
            col = round((left + face.length / 2) / step)
            left += step
            if x1 <= x0 or top <= z:
                continue
            rect = box(x0, z, x1, top)
            if not elevation.covers(rect):
                continue
            mat = DARK if (row + 2 * col) % 7 == 0 else MID if (row + col) % 3 == 0 else BRICK
            vertices, faces = parts[mat]
            offset = len(vertices)
            vertices.extend(face.point(x, h, .015) for x, h in ((x0,z),(x1,z),(x1,top),(x0,top)))
            faces.append(tuple(range(offset, offset + 4)))
    for mat, (vertices, faces) in parts.items():
        if vertices:
            face.builder.add(vertices, faces, mat, face.label + '/staggered facing bricks')


def steel_window(face, aperture, columns, rows, label, sill=True):
    """Shallow steel casements and flat stone sills seen in the 2020 frontal photo."""
    x0,z0,x1,z1=aperture.bounds
    inner=aperture.buffer(-.063,join_style='mitre')
    bars=[]
    for x in np.linspace(x0,x1,columns+1)[1:-1]:
        bars.append(box(x-.024,z0,x+.024,z1))
    for z in np.linspace(z0,z1,rows+1)[1:-1]:
        bars.append(box(x0,z-.024,x1,z+.024))
    panes=inner.difference(unary_union(bars)) if bars else inner
    face.prism(aperture.buffer(.012,join_style='mitre'),-.34,-.32,GLASS,label+'/glass')
    frame=aperture.buffer(-.019,join_style='mitre').difference(panes)
    face.prism(frame,-.26,-.17,STEEL,label+'/steel casements')
    if sill:
        face.box((x0+x1)/2,z0-.047,x1-x0+.09,.094,.21,-.018,STONE,label+'/shallow sill')


def balustrade(face, z, depth, reduced):
    length = face.length - .10
    for up in (.12,.47,.89):
        face.line((-length / 2, z+up, depth), (length / 2,z+up,depth), .028, RAIL, 6, 'horizontal rails')
    for u in np.linspace(-length / 2, length / 2, 1 + round(length / (.65 if reduced else .25))):
        face.line((u,z+.07,depth), (u,z+.90,depth), .018, RAIL, 5, 'vertical balusters')


def wing(builder, side, reduced):
    start, end = (-HALF,-TOWER) if side < 0 else (TOWER,HALF)
    face = Facade(builder,(start,0),(end,0),'West brick bays' if side < 0 else 'East brick bays')
    spacing = face.length / 4
    positions = [(-1.5 + i)*spacing for i in range(4)]
    windows = []
    for index, bottom in enumerate(WING_WINDOW_ROWS):
        # In the eastern rail gallery four skinny lights replace the central ordinary pair.
        row = [(x,1.30) for x in positions]
        if side > 0 and index == 4:
            row = [(positions[0],1.30),(-1.58,.57),(-.55,.57),(.50,.57),(1.57,.57),(positions[-1],1.30)]
        windows.extend((opening(x,bottom,width,1.83), width) for x,width in row)
    base = [opening(x,.78,1.48,1.66) for x in positions if abs(x+(start+end)/2)>PORTAL+.52]
    face.wall(0,3.89,base,.5,TERRA)
    for pane in base:
        steel_window(face,pane,2,1,'plinth glazing')
    surface = face.wall(3.84,EAVES,[p for p,_ in windows],.50,JOINT)
    brick_bond(face,surface,reduced)
    for pane,width in windows:
        steel_window(face,pane,1 if width < .8 else 2,2,'steel windows')
        x0,z0,x1,z1=pane.bounds
        face.box((x0+x1)/2,z1+.085,width+.18,.14,.24,.04,STONE,'pale projecting lintels')
    face.beam(3.82,.14,.10,STONE,face.length,'plinth cap')
    face.beam(EAVES-.08,.16,.12,STONE,face.length,'pale parapet capping')
    face.beam(19.01,.19,.66,STONE,face.length,'continuous rail gallery')
    balustrade(face,19.09,.58,reduced)
    for x in np.linspace(-face.length/2+.15,face.length/2-.15,5):
        face.box(x,19.43,.19,.79,.56,.23,STONE,'gallery stone piers')
    face.line((side*spacing*.97,3.83,.082),(side*spacing*.97,EAVES-.32,.082),.036,RAIL,6,'exposed downpipe')


def joints(face, surface, bottom, ceiling, depth, reduced):
    """Stone courses stop at the edges of the glass or the arched opening."""
    step = .99 if reduced else .83
    for row,z in enumerate(np.arange(bottom+.42,ceiling,step)):
        cuts = surface.intersection(box(-face.length/2,z-.009,face.length/2,z+.009))
        if not cuts.is_empty:
            face.prism(cuts,depth-.005,depth+.007,JOINT,'fine ashlar bed joints')
        for x in np.arange(-face.length/2+.81+(row%2)*.68,face.length/2,1.42):
            cut = surface.intersection(box(x-.007,z,x+.007,min(z+step,ceiling)))
            if not cut.is_empty:
                face.prism(cut,depth-.003,depth+.006,JOINT,'offset stone joints')


def numbered_entrance(builder, reduced):
    face = Facade(builder,(-PORTAL,-1.26),(PORTAL,-1.26),'Number two entrance')
    aperture = opening(0,-.02,4.20,3.98,.47,18 if reduced else 36)
    light = opening(0,5.64,3.64,2.31)
    surface = face.wall(0,9.47,(aperture,light),.72,STONE)
    joints(face,surface,0,9.47,.009,reduced)
    steel_window(face,light,3,2,'recessed lobby window')
    # The 2020 front view shows the opening in deep shade, behind a segmental stone arch.
    inner = Facade(builder,(-PORTAL,.03),(PORTAL,.03),'Shaded recessed entry')
    door = opening(0,.04,3.06,3.04)
    inner.wall(0,4.05,(door,),.31,TERRA)
    steel_window(inner,door,2,1,'recessed entrance leaves',False)
    for x in (-PORTAL+.10,PORTAL-.10):
        builder.box((x,-.72,4.67),(.20,1.38,9.34),STONE,label='Entrance/wing returns')
    builder.box((0,-.91,9.44),(2*PORTAL,1.05,.17),STONE,label='Entrance/stone rail platform')
    balustrade(face,9.52,.025,reduced)
    disc = Point(0,4.62).buffer(.375,quad_segs=12 if reduced else 24)
    face.prism(disc,-.004,.095,RAIL,'dark edge of circular number plaque')
    face.prism(disc.buffer(-.033),.09,.11,LIGHT,'ivory circular number plaque')
    number = LineString([(-.115,4.714),(-.092,4.760),(-.038,4.784),(.054,4.781),(.106,4.750),(.119,4.70),(.104,4.655),(.070,4.621),(-.103,4.47),(.118,4.47)]).buffer(.023,quad_segs=3)
    face.prism(number,.1105,.125,RAIL,'raised numeral 2')


def central_tower(builder, reduced):
    face = Facade(builder,(-TOWER,-.30),(TOWER,-.30),'Ivory stair tower')
    lower = 9.43
    slots = [opening(x,z,.62,2.05) for z in (11.00,14.71,18.45) for x in (-.78,0,.78)]
    square = [opening(x,27.79,.81,1.18) for x in (-1.83,1.83)]
    vent = opening(0,22.07,.48,.73)
    surface=face.wall(lower,TOWER_TOP,[*slots,*square,vent],.62,LIGHT)
    joints(face,surface,lower,TOWER_TOP,.008,reduced)
    for sh in slots:
        steel_window(face,sh,1,2,'three recessed stair lights',False)
    for sh in square:
        steel_window(face,sh,2,2,'upper paired lights',False)
    steel_window(face,vent,1,1,'single square tower vent',False)
    for u in (-1.29,-.39,.39,1.29):
        face.box(u,15.55,.080,11.92,.15,.037,STONE,'stair light vertical fillets')
    # A shallow projecting brow with dated photographic evidence of small dark recesses.
    face.box(0,21.24,2.94,.49,.80,.29,STONE,'projected stone brow')
    for x in np.linspace(-.95,.95,7):
        face.box(x,21.26,.082,.14,.034,.709,RAIL,'recesses in brow')
    for x in (-.50,.50):
        face.box(x,26.47,.105,7.31,.14,.060,STONE,'central tower ribs')
    for x in (-TOWER+.065,TOWER-.065):
        builder.box((x,.61,(TOWER_TOP+lower)/2),(.13,1.92,TOWER_TOP-lower),LIGHT,label='Tower/short side returns')
    builder.box((0,.60,TOWER_TOP-.065),(TOWER*2,1.93,.13),STONE,label='Tower/flat crown')
    builder.tube([(0,.62,TOWER_TOP),(0,.62,TOWER_TOP+1.95)],.033,RAIL,7,'Tower/flagstaff')


def add_geometry(builder,reduced):
    for side in (-1,1):
        wing(builder,side,reduced)
        x=side*(HALF-.07)
        builder.box((x,.90,EAVES/2),(.14,1.8,EAVES),JOINT,label='Street wings/shallow section end')
    numbered_entrance(builder,reduced)
    central_tower(builder,reduced)
    builder.box((0,.96,EAVES-.10),(HALF*2,1.84,.20),ROOF,label='Courtyard elevation/short roof return')
