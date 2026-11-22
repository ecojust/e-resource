"""Window aprons at the curved corner of the former German Post Office, Shanghai."""
from math import sin, cos, pi
RADIUS = 2.12
PANELS = [(-.99, -.50, 9), (-.32, .32, 13)]
PIERS = [(-1.08, -.99), (-.50, -.32), (.32, .43)]

def swatch(rgb):
    c = [x / 255 for x in rgb]
    return dict(color=[v/12.92 if v < .04045 else ((v+.055)/1.055)**2.4 for v in c], metallic=0, roughness=.84)

PALETTE = {name: swatch(rgb) for name, rgb in [
    ('light mineral finish',(188,180,159)), ('curved sill stone',(179,173,154)),
    ('shaded fascia',(154,149,134)), ('smooth pier facing',(193,187,169)),
    ('narrow bed joint',(145,142,132)), ('lower return',(166,161,144)),
]}

def point(angle, radius, height):
    return sin(angle)*radius, RADIUS-cos(angle)*radius, height

def cell(builder, name, a, b, front, back, z0, z1, mat):
    ra, rb = front
    vertices = [point(t,r,z) for z in (z0,z1) for t,r in ((a,ra),(b,rb),(b,back),(a,back))]
    faces = [(3,2,1,0),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    builder.add(vertices, faces, mat, name)

def band(builder, name, a, b, front, back, z0, z1, mat, parts):
    for j in range(parts):
        l = a + (b-a)*j/parts
        r = a + (b-a)*(j+1)/parts
        cell(builder,name,l,r,(front,front),back,z0,z1,mat)

def add_building(builder, lod=False):
    # The left return and front panel meet a broad, smooth pier.
    for side,(a,b,count) in enumerate(PANELS):
        steps = 4 if lod else 12
        for flute in range(count):
            width = (b-a)/count
            start = a + flute*width
            def radial(t):
                return RADIUS+.045-.042*sin(pi*t)**.8
            for j in range(steps):
                t = j/steps
                u = (j+1)/steps
                cell(builder,f'flute {side+1}-{flute+1}',start+t*width,start+u*width,
                     (radial(t),radial(u)),RADIUS-.16,.037,.919,'light mineral finish')
        pieces = count if lod else count*3
        for j,(lo,hi,front,back,material) in enumerate([
            (.000,.037,.038,-.147,'lower return'), (.919,.947,.047,-.16,'shaded fascia'),
            (.947,.981,.079,-.16,'curved sill stone'), (.981,1.012,.108,-.16,'curved sill stone'),
            (1.012,1.026,.093,-.16,'light mineral finish')]):
            band(builder,f'panel {side+1} band {j}',a,b,RADIUS+front,RADIUS+back,lo,hi,material,pieces)
    for i,(a,b) in enumerate(PIERS):
        parts = 3 if lod else 9
        band(builder,f'pier {i} joint backing',a,b,RADIUS+.012,RADIUS-.18,-.11,1.125,'narrow bed joint',parts)
        for course,(lo,hi) in enumerate([(-.11,.428),(.432,1.125)]):
            band(builder,f'pier {i} course {course}',a,b,RADIUS+.020,RADIUS-.16,lo,hi,'smooth pier facing',parts)
