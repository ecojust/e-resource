"""Visible west return of the separate Lane 244 entrance on Nanchang Road.

Local X runs into the lane along the pictured wall, Y runs behind the plaster
and Z is measured above the local threshold. Dimensions and camera limitations
are documented in measurements/lane-244/photogrammetry.json.
"""
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union


def paint(rgb, roughness=.89, metal=0.):
    srgb = [c / 255 for c in rgb]
    linear = [c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4 for c in srgb]
    return dict(color=linear, roughness=roughness, metallic=metal)


LIME = 'Lane 244 | warm lime-plastered courses'
SILL = 'Lane 244 | dressed pale edge'
SEAM = 'Lane 244 | mortar at recessed courses'
BASE = 'Lane 244 | brown-grey stone plinth'
MOULD = 'Lane 244 | weathered plinth mouldings'
PIPE = 'Lane 244 | dull painted downpipes'
TIMBER = 'Lane 244 | dark timber window'
SASH = 'Lane 244 | rubbed timber sash'
GLASS = 'Lane 244 | smoked window glass'
GREEN = 'Lane 244 | dark green number plate'
WHITE = 'Lane 244 | off-white number paint'
IRON = 'Lane 244 | dark iron gate'
PAVING = 'Lane 244 | worn access paving'
PALETTE = {
    LIME: paint([198,184,157]), SILL: paint([185,175,154]), SEAM: paint([121,112,99]),
    BASE: paint([99,87,81]), MOULD: paint([119,108,100]), PIPE: paint([171,167,153],.79),
    TIMBER: paint([65,49,43]), SASH: paint([82,59,49]), GLASS: paint([54,53,50],.39),
    GREEN: paint([27,73,58],.63,.09), WHITE: paint([206,211,187],.71),
    IRON: paint([45,46,43],.76,.25), PAVING: paint([151,145,133]),
}


def front(u, z, depth):
    return (u, -depth, z)


def slab(b, shape, back, face, material, name):
    if shape.is_empty:
        return
    for part in getattr(shape, 'geoms', [shape]):
        if part.geom_type == 'Polygon' and part.area > .000001:
            b.prism(part, back, face, front, material, '244 | ' + name)


def piece(b, x0, x1, y0, y1, z0, z1, material, name):
    b.box(((x0+x1)/2, (y0+y1)/2, (z0+z1)/2),
          (x1-x0, y1-y0, z1-z0), material, label='244 | ' + name)


def plaster_and_base(b, lod):
    left, right = -.56, 1.73
    hole = box(.299, 1.583, .958, 2.522)
    wall = box(left, 0., right, 2.95)
    # The body crosses each horizontal groove. The front course surfaces stop at
    # the groove, including the two courses interrupted by the recessed sash.
    slab(b, wall.difference(hole), -.212, -.012, SEAM, 'continuous wall with window opening')
    heights = [.689, .978, 1.369, 1.738, 2.105, 2.511, 2.909]
    for i, (a, c) in enumerate(zip(heights, heights[1:])):
        face = box(-.274, a+.007, 1.392, c-.007).difference(hole)
        slab(b, face, -.014, .007, LIME, f'plaster course {i+1}')
    slab(b, box(-.274, 2.909, 1.392, 2.95), -.016, .006, LIME, 'plaster head course')
    for xa, xb in [(left,-.273),(1.392,right)]:
        slab(b, box(xa,.63,xb,2.95), -.015,.034, LIME, 'plain upright edge of return')
    slab(b, box(left,0.,right,.679), -.01,.053,BASE,'high dark stone foot')
    for i,(z0,z1,depth) in enumerate([(.035,.094,.082),(.575,.618,.074),(.618,.661,.086),(.661,.688,.100),(.688,.712,.064)]):
        slab(b,box(left,z0,right,z1),.046,depth,MOULD,f'plinth profile {i+1}')
    # Photographed rainwater pipe at the street edge and narrower pipe by the pier.
    for i,(x,r,top) in enumerate([(-.466,.039,2.94),(1.681,.027,2.91)]):
        radius_sides=8 if lod else 14
        b.tube([(x,-.093,.030),(x,-.093,top)],r,PIPE,radius_sides,label=f'244 | downpipe {i+1}')
        for z in [.40,1.95]:
            b.tube([(x,-.093,z),(x,-.093,z+.024)],r+.008,MOULD,radius_sides,label=f'244 | downpipe collar {i+1}')


def narrow_window(b, lod):
    outside = box(.297,1.581,.961,2.523)
    inner = box(.350,1.647,.920,2.465)
    slab(b,outside.difference(inner),-.105,-.016,TIMBER,'deep timber casing')
    sash = inner.buffer(-.018, join_style=2)
    slab(b,inner.difference(sash),-.091,-.052,SASH,'inset sash edge')
    # Two slender uprights outline the sash. The middle rail aligns with the
    # visible cross-rail in both independent 2015 winter images.
    x0,z0,x1,z1=sash.bounds
    midx,midz=.626,2.079
    for j,(xa,xb) in enumerate([(x0,midx-.012),(midx+.012,x1)]):
        for k,(za,zb) in enumerate([(z0,midz-.013),(midz+.013,z1)]):
            slab(b,box(xa,za,xb,zb),-.093,-.089,GLASS,f'window pane {j+1}.{k+1}')
    slab(b,box(midx-.012,z0,midx+.012,z1),-.090,-.048,TIMBER,'central window mullion')
    for xa,xb in [(x0,midx-.012),(midx+.012,x1)]:
        slab(b,box(xa,midz-.013,xb,midz+.013),-.090,-.044,SASH,'cross-rail')
    slab(b,box(.288,1.558,.974,1.594),-.019,.055,TIMBER,'projecting timber sill')
    # Head bow and terminal shoulders traced independently of the numbered plaque.
    profile=Polygon([(.262,2.507),(.268,2.556),(.303,2.572),(.340,2.567),
                     (.392,2.605),(.455,2.622),(.502,2.604),(.555,2.586),
                     (.783,2.567),(.912,2.588),(.987,2.558),(.979,2.505)])
    slab(b,profile,-.013,.070,TIMBER,'bowed window head and shoulders')
    if not lod:
        slab(b,box(.287,2.51,.965,2.526),.067,.079,SASH,'lip of the head moulding')


def painted_plate(b, lod):
    border = box(-.229,2.178,.224,2.389).buffer(.011,quad_segs=4 if lod else 9)
    slab(b,border,.008,.023,GREEN,'green lane plate')
    # Only the principal three figures from the sign are transcribed. They are
    # original vector strokes; the low-contrast subline is unlettered.
    digits=[[(.05,.73),(.23,.94),(.57,1.),(.86,.84),(.87,.58),(.09,.02),(.90,.02)],
            [(.67,.0),(.67,.99),(.03,.36),(.91,.36)],
            [(.67,.0),(.67,.99),(.03,.36),(.91,.36)]]
    for j,path in enumerate(digits):
        x=-.211+j*.063
        digit=LineString([(x+a*.049,2.282+c*.083) for a,c in path]).buffer(.0054,
              cap_style=1,join_style=1,quad_segs=3 if lod else 5)
        slab(b,digit,.0231,.0249,WHITE,f'painted lane number {j+1}')
    if not lod:
        for xa in [-.22,.217]:
            for za in [2.193,2.376]:
                b.box((xa,-.025,za),(.006,.004,.006),PIPE,label='244 | sign fixing')


def gate_and_threshold(b,lod):
    # A single visible leaf sits beside the west jamb. Its far edge and bar
    # shadows are distinct in 2015; only the portion in the source view is built.
    piece(b,1.73,2.60,.08,.32,.02,2.94,LIME,'return up to the inner gate')
    piece(b,2.13,2.65,-.047,.27,.02,2.90,SILL,'west gate pier')
    piece(b,2.095,2.688,-.078,.29,.02,.195,BASE,'pier foot')
    piece(b,2.080,2.692,-.091,.295,.195,.235,MOULD,'pier foot cap')
    start,end=-.884,-.041;left,right=2.647,2.692
    rails=[(.095,.135),(.658,.690),(1.254,1.291),(2.491,2.535)]
    for n,(a,c) in enumerate(rails):
        piece(b,left,right,start,end,a,c,IRON,f'gate crossbar {n+1}')
    for j in range(9):
        y=start+(end-start)*j/8
        width=.028 if j in (0,8) else .018
        piece(b,left+.009,right-.006,y-width/2,y+width/2,.087,2.539,IRON,
              f'gate upright {j+1}')
    for base in [.26,1.87]:
        b.tube([(2.64,-.046,base),(2.64,-.046,base+.107)],.020,IRON,
               6 if lod else 12,label='244 | gate hinge knuckle')
    # A narrow strip of the passage is visible between west wall and gate.
    floor=Polygon([(-.585,.015),(-.585,-.899),(2.712,-.899),(2.712,-.014),(1.64,.015)])
    b.prism(floor,-.055,.008,lambda x,y,z:(x,y,z),PAVING,'244 | threshold and passage edge')


def add_244(builder,lod=False):
    plaster_and_base(builder,lod)
    narrow_window(builder,lod)
    painted_plate(builder,lod)
    gate_and_threshold(builder,lod)
