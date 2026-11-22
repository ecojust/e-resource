"""The visible outside wall behind the garden arcade at 450 Jiaozhou Road.

The dark western entrance and pale boarded entrance are registered separately.
The central window's two visible jambs come from opposite views through the piers.
The render follows figure 13 for the height of the pale closing board.
"""
from shapely.geometry import box
from shapely.ops import unary_union

import garden_arcade as arcade

FACE = 'Rear porch | shaded red running bond'
FRAME = 'Rear porch | dark weathered joinery'
BEAD = 'Rear porch | worn edge of timber bead'
OPENING = 'Rear porch | unlit face behind entrance'
GLASS = 'Rear porch | charcoal blue reflective glazing'
GLASS_LIGHT = 'Rear porch | muted blue-grey glazing'
PANEL = 'Rear porch | pale ochre closing board'
SILL = 'Rear porch | dark masonry sill edge'

PALETTE = {key: {'color': arcade.linear(rgb), 'roughness': rough} for key,rgb,rough in (
    (FRAME,(56,49,44),.79),(BEAD,(77,67,54),.73),
    (OPENING,(39,41,37),.94),(GLASS,(55,66,67),.31),
    (GLASS_LIGHT,(65,77,77),.30),(PANEL,(132,108,89),.90),
    (SILL,(100,75,61),.90))}
# Front is at negative Y. Dimensions use the same 64-mm masonry courses as the arcade.
FRONT_Y = 3.72
WALL_BACK_Y = 4.20
WEST, EAST, TOP = .00, 10.70, 4.70
# The opening extends down to the outside landing at both doors.
WEST_DOOR = (1.17, 3.09, 0., 3.80)
WINDOW = (4.68, 6.58, 1.16, 3.80)
EAST_DOOR = (8.16, 10.23, 0., 3.97)


def _board(b, x0, x1, y0, y1, z0, z1, mat, name):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),
          (x1-x0,y1-y0,z1-z0), mat, label='Garden rear wall | '+name)


def _frame(b, bounds, front, width, label, has_bottom):
    l,r,z,h=bounds
    depth=.082
    _board(b,l,l+width,front,front+depth,z,h,FRAME,label+' west jamb')
    _board(b,r-width,r,front,front+depth,z,h,FRAME,label+' east jamb')
    _board(b,l+width,r-width,front,front+depth,h-width,h,FRAME,label+' head')
    if has_bottom:
        _board(b,l+width,r-width,front,front+depth,z,z+width,FRAME,label+' bottom rail')


def add_back_wall(builder, lod=False):
    """Build the exterior return from X=0 to 10.70 m. The next bay starts at that joint."""
    arcade.texture()
    builder.palette.update(PALETTE)
    # One original running-bond image serves both shaded porch and outer face.
    # Reduce the brightness moderately to reflect the covered brick's observed tone.
    builder.palette[FACE] = {**arcade.PALETTE[arcade.FACE], 'color': [.73,.65,.65]}
    far = lod is True or lod in ('lod','far','low','distant')
    holes=unary_union([box(l,z-.01 if z==0 else z,r,h) for l,r,z,h in (WEST_DOOR,WINDOW,EAST_DOOR)])
    shape=box(WEST,0.,EAST,TOP).difference(holes)
    builder.prism(shape,FRONT_Y-WALL_BACK_Y,0.,lambda x,z,d:(x,FRONT_Y-d,z),
                  FACE,'Garden rear wall | brickwork and three open reveals')
    arcade.material_uv(builder.parts[-1])

    l,r,z,h=WEST_DOOR
    _frame(builder,WEST_DOOR,3.747,.094,'western entrance',False)
    _board(builder,l,r,3.72,3.90,-.085,.012,SILL,'short western entrance threshold')
    _board(builder,l+.057,r-.057,3.819,3.86,.004,2.906,OPENING,'unlit western entrance')
    _board(builder,l+.062,r-.062,3.808,3.850,2.945,h-.068,GLASS,'western rectangular transom')
    _board(builder,l+.094,r-.094,3.740,3.845,2.868,2.977,FRAME,'western transom rail')
    if not far:
        _board(builder,l+.079,r-.079,3.731,3.752,2.900,2.926,BEAD,'western transom rail edge')
        _board(builder,l+.079,r-.079,3.731,3.752,h-.100,h-.074,BEAD,'western head edge')

    l,r,z,h=WINDOW
    _frame(builder,WINDOW,3.815,.082,'central window',True)
    _board(builder,l-.030,r+.030,3.671,3.871,z-.060,z+.006,SILL,'projecting masonry window sill')
    # The parked vehicle appears in the glass in the photographs. The original
    # model uses three neutral pane values and no pictorial reflection.
    rails=(l+.082,5.13,5.98,r-.082)
    for j,(x0,x1) in enumerate(zip(rails,rails[1:])):
        for k,(z0,z1) in enumerate(((z+.082,2.12),(2.12,h-.082))):
            mat=GLASS_LIGHT if j==1 and k==0 else GLASS
            # Glazing seats inside the timber rebate on all four edges.
            _board(builder,x0-.019,x1+.019,3.885,3.908,z0-.018,z1+.018,mat,f'central window pane {j+1}.{k+1}')
    for j,x in enumerate(rails[1:-1]):
        _board(builder,x-.018,x+.018,3.842,3.914,z+.082,h-.082,FRAME,f'central window vertical {j+1}')
    _board(builder,l+.082,r-.082,3.839,3.917,2.095,2.145,FRAME,'central window cross rail')

    l,r,z,h=EAST_DOOR
    # The main gallery paving stops at the rear wall. Complete the short
    # exposed threshold leading to the set-back board, so no ray sees a gap.
    _board(builder,l,r,3.72,4.20,-.095,.014,SILL,'threshold in the east recess')
    _frame(builder,EAST_DOOR,4.095,.091,'eastern boarded doorway',False)
    _board(builder,l+.091,r-.091,4.160,4.190,.018,h-.091,GLASS,'eastern shaded backing and transom')
    # Figure 13 shows the upper edge of the closing board much closer to the head
    # than figure 8. The model preserves the high-board state measured in figure 13.
    _board(builder,8.434,10.140,4.129,4.157,.018,3.806,PANEL,'plain pale closing board')
    _board(builder,l+.091,8.434,4.128,4.159,.019,3.806,FRAME,'recessed western edge of closing board')
    if not far:
        _board(builder,8.434,8.460,4.115,4.134,.018,3.806,BEAD,'narrow exposed board edge')
