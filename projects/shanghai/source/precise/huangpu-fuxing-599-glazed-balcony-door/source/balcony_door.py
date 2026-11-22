"""Glazed balcony door at 599 Middle Fuxing Road as photographed in July 2018."""
from math import pi,cos,sin

def coat(rgb,roughness=.76,metallic=0):
    color=[v/255/12.92 if v/255<.04045 else ((v/255+.055)/1.055)**2.4 for v in rgb]
    return dict(color=color,metallic=metallic,roughness=roughness)

PALETTE={
    'painted leaf':coat((93,68,67)), 'panel field':coat((98,72,70)), 'moulding bevel':coat((110,83,77)),
    'shadow joint':coat((66,54,51)), 'cement render':coat((168,165,143)),
    'rough edge':coat((148,145,127)), 'reveal':coat((148,144,125)), 'soffit':coat((120,119,107)),
    'iron':coat((72,71,64),.72,.24), 'upper glass':coat((87,91,95),.29,.14),
    'door glass':coat((95,105,105),.28,.15),'slab edge':coat((161,155,138))}

def box(b,name,x0,x1,y0,y1,z0,z1,material):
    v=[(x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1),(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)]
    b.add(v,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],material,name)

def ring(b,name,x0,x1,z0,z1,border,front,back,mat):
    # The rectangular bead has a raking face and a recessed interior.
    outer=[(x0,z0),(x1,z0),(x1,z1),(x0,z1)]
    inner=[(x0+border,z0+border),(x1-border,z0+border),(x1-border,z1-border),(x0+border,z1-border)]
    v=[(x,y,z) for y,poly in [(back,outer),(front,outer),(back,inner)] for x,z in poly]
    b.add(v,[(i,(i+1)%4,4+(i+1)%4,4+i)for i in range(4)]+[(4+i,4+(i+1)%4,8+(i+1)%4,8+i)for i in range(4)],mat,name)

def post(b,name,x,y,r,z0,z1,sides):
    verts=[(x+r*cos(i*2*pi/sides),y+r*sin(i*2*pi/sides),z)for z in [z0,z1]for i in range(sides)]
    faces=[(i,(i+1)%sides,(i+1)%sides+sides,i+sides)for i in range(sides)]
    faces.extend([tuple(reversed(range(sides))),tuple(range(sides,2*sides))])
    b.add(verts,faces,'iron',name)

def add_building(b,lod=False):
    # The face of the roughcast wall ends at either side of the tall reveal.
    for ident,x0,x1 in [('left',-1.06,-.51),('right',.51,1.04)]:
        box(b,ident+' rendered wall',x0,x1,0,.29,.15,3.23,'cement render')
    box(b,'wall head',-.51,.51,0,.29,2.95,3.23,'cement render')
    box(b,'head reveal',-.51,.51,.011,.265,2.89,2.95,'reveal')
    for ident,x0,x1 in [('left',-.51,-.487),('right',.487,.51)]:
        box(b,ident+' side reveal',x0,x1,.008,.255,.16,2.89,'reveal')
    box(b,'door threshold',-.51,.51,-.034,.272,.148,.205,'rough edge')
    box(b,'floor slab',-1.28,1.14,-.81,.28,0,.151,'slab edge')
    box(b,'shaded underside',-1.23,1.10,-.770,.24,-.1,0,'soffit')
    for name,x0,x1 in [('left',-.487,-.444),('right',.444,.487)]:
        box(b,name+' wood jamb',x0,x1,.126,.270,.19,2.89,'painted leaf')
    box(b,'upper jamb',-.444,.444,.126,.270,2.836,2.890,'painted leaf')
    # Four recessed panels arranged in two rows on the lower portion of the door.
    for k,(x0,x1) in enumerate([(-.445,-.002),(.002,.445)]):
        box(b,f'painted leaf base {k}',x0,x1,.167,.226,.2,1.367,'painted leaf')
        for i,(za,zb) in enumerate([(.28,.70),(.786,1.261)]):
            ring(b,f'panel moulding {k} {i}',x0+.068,x1-.061,za,zb,.021,.147,.164,'moulding bevel')
            box(b,f'recessed panel {k} {i}',x0+.089,x1-.082,.163,.168,za+.021,zb-.021,'panel field')
    box(b,'dark gap between leaves',-.007,.007,.176,.223,.20,1.366,'shadow joint')
    box(b,'glazing central stile',-.019,.019,.144,.203,1.36,2.843,'painted leaf')
    for k,(za,zb,mat) in enumerate([(1.364,2.006,'door glass'),(2.090,2.838,'upper glass')]):
        box(b,f'glass in upper opening {k}',-.445,.445,.201,.220,za,zb,mat)
        for i,x in enumerate([-.217,.217]):
            box(b,f'slender vertical glazing bar {k} {i}',x-.007,x+.007,.163,.202,za,zb,'painted leaf')
        for i in (1,2):
            z=za+(zb-za)*i/3
            box(b,f'horizontal glazing bar {k} {i}',-.445,.445,.158,.204,z-.009,z+.009,'painted leaf')
    box(b,'transom rail',-.445,.445,.135,.216,2.006,2.09,'painted leaf')
    box(b,'door waist rail',-.445,.445,.142,.213,1.318,1.367,'painted leaf')
    # The metal balcony rail is separate from the window grid. The rail turns toward the wall at right.
    front=-.733;lo=-1.205;hi=1.066
    for z in [.777,.992]:
        box(b,'long balcony rail',lo-.023,hi+.023,front-.017,front+.017,z-.018,z+.018,'iron')
        box(b,'short return rail',hi-.014,hi+.014,front+.017,-.004,z-.016,z+.016,'iron')
    for i in range(12):
        x=lo+(hi-lo)*i/11
        post(b,f'front railing standard {i}',x,front,.014 if i in [0,11] else .0088,.15,.996,8 if lod else 20)
    for i in [1,2,3]:
        y=front+(.733*i/3.55)
        post(b,f'return standard {i}',hi,y,.009,.15,.994,8 if lod else 20)
    # Sparse low relief in the cement represents the coarse exterior, using a fixed repeatable pattern.
    if not lod:
        for side,(xmin,xmax) in enumerate([(-1.06,-.52),(.52,1.04)]):
            v=[];faces=[]
            for i in range(260):
                u=((i*777+19*side)%991)/991;t=((i*i*37+71*i+109*side)%997)/997
                x=xmin+.018+(xmax-xmin-.036)*u;z=.19+3.02*t;r=.0037+.0018*(i%3)
                a=len(v);v.extend([(x-r,-.0001,z-.6*r),(x+.9*r,-.0001,z-r),(x+r,-.0001,z+.7*r),(x-.6*r,-.0001,z+r),(x,-.0025,z)])
                faces.extend([(a+j,a+(j+1)%4,a+4)for j in range(4)])
            b.add(v,faces,'rough edge','roughcast grains on '+('right'if side else'left'))
