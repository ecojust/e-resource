"""Garden-facing middle and right bays in the 2013 photograph of Anting Villa, building 1."""
from math import cos, pi, sin

PITCH = 2.56
CENTRES = (-PITCH / 2, PITCH / 2)
SPRING = 2.36
OPEN_RADIUS = 1.10
WALL_TOP = 3.74
BACK = 1.56

def linear(v):
    v /= 255
    return v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4

COLOURS = {
    'apricot plaster': (221, 190, 151), 'warm reveal': (183, 151, 121),
    'chalk stone': (215, 210, 192), 'moulding shadow': (185, 178, 161),
    'jointed plinth': (145, 139, 122), 'terrace flags': (170, 159, 139),
    'russet tile': (170, 78, 47), 'light fired tile': (185, 92, 54),
    'tile underside': (119, 70, 51), 'dark walnut': (59, 47, 41),
    'door glass': (52, 58, 52), 'bronze': (90, 77, 58), 'pendant glass': (164, 148, 118),
}
PALETTE = {k: {'color': [linear(v) for v in rgb], 'roughness': .87} for k, rgb in COLOURS.items()}

def moulding(b, label, cx, elevation, sections, profile, material):
    """Sweep a stepped profile around a half circle. A profile pair is (radius, y)."""
    vertices = []
    for i in range(sections + 1):
        theta = pi * i / sections
        vertices.extend((cx + r*cos(theta), y, elevation + r*sin(theta)) for r,y in profile)
    n = len(profile)
    faces = []
    for i in range(sections):
        base = i*n
        for j in range(n):
            k = (j+1)%n
            faces.append((base+j,base+k,base+n+k,base+n+j))
    faces.extend([tuple(range(n-1,-1,-1)),tuple(range(sections*n,(sections+1)*n))])
    b.add(vertices,faces,material,label)

def infill_above(b,label,cx,half,cy,radius,top,front,back,material,n):
    """A continuous wall between a semicircular soffit and level entablature."""
    v=[]; f=[]
    for i in range(n+1):
        t=pi-pi*i/n
        x=cx+radius*cos(t); z=cy+radius*sin(t)
        v.extend([(x,front,z),(x,front,top),(x,back,top),(x,back,z)])
    for i in range(n):
        for j in range(4):
            k=(j+1)%4
            f.append((4*i+j,4*(i+1)+j,4*(i+1)+k,4*i+k))
    f.extend([(3,2,1,0),tuple(range(4*n,4*n+4))])
    b.add(v,f,material,label)
    for side in (-1,1):
        b.box((cx+side*(radius+half)/2,(front+back)/2,(cy+top)/2),
              (half-radius,back-front,top-cy),material,label=label)

def half_panel(b,label,cx,y,cz,radius,material,n):
    v=[(cx,y,cz)]
    v.extend((cx+radius*cos(pi*i/n),y,cz+radius*sin(pi*i/n)) for i in range(n+1))
    b.add(v,[(0,i,i+1) for i in range(1,n+1)],material,label)

def tile_course(b,x,y,z,width,length,material,n,label):
    r=width/2; verts=[];faces=[]
    for u in (0.,1.):
        for i in range(n+1):
            t=pi*i/n
            verts.extend([(x+r*cos(t),y+u*length,z+.13*u+r*sin(t)),
                          (x+(r-.021)*cos(t),y+u*length,z+.13*u+(r-.021)*sin(t))])
    jump=2*(n+1)
    for i in range(n):
        j=2*i
        faces.extend([(j,j+2,jump+j+2,jump+j),(j+1,jump+j+1,jump+j+3,j+3),
                      (j,j+1,j+3,j+2),(jump+j,jump+j+2,jump+j+3,jump+j+1)])
    b.add(verts,faces,material,label)

def add_building(b,lod=False):
    n=16 if lod else 36
    b.box((0,-.06,-.16),(5.47,3.58,.32),'jointed plinth',label='Terrace stone plinth')
    b.box((0,-.06,-.025),(5.52,3.61,.065),'terrace flags',label='Terrace flagstone nosing')
    for idx,x in enumerate((-PITCH,0,PITCH)):
        label=f'Arcade post {idx+1}'
        b.box((x,.14,1.15),(.31,.38,2.30),'chalk stone',label=label+' shaft')
        for z,width,height,mat in ((.09,.42,.17,'moulding shadow'),(.21,.37,.07,'chalk stone'),
                                    (2.21,.36,.085,'moulding shadow'),(2.28,.42,.08,'chalk stone'),
                                    (2.345,.47,.055,'moulding shadow'),(2.405,.50,.07,'chalk stone')):
            b.box((x,.14,z),(width,width+.045,height),mat,label=label+' cap and base')
    for index,cx in enumerate(CENTRES):
        lab=f'Bay {index+1}'
        infill_above(b,lab+' plaster spandrel',cx,PITCH/2,SPRING,OPEN_RADIUS,WALL_TOP,.035,.36,'apricot plaster',n)
        moulding(b,lab+' stone archivolt',cx,SPRING,n,
                 [(1.095,.33),(1.095,-.035),(1.122,-.077),(1.17,-.077),(1.188,-.052),(1.205,-.032),(1.205,.07)],'chalk stone')
        moulding(b,lab+' recessed fillet',cx,SPRING,n,[(1.169,-.08),(1.182,-.072),(1.186,-.059),(1.177,-.059)],'moulding shadow')
        rear_spring,rear_radius=1.88,.775
        infill_above(b,lab+' back wall',cx,PITCH/2,rear_spring,rear_radius,3.79,BACK,BACK+.16,'warm reveal',n)
        moulding(b,lab+' door surround',cx,rear_spring,n,
                 [(rear_radius,BACK+.10),(rear_radius,BACK-.045),(.84,BACK-.09),(.91,BACK-.07),(.93,BACK+.015)],'chalk stone')
        for side in (-1,1):
            w=PITCH/2-rear_radius
            b.box((cx+side*(rear_radius+w/2),BACK+.08,rear_spring/2),(w,.16,rear_spring),'warm reveal',label=lab+' rear jamb')
            b.box((cx+side*.825,BACK-.02,rear_spring/2),(.10,.14,rear_spring),'chalk stone',label=lab+' inner jamb')
        half_panel(b,lab+' dark arched fanlight',cx,BACK+.105,rear_spring,.775,'door glass',n)
        for side in (-1,1):
            x=cx+side*.385
            b.box((x,BACK+.125,.93),(.768,.07,1.86),'dark walnut',label=lab+' timber door leaves')
            b.box((x,BACK+.083,1.13),(.565,.016,1.2),'door glass',label=lab+' upper door glass')
            if not lod:
                b.box((x,BACK+.075,.345),(.565,.018,.21),'moulding shadow',label=lab+' lower door panel')
        b.box((cx,BACK+.07,.96),(.05,.052,1.91),'dark walnut',label=lab+' meeting stile')
        b.box((cx,BACK+.065,1.86),(1.58,.07,.09),'dark walnut',label=lab+' transom bar')
        # The small square lantern appears as a diamond in the frontal photograph.
        b.tube([(cx,.52,3.51),(cx,.52,3.29)],.016,'bronze',sides=5,label=lab+' pendant rod')
        b.add([(cx,.52,3.29),(cx-.165,.52,3.14),(cx,.36,3.14),(cx+.165,.52,3.14),
               (cx,.68,3.14),(cx,.52,2.98)],[(0,1,2),(0,2,3),(0,3,4),(0,4,1),
               (5,2,1),(5,3,2),(5,4,3),(5,1,4)],'pendant glass',lab+' lantern panes')
        if not lod:
            for dx,dy in ((-.165,0),(0,-.16),(.165,0),(0,.16)):
                b.tube([(cx,.52,3.29),(cx+dx,.52+dy,3.14),(cx,.52,2.98)],.012,'bronze',sides=5,label=lab+' lantern frame')
    b.box((0,.48,3.711),(5.54,1.67,.19),'chalk stone',label='Projecting pale eaves')
    b.box((0,.49,3.806),(5.57,1.7,.054),'tile underside',label='Clay roof bed')
    cols=28; width=5.56/cols
    for col in range(cols):
        x=-5.56/2+(col+.5)*width
        for course in range(2 if lod else 4):
            step=.38 if lod else .19
            tile_course(b,x,-.402+course*step,3.816+.061*course*(2 if lod else 1),width-.006,
                        step+.045,('russet tile','light fired tile')[(col+course)%5==1],
                        4 if lod else 8,'Tiles course '+str(course+1))
    b.box((0,-1.55,.102),(5.53,.24,.204),'moulding shadow',label='Balustrade bottom rail')
    b.box((0,-1.55,.18),(5.51,.26,.065),'chalk stone',label='Balustrade base moulding')
    for x in (-PITCH,0,PITCH):
        b.box((x,-1.55,.54),(.25,.27,.78),'chalk stone',label='Balustrade square piers')
    profile=[(.205,.084),(.236,.096),(.27,.074),(.32,.058),(.383,.061),(.48,.093),(.54,.094),(.625,.062),(.69,.046),(.764,.064),(.80,.082),(.834,.083)]
    for idx,cx in enumerate(CENTRES):
        for j in range(8):
            x=cx+((j+.5)/8-.5)*(PITCH-.17)
            b.lathe((x,-1.55),profile,'chalk stone',segments=7 if lod else 14,label='Turned balusters bay '+str(idx+1))
    b.box((0,-1.55,.865),(5.55,.27,.087),'moulding shadow',label='Balustrade upper fillet')
    b.box((0,-1.55,.925),(5.60,.295,.061),'chalk stone',label='Balustrade stone coping')
