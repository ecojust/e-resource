"""The pair of raking stone hoods and both of the different striped awnings."""
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_plane import position
from shade_bands import band_count,band_interval

STONE="Pale carved limestone"; LIGHT="Cream arris"; SHADE="Weathered moulding return"
FIELD="Warm grey lime render"; JOINT="Lime joint"; REVEAL="Stone reveal"; SILL="Cut stone sill"
WOOD="Graphite sash"; GLAZING=("Charcoal grey glass","Grey blue reflection","Warm smoky glass")
BLUE="Dusty blue awning stripe"; OCHRE="Warm flax awning stripe"; HEM="Dark canvas hem"
LINING="Recessed panelling"; METAL="Awning hinge"
# Each polygon was measured on the upright photograph, with the two sides kept distinct.
BAYS=(
 dict(name='Left',sill=[(90,911),(260,841)], opening=[(91,560),(245,482),(254,848),(90,915)],
      hood=[(40.5,463),(141.7,292),(253.5,336)], hood_in=[(66,460),(154,339),(241,363)],
      panel=[(68,496),(254,386),(256,493),(64,579)],
      key=[(134,421),(176,404),(199,491),(151,517)],
      awning=[(54,586),(99,563),(144,542),(198,517),(239,494)],
      drops=[[(55,590),(85,572),(84,750),(59,761)],[(207,520),(237,497),(245,673),(216,680)]]),
 dict(name='Right',sill=[(335,810),(531,727)],opening=[(333,419),(518,327),(531,731),(338,811)],
      hood=[(268,328.8),(390,135.8),(524,175)],hood_in=[(303,323),(403,190),(509,211)],
      panel=[(298,365),(522,237),(522,334),(305,455)],
      key=[(382,275),(429,257),(448,349),(397,375)],
      awning=[(289,484),(331,431),(360,421),(401,412),(438,393),(469,378),(493,353),(510,344)],
      drops=[[(294,475),(335,442),(354,648),(298,650)],[(472,375),(523,344),(533,548),(493,559)]]))

def shape(points,y=0.):
    return Polygon([(p[0],p[2]) for p in [position(*q,y) for q in points]])
def bilinear(quad,u,v):
    a,b,c,d=np.asarray(quad)
    return (1-v)*((1-u)*a+u*b)+v*((1-u)*d+u*c)
def quadcell(quad,u,U,v,V):
    return Polygon([bilinear(quad,t,h) for t,h in [(u,v),(U,v),(U,V),(u,V)]])
def projected(point,y):
    p=position(*point,y);return p[[0,2]]
def label(name,part):return name+' bay/'+part

def panelled_stone(f,bay):
    name=bay['name'];q=np.asarray(bay['hood'],float);inside=np.asarray(bay['hood_in'],float)
    # The tympanum lies back from the folded fascia; the two planes meet at the apex.
    f.prism(shape(bay['hood'],-.22),.025,.12,STONE,label(name,'pedimental tympanum'))
    def raking_sweep(outline,inn,section,tag):
        # Sweep a continuous stepped profile along both rakes. The shared apex remains mitred.
        for side in (0,1):
            for it,((t0,d0),(t1,d1)) in enumerate(zip(section,section[1:])):
                p0,p1=(1-t0)*outline+t0*inn,(1-t1)*outline+t1*inn
                vertices=[position(*p0[side],-d0),position(*p0[side+1],-d0),position(*p1[side+1],-d1),position(*p1[side],-d1)]
                material=LIGHT if it in (1,3,5,8) else SHADE if it in (2,4,7) else STONE
                f.builder.add(vertices,[(3,2,1,0)],material,label(name,tag+' '+str(side+1)+' fillet '+str(it+1)))
    raking_sweep(q,inside,[(0,.06),(.04,.285),(.11,.298),(.16,.276),(.23,.276),(.35,.241),(.49,.245),(.69,.207),(.80,.193),(.91,.158),(1,.12)],'raking cornice')
    # Flat run-outs at both feet. The level moulding is interrupted by the projecting keystone.
    feet=np.asarray([q[0]-[0,-2.5],q[2]+[11 if name=="Left" else 15,-4]])
    shift=np.array([5.,24.])
    for j,(t,T,d,D) in enumerate([(0,.18,.25,.32),(.18,.38,.21,.30),(.38,.64,.17,.26),(.64,1,.09,.22)]):
        f.prism(shape([feet[0]+t*shift,feet[1]+t*shift,feet[1]+T*shift,feet[0]+T*shift],-D),d,D,[LIGHT,STONE,SHADE,STONE][j],label(name,'horizontal cornice '+str(j+1)))
    frieze=shape(bay['panel'],-.07)
    f.prism(frieze,.001,.067,STONE,label(name,'frieze backing'))
    panel=np.asarray(bay['panel'],float)
    for k,(u,U) in enumerate(((.105,.485),(.56,.925))):
        outer=shape([bilinear(panel,t,h) for t,h in [(u,.17),(U,.17),(U,.84),(u,.84)]],-.105)
        inset=outer.buffer(-.028,join_style=2)
        f.prism(outer.difference(inset),.066,.11,LIGHT,label(name,'raised panel return '+str(k+1)))
        f.prism(inset,.065,.069,LINING,label(name,'recessed square field '+str(k+1)))
    keystone=shape(bay['key'],-.255)
    f.prism(keystone,.061,.243,STONE,label(name,'tapered central console'))
    f.prism(keystone.buffer(-.012,join_style=2),.243,.255,LIGHT,label(name,'console face'))

def sash(f,bay):
    name=bay['name'];q=np.array([projected(p,.015) for p in bay['opening']])
    perimeter=Polygon(q)
    for k,(a,b,depth,mat) in enumerate(((0,.037,.039,STONE),(.037,.07,.018,REVEAL),(.07,.103,-.19,WOOD))):
        outside=perimeter.buffer(-a,join_style=2);inside=perimeter.buffer(-b,join_style=2)
        f.prism(outside.difference(inside),-.268,depth,mat,label(name,'sash reveal '+str(k+1)))
    f.prism(perimeter.buffer(-.085,join_style=2),-.319,-.315,GLAZING[0],label(name,'dark interior'))
    for col,(u,U) in enumerate(((.07,.48),(.515,.94))):
        for row,(v,V) in enumerate(((.025,.48),(.507,.97))):
            p=quadcell(q,u,U,v,V).intersection(perimeter.buffer(-.095,join_style=2))
            if p.area: f.prism(p,-.275,-.271,GLAZING[(col+row+(name=='Right'))%3],label(name,'glass '+str(col+1)+' '+str(row+1)))
    for i,cell in enumerate([(0.48,.516,.02,.98),(.045,.952,.48,.507)]):
        f.prism(quadcell(q,*cell),-.267,-.199,WOOD,label(name,'mullion' if not i else 'transom'))
    a,b=map(np.asarray,bay['sill']);q=[a,b,b+[0,19],a+[1,18]]
    sill=shape(q,-.154)
    f.prism(sill,-.015,.153,SILL,label(name,'weathered sill'))
    f.prism(shape([a,b,b+[0,5],a+[0,5]],-.163),.149,.164,LIGHT,label(name,'sill nose'))
    return perimeter

def cloth(b,bay,lod):
    name=bay['name'];front=np.asarray(bay['awning'],float)
    front_y=-.385 if name=='Left' else -.51
    hinge_y=.004
    down=30 if name=='Left' else 37
    # Cubic woven folds connect the projected edge to the bracket at the wall.
    n=40 if lod else 92;rows=7 if lod else 17
    ts=np.linspace(0,1,len(front))
    def point(t,v):
        u,z=[np.interp(t,ts,front[:,axis]) for axis in (0,1)]
        waved=np.sin(6*np.pi*t+.31)*np.sin(v*np.pi)
        p=position(u+v*(10 if name=='Left' else 17),z-v*down-3*waved,front_y*(1-v)+hinge_y*v)
        p[2]+= .01*waved*(1-v)
        return p
    for i in range(n):
        vertices=[];faces=[]
        for col in range(2):
            for j in range(rows+1):vertices.append(point((i+col)/n,j/rows))
        for j in range(rows):faces.append((j,j+rows+1,j+rows+2,j+1))
        b.add(vertices,faces,HEM if int(i*11/n)%3 else BLUE,label(name,'awning woven canopy'))
    # The right canopy is gathered. Its two scalloped hems stand in front of the rail.
    nrows=3 if lod else 5
    for edge in range(2 if name=='Right' else 1):
        verts=[];faces=[]
        for i in range(n+1):
            t=i/n
            for j in range(nrows+1):
                v=j/nrows
                p=point(t,.045+edge*.22)
                sag=.038*(.3+np.sin(np.pi*t)**2) if name=='Right' else .018
                p[1]-=(.013+.008*np.cos(t*8))*np.sin(v*np.pi)
                p[2]-=(sag+.013*np.sin(t*(13 if name=='Right' else 8)))*v
                verts.append(p)
        for i in range(n):
            for j in range(nrows):
                k=i*(nrows+1)+j;faces.append((k,k+nrows+1,k+nrows+2,k+1))
        b.add(verts,faces,HEM,label(name,'gathered forward hem '+str(edge+1)))
    for index,quad in enumerate(bay['drops']):
        for band in range(band_count(name,index)):
            ns=5 if lod else 12;nt=3 if lod else 6
            verts=[];faces=[]
            for us in range(ns+1):
                u=us/ns
                for vs in range(nt+1):
                    top,bottom,is_blue=band_interval(name,index,band,u)
                    v=top+(bottom-top)*vs/nt;uv=bilinear(quad,u,v)
                    wave=np.sin(u*3*np.pi+1.2*v)
                    d=front_y+.13*u+.042*wave*(.2+.8*v)+.025*np.sin(v*3.14)
                    verts.append(position(*uv,d))
            for us in range(ns):
                for vs in range(nt):
                    s=us*(nt+1)+vs;faces.append((s+1,s+nt+2,s+nt+1,s))
            b.add(verts,faces,BLUE if is_blue else OCHRE,label(name,'striped side '+str(index+1)+' band '+str(band+1)))
    for i,t in enumerate((.06,.93)):
        top=point(t,1);end=point(t,0)
        shaft=(top+end)/2;v=top-end;v=v/np.linalg.norm(v)
        axis=np.cross(v,[0,0,1]);axis/=np.linalg.norm(axis);other=np.cross(v,axis)
        b.box(shaft,[np.linalg.norm(top-end),.014,.016],METAL,[v,axis,other],label(name,'awning support '+str(i+1)))
