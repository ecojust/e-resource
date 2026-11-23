"""Paired cast door knockers, enamel address and visible call plate at No. 20.

Dimensions are in metres. Y increases into the courtyard. The source photographs
are external references. All meshes and inscription strokes below are authored.
"""
from math import cos, sin, tau

from shapely import affinity
from shapely.geometry import LineString, Point, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union


CAST = 'No. 20 gate | dark cast bronze'
RIDGE = 'No. 20 gate | rubbed bronze ridges'
HOLLOW = 'No. 20 gate | dark metal recess'
ENAMEL = 'No. 20 gate | teal enamel'
PAINT = 'No. 20 gate | cream enamel lettering'
ALLOY = 'No. 20 gate | grey call-plate frame'
GREY = 'No. 20 gate | smoked grey insert'
RED = 'No. 20 gate | small red indicator'


def finish(rgb, roughness, metallic=0):
    linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    return {'color': linear, 'roughness': roughness, 'metallic': metallic}


PALETTE = {
    CAST: finish((.31, .285, .263), .71, .45),
    RIDGE: finish((.42, .345, .262), .57, .54),
    HOLLOW: finish((.20, .188, .172), .8, .36),
    ENAMEL: finish((.125, .395, .375), .38, .1),
    PAINT: finish((.86, .847, .68), .43),
    ALLOY: finish((.56, .556, .548), .53, .39),
    GREY: finish((.34, .349, .357), .61, .20),
    RED: finish((.55, .24, .17), .45),
}


def plate(b, shape, y, thick, material, name):
    """Extrude a front-facing outline toward the viewer from its support."""
    parts = shape.geoms if shape.geom_type == 'MultiPolygon' else [shape]
    for piece in parts:
        b.prism(orient(piece, sign=1), 0., thick, lambda x, z, d: (x, y - d, z),
                material, 'No. 20 | ' + name)


def rounded(x, z, width, height, radius):
    return box(x-width/2+radius, z-height/2+radius,
               x+width/2-radius, z+height/2-radius).buffer(radius, quad_segs=4)


def oval(b, x, y, z, width, height, relief, material, name, count=24, scallop=0):
    """Capped cast relief with an oval perimeter and a gently convex face."""
    verts, faces = [], []
    profile = ((1., 0.), (1., .14), (.91, .54), (.65, .86), (.29, .98))
    for radius, depth in profile:
        for i in range(count):
            angle = tau * i / count
            wave = 1 + scallop * cos(12 * angle) * radius
            verts.append((x + width/2 * radius * wave * cos(angle), y - relief*depth,
                          z + height/2 * radius * wave * sin(angle)))
    faces.append(tuple(reversed(range(count))))
    for j in range(len(profile) - 1):
        for i in range(count):
            a, c = j * count + i, j * count + (i + 1) % count
            faces.append((a, c, c+count, a+count))
    tip = len(verts)
    verts.append((x, y-relief, z))
    for i in range(count):
        faces.append(((len(profile)-1)*count+i, (len(profile)-1)*count+(i+1)%count, tip))
    b.add(verts, faces, material, 'No. 20 | '+name)


def pendant(b, x, y, z, width, height, lod, label):
    """An open projecting hoop, thickest at its worn bottom grip."""
    n, sides = (28, 7) if lod else (52, 10)
    verts, faces = [], []
    for i in range(n):
        a = tau*i/n
        lower = (1-sin(a))/2
        r = (.0044 + .0032*lower**2) * width / .11
        for j in range(sides):
            v = tau*j/sides
            verts.append((x+(width/2+r*cos(v))*cos(a),
                          y-.015*lower+r*sin(v),
                          z+(height/2+r*cos(v))*sin(a)))
    for i in range(n):
        for j in range(sides):
            faces.append((i*sides+j, i*sides+(j+1)%sides,
                          ((i+1)%n)*sides+(j+1)%sides, ((i+1)%n)*sides+j))
    b.add(verts,faces,RIDGE,'No. 20 | '+label+' hanging hoop')


def cast_head(b, cx, y, cz, scale, lod, label):
    """Only the face shapes resolved in the frontal photograph are modelled."""
    n=16 if lod else 36
    def boss(x,dy,z,w,h,d,mat,part,scallop=0):
        oval(b,cx+x*scale,y+dy*scale,cz+z*scale,w*scale,h*scale,d*scale,
             mat,label+' '+part,n,scallop)
    boss(0,0,0,.135,.138,.014,CAST,'oval casting',.017 if not lod else 0)
    boss(0,-.007,.003,.123,.121,.014,CAST,'face ground')
    for side, eye in ((-1,'left'),(1,'right')):
        brow=[(.009,.009),(.020,.021),(.032,.025),(.046,.033)]
        points=[(cx+side*xx*scale,y-.021*scale,cz+zz*scale) for xx,zz in brow]
        b.tube(points,.007*scale,RIDGE,6 if lod else 10,label='No. 20 | '+label+' '+eye+' raised brow')
        boss(side*.032,-.017,.002,.029,.016,.006,HOLLOW,eye+' eye hollow')
        boss(side*.032,-.021,.001,.011,.009,.004,CAST,eye+' eye')
        boss(side*.027,-.017,-.018,.039,.027,.012,CAST,eye+' cheek')
        boss(side*.036,-.013,-.034,.019,.023,.012,RIDGE,eye+' mouth lug')
    boss(0,-.018,.009,.022,.051,.019,CAST,'nose bridge')
    boss(0,-.027,-.016,.029,.021,.014,RIDGE,'rounded nose')
    boss(0,-.018,-.034,.056,.018,.009,HOLLOW,'mouth below nose')
    pendant(b,cx,y-.029*scale,cz-.066*scale,.105*scale,.103*scale,lod,label)


# Original line lettering for the small address line. Each cell uses its own
# 0..10 square. The historical house number uses two broad, curved numerals.
TEXT = {
    '陕':[[(1,1),(1,9),(3.4,9),(2.3,6.4),(3.4,5.3),(3.4,3.7),(2.3,3.4)],
          [(4.2,8),(9.5,8)],[(4.2,6.7),(5,5.5)],[(8.8,6.8),(8,5.4)],
          [(3.7,4.8),(9.7,4.8)],[(6.6,9.5),(6.6,5.5),(6,3.5),(4,.7)],
          [(6.8,4.6),(7.6,2.8),(9.6,.9)]],
    '西':[[(.5,9),(9.5,9)],[(1.5,1.0),(1.5,6.9),(8.6,6.9),(8.6,1.0),(1.5,1.0)],
          [(4.2,8.9),(4.2,5.1),(3.6,4.0),(2.5,3.3)],
          [(6.3,8.9),(6.3,4.1),(6.8,3.7),(7.7,3.7)]],
    '南':[[(.6,8),(9.4,8)],[(5,9.6),(5,6.8)],[(1.5,1),(1.5,6.6),(8.7,6.6),(8.7,1),(7.5,1)],
          [(3.2,5.9),(4,4.9)],[(6.6,5.9),(5.7,4.9)],[(2.6,4.6),(7.6,4.6)],
          [(2.7,3.1),(7.5,3.1)],[(5.1,4.6),(5.1,1.25)]],
    '路':[[(.5,9),(3.9,9),(3.9,6.1),(.5,6.1),(.5,9)],[(2.4,6),(2.4,1.3)],
          [(2.4,4.2),(4,4.2)],[(.6,4.5),(.6,1.1),(4.2,2)],
          [(6.4,9.5),(4.8,7.0)],[(5.8,8.4),(9,8.4),(7.1,6.1),(5,5)],
          [(5.7,7.4),(7.6,5.9),(9.7,5)],[(5.2,4.1),(9.2,4.1),(9.2,.7),(5.2,.7),(5.2,4.1)]],
    '二':[[(1.8,7.3),(8.4,7.3)],[(.5,2.2),(9.6,2.2)]],
    '弄':[[(1,9),(9.1,9)],[(2,7.1),(8.1,7.1)],[(5,8.9),(5,5.3)],[(.6,5.3),(9.4,5.3)],
          [(.5,3.5),(9.6,3.5)],[(3.3,4.8),(3.1,2),(1.4,.4)],[(6.9,4.8),(6.9,.5)]],
}


def add_address(b, lod, centre_z):
    plate(b,rounded(0,centre_z,.280,.200,.0055),.0003,.0043,ENAMEL,'rounded teal address plate')
    digit_top = centre_z + .072
    digit_bottom = centre_z - .021
    two_top = digit_top - .0075
    two=LineString([(-.056,two_top-.021),(-.053,two_top-.014),(-.047,two_top-.005),
                    (-.038,two_top),(-.029,two_top-.0005),(-.022,two_top-.005),
                    (-.018,two_top-.013),(-.018,two_top-.023),(-.0215,two_top-.032),
                    (-.029,two_top-.044),(-.043,two_top-.064),(-.056,digit_bottom),
                    (-.015,digit_bottom)]).buffer(.0066,quad_segs=4,cap_style='flat',join_style='round')
    plate(b,two,-.0039,.0008,PAINT,'20 numeral two')
    centre=(.034,(digit_top+digit_bottom)/2)
    outline=Point(*centre).buffer(1,quad_segs=9 if lod else 15)
    outer=affinity.scale(outline,.026,.050,origin=centre)
    inner=affinity.scale(outline,.012,.036,origin=centre)
    plate(b,outer.difference(inner),-.0039,.0008,PAINT,'20 numeral zero')
    for i,glyph in enumerate('陕西南路二二二弄'):
        strokes=[LineString([(-.117+i*.0297+x*.00276,centre_z-.084+z*.00295)for x,z in path])
                 .buffer(.00165,cap_style='flat',join_style='bevel')for path in TEXT[glyph]]
        plate(b,unary_union(strokes),-.0039,.0008,PAINT,'address line '+str(i+1)+' '+glyph)


def add_hardware(b, lod=False, door_y=.12, *, pull_centres=None, pull_scale=1., plate_z=2.440):
    """Add the two visible castings and hoops, enamel plate, and exterior call plate.

    pull_centres gives the two medallion centres in X,Z on the final door plane.
    Defaults are rectified photo 06; the wall plaque and bell keep their own Y=0.
    """
    for name, material in PALETTE.items():
        b.palette.setdefault(name,material)
    centres = [(-.14339011,1.02710804),(.17056026,1.02858505)] if pull_centres is None else pull_centres
    for (cx,cz),label in zip(centres,('left pull','right pull'),strict=True):
        cast_head(b,cx,door_y,cz,pull_scale,lod,label)
    add_address(b,lod,plate_z)
    plate(b,rounded(.95753,.96860,.111,.157,.005),.002,.022,ALLOY,'rectangular call plate')
    plate(b,rounded(.95753,.96660,.083,.132,.003),-.019,.005,GREY,'inset grey face')
    plate(b,rounded(.95753,.99860,.064,.039,.002),-.022,.003,ALLOY,'small upper label window')
    plate(b,rounded(.95753,.99860,.033,.021,.0015),-.024,.002,GREY,'grey upper inset')
    plate(b,rounded(.95753,.94960,.060,.047,.0025),-.022,.003,HOLLOW,'lower dark insert')
    plate(b,Point(.99068,.91954).buffer(.0048,quad_segs=4),-.0248,.0028,RED,'red point on call plate')
