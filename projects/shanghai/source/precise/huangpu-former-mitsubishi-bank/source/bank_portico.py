"""The four giant street columns, their capitals and the two reclining entrance lions."""
import math
import numpy as np

GRANITE='light dressed granite'
CUT='carved capital stone'
BASE='dark granite foundation'
BRONZE='patinated cast bronze'

def ellipsoid(b,center,radii,mat,label,lod):
    steps=8 if lod else 14;rings=4 if lod else 7
    x,y,z=center;rx,ry,rz=radii
    pts=[(x,y,z-rz)]
    for j in range(1,rings):
        h=math.pi*j/rings
        for k in range(steps):
            t=math.tau*k/steps
            pts.append((x+rx*math.sin(h)*math.cos(t),y+ry*math.sin(h)*math.sin(t),z-rz*math.cos(h)))
    pts.append((x,y,z+rz));top=len(pts)-1;faces=[]
    for k in range(steps):
        n=(k+1)%steps;faces.append((0,n+1,k+1))
        for j in range(rings-2):
            a=1+j*steps+k;v=1+j*steps+n
            faces.extend([(a,v,v+steps),(a,v+steps,a+steps)])
        faces.append((top,1+(rings-2)*steps+k,1+(rings-2)*steps+n))
    b.add(pts,faces,mat,label)

def columns(b,f,lod,xs):
    for idx,x in enumerate(xs):
        route='Portico / column '+str(idx+1)
        centre=f.point(x,0,.18)[:2]
        # Lower plinth, torus and scotia, tall unfluted shaft, neck and square abacus.
        b.lathe(centre,[(.79,1.00),(.89,1.00),(.97,.94),(1.01,.81),(1.09,.91),(1.18,.91),
                 (1.24,.80),(1.31,.71),(1.39,.78),(1.45,.78),(1.49,.71),(4.2,.70),
                 (8.4,.66),(11.46,.61),(11.55,.64),(11.63,.69),(11.75,.70),(12.30,.81),
                 (12.46,.83)],GRANITE,18 if lod else 36,route+'/shaft and moulded base')
        f.box(x,12.55,1.85,.20,1.87,.18,CUT,route+'/upper abacus')
        for direction in [0,math.pi/2,math.pi,3*math.pi/2]:
            outward=np.array([math.cos(direction),math.sin(direction)]);t=np.array([-outward[1],outward[0]])
            def at(u,z,projection):
                v=centre+outward*projection+t*u;return(v[0],v[1],z)
            for sign in (-1,1):
                samples=np.linspace(0,math.tau*1.15,12 if lod else 24)
                coil=[at(sign*(.61+.157*(1-.54*i/(len(samples)-1))*math.cos(a)),12.28+.148*(1-.54*i/(len(samples)-1))*math.sin(a),.68)for i,a in enumerate(samples)]
                b.tube(coil,.048,CUT,6 if lod else 8,route+'/corner volutes')
            for tx in [-.27,0,.27]:
                start=at(tx*.32,11.82,.668);tip=at(tx,12.23,.710)
                ridge=at(tx*.69,12.03,.748)
                left=at(tx*.69-.08,12.02,.704);right=at(tx*.69+.08,12.02,.704)
                b.add([start,left,ridge,right,tip],[(0,2,1),(0,3,2),(1,2,4),(2,3,4)],CUT,route+'/leaf fans')
        for k in range(12 if lod else 24):
            t=math.tau*k/(12 if lod else 24);cx,cy=centre+np.array([math.cos(t),math.sin(t)])*.66
            b.box((cx,cy,11.62),(.070,.070,.11),CUT,label=route+'/neck beads')
        if not lod:
            for z in (3.0,5.2,7.4,9.6):
                rad=.72-.11*max(0,(z-1.5)/10);b.lathe(centre,[(z-.009,rad),(z,rad+.004),(z+.009,rad)],GRANITE,36,route+'/drum joint')

def lions(b,f,lod):
    for side in (-1,1):
        cx=side*4.43;y=-.40;z=.81
        label='Entrance / '+('west'if side<0 else'east')+' reclining bronze lion'
        # The pair faces in toward the stair. Body, head, forepaws and curled tail are distinct volumes.
        def blob(x,yoff,h,dims,part):ellipsoid(b,(cx+side*x,y+yoff,z+h),dims,BRONZE,label+'/'+part,lod)
        b.box((cx,y,z+.06),(1.98,1.03,.12),BRONZE,label=label+'/base plate')
        blob(.17,.0,.31,(.73,.36,.31),'reclining torso');blob(.60,.03,.28,(.39,.37,.27),'haunch')
        blob(-.36,.03,.51,(.33,.32,.44),'chest and mane');blob(-.43,-.04,.84,(.29,.28,.30),'head')
        blob(-.56,-.19,.78,(.20,.18,.14),'muzzle');blob(-.57,-.31,.80,(.105,.060,.061),'nose')
        for off in (-1,1):
            blob(-.43+off*.16,-.01,1.03,(.075,.079,.09),'ear')
            blob(-.49+off*.20,-.17,.17,(.26,.12,.115),'foreleg')
            blob(-.59+off*.19,-.26,.14,(.17,.13,.075),'paw')
        if not lod:
            for ang in np.linspace(0,math.tau,9,endpoint=False):
                blob(-.38+.22*math.cos(ang),.02+.23*math.sin(ang),.64,(.10,.094,.16),'mane locks')
        tail=[(cx+side*x,y+dy,z+h)for x,dy,h in [(.50,.12,.38),(.75,.20,.26),(.88,.08,.17),(.84,-.11,.145),(.69,-.20,.15),(.57,-.15,.17)]]
        b.tube(tail,.055,BRONZE,6 if lod else 9,label+'/tail')
