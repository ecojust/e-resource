"""Build the visible planks, two rows of nail heads and the paired lock plates in the 2020 survey."""
from math import cos, sin, pi, sqrt
from random import Random
from pathlib import Path

COLORS={
    'dark oak':(.118,.091,.070),'weathered board':(.160,.134,.109),'inner strip':(.082,.063,.048),
    'wood ridges':(.043,.037,.030),'worn lower grain':(.066,.065,.058),'fine split':(.022,.019,.017),
    'blackened iron':(.100,.079,.062),'iron wear':(.292,.244,.176),'pale fitting':(.402,.376,.309),
    'oxidized metal':(.232,.171,.094),'lock steel':(.209,.220,.219)
}
PALETTE={k:{'color':list(v),'roughness':.83 if k in ('dark oak','weathered board','inner strip','fine split','wood ridges','worn lower grain')else .56,
            'metallic':.38 if k in ('blackened iron','iron wear','oxidized metal','lock steel')else .03}for k,v in COLORS.items()}
WOOD_MATERIALS = ('dark oak','weathered board','inner strip')
for key,tint in zip(WOOD_MATERIALS,([.91,.87,.82],[1.,1.,1.],[.67,.64,.61])):
    PALETTE[key].update(color=tint,texture=str(Path(__file__).with_name('weathered-planks.png')))
SCALE=.00345
LEFT=[(20,12),(96,88),(149,146),(202,199),(253,249)]
RIGHT=[(259,259),(316,312),(369,369),(429,432),(493,491)]
HEADS=[33,69,104,139,172,205,238,277,311,345,381,416,451,486]

def pos(x,y,depth):
    return ((x-252)*SCALE,depth,(751-y)*SCALE)

def skin(builder,label,poly,depth,thick,material):
    # The front outline is anticlockwise in X/Z, which points toward the camera at negative Y.
    poly=list(poly)
    area=sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(poly,poly[1:]+poly[:1]))
    if area>0:poly.reverse()
    count=len(poly)
    front=[pos(x,y,depth) for x,y in poly];back=[pos(x,y,depth+thick) for x,y in poly]
    faces=[tuple(range(count)),tuple(range(count,2*count))[::-1]]
    faces.extend(((j+1)%count,j,j+count,(j+1)%count+count)for j in range(count))
    builder.add(front+back,faces,material,label)
    if material in WOOD_MATERIALS:
        uv=[(max(0.,min(1.,x/500)),max(0.,min(1.,y/752))) for x,y in poly]
        builder.parts[-1]['texcoords']=uv+uv

def top(x):
    if x<50:
        return 52-sqrt(max(0,31**2-(x-51)**2))
    if x>465:
        return 50-sqrt(max(0,29**2-(x-464)**2))
    return 20+(252-x)*.007

def dome(b,label,x,y,depth,r,lod):
    n=8 if lod else 16
    verts=[]
    for rr,offset in [(r,.001),(r*.90,-.002),(r*.56,-.005)]:
        verts.extend(pos(x+rr*cos(i*2*pi/n),y-rr*sin(i*2*pi/n),depth+offset) for i in range(n))
    verts.append(pos(x,y,depth-.0065))
    faces=[tuple(range(n))[::-1]]
    for ring in [0,n]:
        for j in range(n):
            k=(j+1)%n;faces.append((ring+j,ring+k,ring+n+k,ring+n+j))
    faces.extend((2*n+j,2*n+(j+1)%n,3*n)for j in range(n))
    b.add(verts,faces,'blackened iron',label)

def escutcheon(b,x,y,side,angle,depth,lod):
    c=cos(angle);s=sin(angle)
    poly=[(x+c*a-s*d,y+s*a+c*d)for a,d in [(-15,-15),(15,-15),(15,15),(-15,15)]]
    skin(b,side+' skew square lock plate',poly,depth-.0055,.0065,'pale fitting')
    dome(b,side+' riveted spindle',x,y,depth-.006,3,lod)
    loop=[pos(x+3.8*cos(t*2*pi/16),y+1.8*sin(t*2*pi/16),depth-.021-.014*sin(t*2*pi/16))for t in range(17)]
    b.tube(loop,.0045,'oxidized metal',6 if lod else 10,side+' iron eye')

def add_building(b,lod):
    rng=Random(746)
    for side,edges,depth in [('left',LEFT,0.),('right',RIGHT,.012)]:
        for j,((left,left_bottom),(right,right_bottom)) in enumerate(zip(edges,edges[1:])):
            poly=[(left_bottom+.5,750),(right_bottom-.5,750)]
            segments=6 if j in (0,3) else 1
            for k in range(segments+1):
                x=right-.5+(left+.5-right+.5)*k/segments
                poly.append((x,top(x)))
            mat='inner strip'if (side,j)==('left',3) else ('dark oak' if j%2 else 'weathered board')
            skin(b,f'{side} vertical board {j+1}',poly,depth,.043,mat)
            for g in range(7 if lod else 21):
                ratio=rng.uniform(.05,.95);ty=rng.uniform(42,708);by=min(746,ty+rng.uniform(22,128))
                def x_at(t):return (left+ratio*(right-left))*(1-t/751)+(left_bottom+ratio*(right_bottom-left_bottom))*t/751
                tx=x_at(ty);bx=x_at(by)
                skin(b,f'{side} board {j+1} grain {g+1}',[(tx,ty),(tx+.40,ty+5),(bx+.85,by-3),(bx,by)],depth-.0008,.0014,
                     'worn lower grain'if ty>583 else ('fine split' if g%3 else 'wood ridges'))
    for row,py in [('upper',132),('lower',645)]:
        for ix,x in enumerate(HEADS):
            yy=py+((ix%4)-2)*.9
            dome(b,f'{row} nail {ix+1}',x,yy,0. if ix<7 else .012,3.6 if ix%3 else 4.1,lod)
    escutcheon(b,228,386,'left',.61,0.,lod)
    escutcheon(b,282,397,'right',-.35,.012,lod)
    b.tube([pos(x,y,z)for x,y,z in [(228,387,-.021),(233,391,-.029),(238,399,-.035),(242,405,-.034)]],
           .0042,'blackened iron',6 if lod else 10,'left short hasp below its eye')
    b.tube([pos(x,y,z)for x,y,z in [(242,404,-.034),(251,404,-.029),(269,398,-.015),(282,397,-.011)]],
           .0034,'oxidized metal',6 if lod else 10,'slender link obliquely between eyes')
    skin(b,'small rectangular padlock below left fitting',[(233,409),(245,405),(248,415),(235,419)],-.036,.013,'lock steel')
    bow=[pos(239+3.3*cos(pi*k/12),407-6*sin(pi*k/12),-.033)for k in range(13)]
    b.tube(bow,.0023,'iron wear',6 if lod else 10,'round padlock bow')
