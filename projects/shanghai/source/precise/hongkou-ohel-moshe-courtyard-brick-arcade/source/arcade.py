"""Three segmental arches on the courtyard face of the Ohel Moishe Synagogue, from the original stair elevation and 2011–2026 photographs."""
from math import acos, ceil, cos, pi, sin, sqrt

RGB = {'blue brick':(103,108,110),'ash brick':(111,114,112),'slate brick':(98,101,105),
       'red header':(154,92,74),'orange brick':(165,102,83),'shadow red':(144,84,70),
       'buff mortar':(132,121,113),'red mortar':(130,87,74),'cap stone':(130,126,118)}
def linear(c):
    s=c/255
    return s/12.92 if s<=.04045 else ((s+.055)/1.055)**2.4
PALETTE={k:{'color':[linear(c) for c in rgb],'roughness':.93} for k,rgb in RGB.items()}
PITCH=3.08
PIER=.762
CENTRES=[-PITCH,0.,PITCH]
SPRING=2.53
RISE=.36
TOP=3.49
HALF=(PITCH-PIER)/2
RADIUS=(HALF**2+RISE**2)/(2*RISE)
ZCENTRE=SPRING+RISE-RADIUS
ANGLE=acos((SPRING-ZCENTRE)/RADIUS)

def box(b,name,mat,l,r,z0,z1,front,back):
    b.box(((l+r)/2,(front+back)/2,(z0+z1)/2),(r-l,back-front,z1-z0),mat,label=name)
def extrude(b,name,material,out,front,back):
    if sum(x*v-u*z for (x,z),(u,v) in zip(out,out[1:]+out[:1]))<0:out=list(reversed(out))
    n=len(out);vs=[(x,y,z) for y in (front,back) for x,z in out];faces=[]
    for i in range(1,n-1):faces.extend([(0,i,i+1),(n,n+i+1,n+i)])
    for i in range(n):j=(i+1)%n;faces.extend([(i,n+i,n+j),(i,n+j,j)])
    b.add(vs,faces,material,name)
def point(x,r,t):return (x+r*sin(t),ZCENTRE+r*cos(t))
def segment(b,name,mat,x,lo,hi,a,c,f,g):
    extrude(b,name,mat,[point(x,lo,a),point(x,hi,a),point(x,hi,c),point(x,lo,c)],f,g)
def pier(b,k,x,far):
    name=f'Pier {k}';left=x-PIER/2;right=x+PIER/2
    box(b,name+' masonry core','buff mortar',left,right,0,SPRING+.01,.012,.57)
    rows=32;row_height=(SPRING-.25)/rows
    for row in range(rows):
        z=.25+row*row_height;red=row in (8,9,18,19,30,31)
        cols=2 if far else 3; size=PIER/cols;offset=size*.5 if not far and row%2 else 0
        for col in range(-1,cols+1):
            l=max(left,left+col*size+offset);r=min(right,left+(col+1)*size+offset)
            if r-l<.025:continue
            mat=('red header','orange brick','shadow red')[(row+col+k)%3] if red else ('blue brick','ash brick','slate brick')[(row*7+col*5+k)%3]
            box(b,name+(' red bands' if red else ' grey stretchers'),mat,l+.003,r-.003,z+.004,z+row_height-.004,0,.026)
        for side in (-1,1):
            edge=left if side<0 else right;bound=sorted((edge,edge+.047*side))
            box(b,name+' red jamb returns','red header',*bound,z+.004,z+row_height-.004,-.002,.572)
    for n,(h,e,m) in enumerate([(.18,.035,'red header'),(.06,.055,'orange brick'),(.035,.027,'red header')]):
        base=[0,.18,.24][n];box(b,name+' moulded red plinth',m,left-e,right+e,base,base+h,-.045-e,.57+e)
    for n,(z,h,e,mat) in enumerate([(SPRING-.275,.095,.019,'orange brick'),(SPRING-.18,.09,.045,'red header'),(SPRING-.09,.035,.077,'orange brick'),(SPRING-.055,.055,.089,'red header')]):
        box(b,name+' stepped brick impost',mat,left-e,right+e,z,z+h,-.031-e,.57+e)

def arch(b,i,x,far):
    name=f'Bay {i}';steps=20 if far else 35;outer=RADIUS+.259
    # The intrados, inner lip, outer soldier course and solid spandrel all stay hollow beneath the arch.
    for k in range(steps):
        a=-ANGLE+2*ANGLE*k/steps;c=-ANGLE+2*ANGLE*(k+1)/steps
        segment(b,name+' structural ring','red mortar',x,RADIUS,outer,a,c,.018,.575)
        q=.0015 if far else .0019
        for j,(lo,hi,front,back) in enumerate([(RADIUS+.003,RADIUS+.085,-.022,.055),(RADIUS+.089,outer-.003,-.060,.038)]):
            mat=('red header','orange brick','shadow red')[(k*11+i*7+j)%3]
            segment(b,name+(' inner rowlock' if not j else ' radial soldiers'),mat,x,lo,hi,a+q,c-q,front,back)
        v0=point(x,outer,a);v1=point(x,outer,c)
        extrude(b,name+' spandrel', 'blue brick',[v0,v1,(v1[0],TOP),(v0[0],TOP)],.007,.575)
    for row in range(5):
        z=3.075+row*.076
        if z>=TOP:continue
        bw=.295 if not far else .51
        for j in range(-6,7):
            left=max(x-PITCH/2,x+j*bw+(row%2)*bw/2);right=min(x+PITCH/2,x+(j+1)*bw+(row%2)*bw/2)
            if right-left<.026:continue
            # Do not let a rectangular stretcher intrude on the curved red soldier face.
            radius_x=min(abs(left-x),abs(right-x)) if left*right>0 or not (left<=x<=right) else 0
            bottom=ZCENTRE+sqrt(max(0,outer**2-radius_x**2))
            if bottom>=z:continue
            mat='red header' if row in (2,) else ('blue brick','ash brick','slate brick')[(j+row+i)%3]
            box(b,name+' spandrel brick courses',mat,left+.004,right-.004,z+.004,z+.072,-.001,.02)

def add_building(b,lod=False):
    for k in range(4):pier(b,k+1,(k-1.5)*PITCH,lod)
    for i,x in enumerate(CENTRES):arch(b,i+1,x,lod)
    # Red impost-zone courses continue across each pier to close the solid material between adjacent arch shoulders.
    for k in range(4):
        x=(k-1.5)*PITCH
        box(b,f'Pier {k+1} upper face','red header',x-PIER/2,x+PIER/2,SPRING,TOP,-.003,.572)
        for j in range(10):
            z=SPRING+j*(TOP-SPRING)/10;h=(TOP-SPRING)/10
            brick_width=.254 if not lod else .381
            offset=brick_width/2 if j%2 else 0.
            for piece in range(-1,4):
                left=max(x-PIER/2,x-PIER/2+piece*brick_width+offset)
                right=min(x+PIER/2,x-PIER/2+(piece+1)*brick_width+offset)
                if right-left<.025:continue
                colors=('blue brick','ash brick','slate brick') if j in (6,8,9) else ('red header','orange brick','shadow red')
                box(b,f'Pier {k+1} upper courses',colors[(j+piece+k)%3],left+.004,right-.004,z+.004,z+h-.004,-.013,.011)
    l,r=-1.5*PITCH-PIER/2,1.5*PITCH+PIER/2
    for z,h,e,mat in [(TOP,.035,.012,'red mortar'),(TOP+.035,.051,.048,'red header'),(TOP+.086,.055,.077,'cap stone')]:
        box(b,'Continuous gallery stringcourse',mat,l-e,r+e,z,z+h,-e,.57+e)
