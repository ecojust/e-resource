"""The red clay corner eaves of the garden house at 1 Kangping Road in December 2013."""
from math import cos, pi, sin, sqrt

PITCH = .192
COUNT = 16
LENGTH = PITCH * COUNT
DEPTH = 1.24
EAVE = 1.08
SLOPE = .43

def linear(c):
    value = c / 255
    return value / 12.92 if value <= .04045 else ((value+.055)/1.055)**2.4

COLOURS = {
    'dark clay underlay': (94, 61, 49), 'russet cover': (159, 98, 74),
    'weathered cover': (138, 82, 64), 'red clay pan': (139, 87, 68),
    'red hip cap': (153, 94, 78), 'shadowed gutter': (57, 53, 48),
    'brown fascia': (86, 62, 52), 'sand render': (201, 190, 166),
}
PALETTE = {name:dict(color=[linear(c) for c in rgb],roughness=.92) for name,rgb in COLOURS.items()}

def transverse(side, across, upslope, height):
    if side=='front':
        return (across, upslope, height)
    return (upslope, across, height)

def skin(builder, vertices, profile, material, name):
    faces=[]
    for j in range(profile):
        k=(j+1)%profile
        faces.append((j,k,profile+k,profile+j))
    faces += [tuple(reversed(range(profile))),tuple(range(profile,2*profile))]
    builder.add(vertices,faces,material,name)

def hollow_end_skin(builder, vertices, count, material, name):
    # The two end faces follow the arc. A triangle fan across a concave half-tube fills its mouth.
    length = 2 * count
    faces = []
    for i in range(length):
        j = (i + 1) % length
        faces.append((i, j, j+length, i+length))
    for i in range(count-1):
        inner = length-1-i
        faces.append((i,inner,inner-1,i+1))
        faces.append((i+length,i+length+1,inner+length-1,inner+length))
    builder.add(vertices,faces,material,name)

def course(builder, side, center, start, end, width, rise, pan, steps, material, name):
    """Trim a hollow tile against the actual diagonal where the two slopes meet."""
    profile=[]
    for inner,angles in [(False,range(steps+1)),(True,range(steps,-1,-1))]:
        for i in angles:
            angle=pi*i/steps
            local=center+.5*width*cos(angle)
            crown=rise*((1-sin(angle)) if pan else sin(angle))
            profile.append((local,crown-(.013 if inner else 0)))
    vertices=[]
    for depth in (start,end):
        for local,crown in profile:
            actual=min(depth,max(0,local))
            lap_lip = .009 if depth == start else 0
            z=EAVE+actual*SLOPE+crown+(.020 if not pan else 0)+lap_lip
            vertices.append(transverse(side,local,actual,z))
    hollow_end_skin(builder,vertices,steps+1,material,name)

def hip(builder, start, end, idx, steps):
    """Rounded overlapping ridge tile, open at its street-facing end."""
    points=[]
    for inner,angles in [(False,range(steps+1)),(True,range(steps,-1,-1))]:
        for j in angles:
            a=pi*j/steps
            r=.142-(.020 if inner else 0)
            points.append((r*cos(a)/sqrt(2),r*sin(a)))
    verts=[]
    for d in (start,end):
        for offset,z in points:
            scale = 1.08 if d == start else .96
            verts.append((d+offset*scale,d-offset*scale,EAVE+SLOPE*d+.070+z*scale))
    hollow_end_skin(builder,verts,steps+1,'red hip cap',f'Rounded hip tile {idx+1}')

def add_building(b,lod=False):
    for side in ('front','return'):
        plan=[(0,0),(LENGTH,0),(LENGTH,DEPTH),(DEPTH,DEPTH)]
        verts=[transverse(side,x,y,EAVE+SLOPE*y+dz) for dz in (-.062,-.015) for x,y in plan]
        skin(b,verts,4,'dark clay underlay',side+' roof bed')
        def fascia(width,depth,z,offset,mat,label):
            size=(width,depth,.085)
            c=(width/2,offset,z)
            b.box(transverse(side,*c),size if side=='front' else (size[1],size[0],size[2]),mat,label=side+' '+label)
        fascia(LENGTH,.073,EAVE-.091,.057,'brown fascia','painted fascia board')
        fascia(LENGTH,.078,EAVE-.031,.009,'shadowed gutter','dark outer eave gutter')
        for i in range(COUNT):
            for pan in (True,False):
                mid=(i+(.78 if pan else .28))*PITCH
                start=0
                limit=min(mid+.5*PITCH,DEPTH)
                n=0
                while start<limit-.004:
                    length=.37 if not lod else .75
                    # The street row is exposed; successive covers lap a little over its head.
                    end=min(start+length,DEPTH)
                    width,rise=(.126,.034) if pan else (.087,.048)
                    mat='red clay pan' if pan else ('weathered cover' if (3*i+n)%7<2 else 'russet cover')
                    label=f'{side} '+('pan' if pan else 'convex cover')+f' course {i+1}'
                    course(b,side,mid,start,end,width,rise,pan,3 if lod else 8,mat,label)
                    start+=length-.024;n+=1
    y0=.30
    b.box(((LENGTH+y0)/2,(DEPTH+y0)/2,.485),(LENGTH-y0,DEPTH-y0,.97),'sand render',label='Plastered wall under the front eave')
    b.box(((DEPTH+y0)/2,(LENGTH+DEPTH)/2,.485),(DEPTH-y0,LENGTH-DEPTH,.97),'sand render',label='Plastered wall around the corner')
    for j in range(5):
        hip(b,max(-.055,j*.26-.041),min(DEPTH,j*.26+.258),j,6 if lod else 16)
