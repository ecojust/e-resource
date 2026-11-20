"""Set out the joining nave and transept roofs, two aisle slopes, and canted chancel."""
import numpy as np
from math import cos, pi, sin
from shapely.geometry import Polygon

SLATE='slate roof'
RIDGE='lipped roof stone'
HALF=5.82
CROSS_Y=34.50
TRANSVERSE_HALF=4.72
NAVE_END=39.50
APSE_START=39.26
APSE_TANGENT=41.36
APSE_RADIUS=5.09
APSE_HALF=5.48
APSE_EAVE=9.14
APSE_PEAK=12.15
EAVE=12.52
PEAK=18.14


def slope(b,pts,label):
    vertices=[list(q) for q in pts]
    n=len(vertices)
    faces=[(0,i,i+1) for i in range(1,n-1)]
    # Both sides of the plate close against a visible fascia.
    vertices.extend([(x,y,z-.16) for x,y,z in pts])
    faces.extend([(n,n+i+1,n+i) for i in range(1,n-1)])
    for i in range(n):
        j=(i+1)%n;faces.extend([(i,n+i,j),(j,n+i,n+j)])
    b.add(vertices,faces,SLATE,label)


def add_roofs(b,lod):
    y0=-.18;y1=NAVE_END
    for sign in (-1,1):
        x=sign*HALF
        # Re-entrant valley meeting on the common ridge at the crossing.
        slope(b,[(0,y0,PEAK),(x,y0,EAVE),(x,CROSS_Y-TRANSVERSE_HALF,EAVE),(0,CROSS_Y,PEAK)],'Nave/east roof')
        slope(b,[(0,CROSS_Y,PEAK),(x,CROSS_Y+TRANSVERSE_HALF,EAVE),(x,y1,EAVE),(0,y1,PEAK)],'Nave/west roof')
        b.tube([(x,y0,EAVE),(x,CROSS_Y-TRANSVERSE_HALF,EAVE)],.078,RIDGE,7,'Nave/eave gutter')
        end=14.03 if sign<0 else 13.12
        for side in (-1,1):
            yy=CROSS_Y+side*TRANSVERSE_HALF
            slope(b,[(0,CROSS_Y,PEAK),(x,yy,EAVE),(sign*end,yy,EAVE),(sign*end,CROSS_Y,PEAK)],
                  'Transept/slate pitches')
        b.tube([(0,CROSS_Y,PEAK+.045),(sign*end,CROSS_Y,PEAK+.045)],.115,RIDGE,9,'Transept/ridge')
        # The low lean-to over the inner aisle and the public covered walk.
        inner,outer=sign*5.66,sign*12.24
        slope(b,[(inner,-.07,10.14),(outer,-.07,6.07),(outer,CROSS_Y-TRANSVERSE_HALF,6.07),(inner,CROSS_Y-TRANSVERSE_HALF,10.14)],'Aisle/pitched roof')
        b.tube([(outer,-.07,6.07),(outer,CROSS_Y-TRANSVERSE_HALF,6.07)],.077,RIDGE,7,'Aisle/eaves')
        # Closely spaced horizontal tile courses, individually modelled only in the near mesh.
        if not lod:
            for k in range(1,16):
                t=k/16;p=x*t;z=PEAK+(EAVE-PEAK)*t+.024
                b.tube([(p,y0+.07,z),(p,CROSS_Y-TRANSVERSE_HALF*t,z)],.020,SLATE,5,'Nave/slate courses')
    b.tube([(0,y0,PEAK+.045),(0,y1,PEAK+.045)],.12,RIDGE,10,'Nave/ridge')
    # The 2025 owner-published overhead photograph shows a round western end
    # and a short straight barrel behind the transept, with two lower side roofs.
    n=12 if lod else 28
    for i in range(n):
        alpha=pi*i/n;beta=pi*(i+1)/n
        def cross(a,y):
            return (APSE_HALF*cos(a),y,APSE_EAVE+(APSE_PEAK-APSE_EAVE)*sin(a))
        slope(b,[cross(alpha,APSE_START),cross(beta,APSE_START),
                 cross(beta,APSE_TANGENT),cross(alpha,APSE_TANGENT)],'Chancel/barrel slate roof')
    ring_count=4 if lod else 9
    for level in range(ring_count):
        t0=pi*.5*level/ring_count;t1=pi*.5*(level+1)/ring_count
        for i in range(n):
            phi=pi*i/n;theta=pi*(i+1)/n
            def dome(t,a):
                return (APSE_HALF*cos(t)*cos(a),APSE_TANGENT+APSE_RADIUS*cos(t)*sin(a),
                        APSE_EAVE+(APSE_PEAK-APSE_EAVE)*sin(t))
            quad=[dome(t0,phi),dome(t0,theta),dome(t1,theta)]
            if level<ring_count-1:quad.append(dome(t1,phi))
            b.add(quad,[(0,k,k+1) for k in range(1,len(quad)-1)],SLATE,'Chancel/rounded slate half-dome')
    for sign in (-1,1):
        low,high=5.44,10.25 if sign>0 else 11.17
        annex=Polygon([(sign*low,39.19),(sign*high,39.19),(sign*high,44.20),(sign*low,44.20)])
        b.plan_prism(annex,5.74,5.94,SLATE,'Chancel/side annex flat roof')
