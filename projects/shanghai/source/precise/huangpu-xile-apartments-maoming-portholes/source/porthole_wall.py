"""Model the three glazed oculi and the shallow stack-bond cream facing between the bays."""
from math import cos, sin, tau
from shapely.geometry import Polygon, box
from shapely.ops import unary_union


def circle(x, z, radius, sides):
    return Polygon([(x + radius * cos(tau*i/sides), z + radius * sin(tau*i/sides))
                    for i in range(sides)])


def facade(builder, shape, y_front, y_back, material, label):
    if not shape.is_empty and shape.area > 1e-7:
        builder.prism(shape, -y_back, -y_front, lambda x,z,d: (x,-d,z), material, label)


def block(builder, x1, x2, y1, y2, z1, z2, mat, label):
    builder.box(((x1+x2)/2,(y1+y2)/2,(z1+z2)/2), (x2-x1,y2-y1,z2-z1), mat, label=label)


def circular_moulding(builder, z, profile, sides, mat, label):
    vertices = [(r*cos(tau*i/sides), y, z+r*sin(tau*i/sides))
                for r,y in profile for i in range(sides)]
    panels = []
    for j in range(len(profile)):
        following = (j+1) % len(profile)
        for i in range(sides):
            k = (i+1)%sides
            panels.append((j*sides+i,j*sides+k,following*sides+k,following*sides+i))
    builder.add(vertices,panels,mat,label)


def porthole(builder, z, floor, lod, d):
    n = 24 if lod else 56
    r, opening = d['outer_ring'], d['clear_ring']
    name = f'{floor}F street porthole'
    # The retaining moulding projects beyond the wall plane. Its inside edge is bevelled into the reveal.
    profile = [(r,0.017),(r,-0.037),(r-0.020,-0.061),(opening+0.012,-0.061),
               (opening,-0.047),(opening,0.053),(r-0.02,0.053)]
    circular_moulding(builder,z,profile,n,'Buff cast-stone ring',name+' moulded surround')
    circular_moulding(builder,z,[(opening,0.048),(opening,0.024),(opening-0.026,0.034),
                                 (opening-0.036,0.084),(opening-0.036,0.117),(opening,0.117)],
                      n,'Deep bronze sash',name+' circular sash')
    pane = circle(0,z,opening-0.032,n)
    facade(builder,pane,0.118,0.134,'Blue grey glass',name+' inset glazing')
    # Photographs show a square opening sash inside the round light, with narrow curved sidelights.
    left, right, head, foot = -0.312,0.290,z+0.288,z-0.311
    for x in [left,right]:
        facade(builder,pane.intersection(box(x-0.015,z-0.55,x+0.015,head)),
               0.064,0.110,'Deep bronze sash',name+' casement jamb')
    for h in [head,foot]:
        facade(builder,pane.intersection(box(-0.52,h-0.016,0.52,h+0.016)),
               0.061,0.110,'Deep bronze sash',name+' transom and sill')
    facade(builder,pane.intersection(box(left+0.02,foot+0.02,right-0.02,head-0.02)),
           0.109,0.116,'Casement reflection',name+' central light')
    if not lod:
        # A short reveal is visible around the sash when seen towards the south.
        circular_moulding(builder,z,[(opening-0.025,0.076),(opening-0.029,0.073),
                                     (opening-0.038,0.09),(opening-0.034,0.094)],
                          n,'Sash rebate',name+' inner bead')


def tile_courses(builder, rect, circles, d, lod):
    xmin, zmin, xmax, zmax = rect.bounds
    pitch = d['tile_pitch_z']
    rings = unary_union(circles)
    field = rect.difference(rings)
    if lod:
        # Preserve the visible horizontal graining of the face at distance as broad bands.
        step = pitch*3
        for j in range(int((zmax-zmin)/step)+1):
            z=zmin+j*step
            strip = field.intersection(box(xmin,z,xmax,min(z+0.012,zmax)))
            facade(builder,strip,-0.009,-0.003,'Tan mortar','Street pier grouped horizontal joints')
        return
    tones = ['Pale ochre tile','Honey buff tile','Old straw tile','Muted biscuit tile']
    column = 0
    x = xmin
    while x < xmax-0.02:
        row = 0
        z = zmin
        while z < zmax-0.02:
            x2=min(x+d['tile_pitch_x']-0.008,xmax)
            z2=min(z+pitch-0.008,zmax)
            tile=box(x,z,x2,z2)
            index=(11*column+17*row+row//5+column//3)%13
            mat=tones[0] if index<6 else tones[1] if index<9 else tones[2] if index<12 else tones[3]
            if not rings.intersects(tile):
                block(builder,x,x2,-0.012,0.0,z,z2,mat,'Street pier facing tiles')
            elif not rings.covers(tile):
                facade(builder,tile.difference(rings),-0.012,0.0,mat,'Street pier cut tiles at stone rings')
            row += 1
            z=zmin+row*pitch
        column += 1
        x=xmin+column*d['tile_pitch_x']


def street_pier(builder, lod, d):
    sides=24 if lod else 56
    panel=box(d['south_jamb'],d['slab_soffits'][0],d['bay_edge'],d['cap_soffit'])
    holes=[circle(0,z,d['clear_ring']+0.012,sides) for z in d['centres']]
    facade(builder,panel.difference(unary_union(holes)),0.0,d['wall_thickness'],
           'Pale ochre tile' if lod else 'Tan mortar','Street pier masonry with three cut openings')
    tile_courses(builder,panel,[circle(0,z,d['outer_ring']-0.035,sides) for z in d['centres']],d,lod)
    for floor,z in enumerate(d['centres'],2):
        porthole(builder,z,floor,lod,d)
