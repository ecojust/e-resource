"""Curved tiled eaves, barrel ridges and the four lifted corners of the old gate."""
import math,json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
TILE='Fudan | dark grey clay'
NOSE='Fudan | grey ridge tile'
TIMBER='Fudan | weathered cypress'
DARK='Fudan | dark eave timber'
FINIAL='Fudan | pale glazed ridge ornaments'
ORNAMENT=json.loads((Path(__file__).resolve().parents[1]/'measurements/ridge-ornaments.json').read_bytes())['parameters']
def field(b,label,fn,na,nb,mat,thickness):
    vertices=[]
    for z in (0,-thickness):
        for i in range(na+1):
            for j in range(nb+1):
                x,y,h=fn(i/na,j/nb);vertices.append([x,y,h+z])
    m=(na+1)*(nb+1);faces=[]
    for i in range(na):
        for j in range(nb):
            a=i*(nb+1)+j;c=a+nb+1
            faces.extend([(a,c,c+1,a+1),(m+a+1,m+c+1,m+c,m+a)])
    perimeter=list(range(0,na*(nb+1)+1,nb+1))
    perimeter+=list(range(na*(nb+1)+1,m))
    perimeter+=list(range(m-1-(nb+1),nb-1,-(nb+1)))+list(range(nb-1,0,-1))
    for a,c in zip(perimeter,perimeter[1:]+perimeter[:1]):faces.append((c,a,a+m,c+m))
    # Parameter order is reversed on the back and on one short end.
    tri=np.array(vertices);v0=tri[faces[0][0]];a=tri[faces[0][1]]-v0;c=tri[faces[0][2]]-v0
    if np.cross(a,c)[2]<0:faces=[tuple(reversed(face))for face in faces]
    b.add(vertices,faces,mat,label)
def lifted_roof(b, center, width, depth, center_y, low, high, tip, lod, label, small=False,ridge_y=None):
    """A hipped roof with a concave main slope, outward-curving corners and a solid soffit."""
    half=width/2;dh=depth/2;ridge=half*(.70 if small else .842);base=low+.10
    ridge_y=center_y if ridge_y is None else ORNAMENT['y']
    nx=10 if lod else 20;steps=4 if lod else 8
    def xf(a,t):
        return center+(2*a-1)*((1-t)*half+t*ridge)
    def z(a,t):
        uplift=(max(abs(a*2-1)-.58,0)/.42)**2.7
        return base+(high-base)*(.42*t+.58*t*t)+(tip-base)*uplift*(1-t)**1.55
    for side in (-1,1):
        def fit(a,t):
            return xf(a,t),ridge_y*t+(center_y+side*dh)*(1-t),z(a,t)
        field(b,label+f' / curved tile field {side}',fit,nx,steps,TILE,.105 if not small else .074)
        # Longitudinal crown tiles sit above the dark pantile field. The dark
        # concave band in each row remains exposed between the raised rolls.
        count=49 if not small else 11
        for k in range(count+1):
            a=k/count
            pts=[]
            for t in np.linspace(0,1,steps+1):
                x,y,h=fit(a,t);pts.append([x,y,h+.021])
            roll=.031 if small else .041
            b.tube(pts,roll,NOSE,5 if lod else 8,label+'/covered tile roll '+str(k))
            # Circular tile ends project beyond the timber eave fascia.
            x,y,h=fit(a,0)
            b.tube([[x,y+side*.035,h+.011],[x,y+side*.072,h-.014]],roll*1.22,NOSE,6 if lod else 10,label+'/tile nose '+str(k))
            if not lod and not small:
                for t in (.24,.50,.76):
                    x,y,h=fit(a,t);x2,y2,h2=fit(a,t+.022)
                    b.tube([[x,y,h+.021],[x2,y2,h2+.021]],roll*1.11,NOSE,7,label+'/tile collar '+str(k))
        pts=[list(fit(a,0))for a in np.linspace(0,1,nx+1)]
        for p in pts:p[2]-=.092 if not small else .059
        b.tube(pts,.049 if small else .069,TIMBER if not small else TILE,6 if lod else 10,label+'/eave fascia')
    for sign in (-1,1):
        # Fan the end field into the end of the horizontal ridge. The final
        # narrow slice is solid at the ridge, so no singular top edge is extruded.
        def hip(a,t):
            h=z(1.,t)
            e=(abs(2*a-1)**2.7)
            h-=min(.16, .23*(tip-base))*(1-e)*(1-t)**1.55
            return center+sign*((1-t)*half+t*ridge),ridge_y*t+(center_y+(2*a-1)*dh)*(1-t),h
        verts=[];faces=[]
        for iz in (0,-.08):
            start=len(verts)
            for t in np.linspace(0,1,steps+1)[:-1]:
                for a in np.linspace(0,1,7):
                    x,y,h=hip(a,t);verts.append([x,y,h+iz])
            verts.append([center+sign*ridge,ridge_y,high+iz])
        n=7*steps+1
        for i in range(steps-1):
            for j in range(6):
                a=i*7+j;faces.append((a,a+1,a+8,a+7))
        for j in range(6):a=(steps-1)*7+j;faces.append((a,a+1,n-1))
        top=list(faces);faces.extend(tuple(n+x for x in reversed(f)) for f in top)
        boundary=list(range(7))+list(range(13,n-1,7))+[n-1]+list(range((steps-1)*7,0,-7))
        faces.extend((c,a,a+n,c+n)for a,c in zip(boundary,boundary[1:]+boundary[:1]))
        if sign<0:faces=[tuple(reversed(x))for x in faces]
        b.add(verts,faces,TILE,label+'/hip end')
        for side in (-1,1):
            pts=[]
            for t in np.linspace(0,1,steps+1):
                x,y,h=hip(0 if side<0 else 1,t);pts.append([x,y,h+.055])
            b.tube(pts,.053 if small else .075,NOSE,7 if lod else 11,label+'/hip corner rib')
    # Raised straight ridge over the scalloped curved bands.
    b.tube([[center-ridge,ridge_y,high+.076],[center+ridge,ridge_y,high+.076]],.076 if small else .108,NOSE,8 if lod else 14,label+'/long ridge')
    for sign in (-1,1):
        width0=.19 if small else .31
        rise=.19 if small else ORNAMENT['height']
        x0=center+sign*(ridge-.20 if small else ORNAMENT['half_spacing'])
        base_z=high+.07 if small else ORNAMENT['z_foot']
        # The front, side and reverse photographs all show the pale glazed ornaments
        # inboard of the long dark ridge ends, with their upper heads turned inward.
        curve=[(-.31,0),(.21,.01),(.62,.15),(.75,.28),(.37,.19),(.16,.20),
               (.08,.31),(.23,.38),(.48,.38),(.34,.48),(.02,.48),(-.14,.62),
               (-.11,.75),(.02,.85),(.34,.88),(.48,.83),(.44,.94),
               (.29,.99),(.32,1.04),(.10,1.00),(-.14,.89),(-.38,.78),
               (-.54,.59),(-.58,.38),(-.54,.16)]
        outline=Polygon([(x0-sign*a*width0,base_z+z*rise)for a,z in curve])
        b.prism(outline,-.048,.048,lambda x,h,d:(x,ridge_y-d,h),FINIAL,label+'/pale inward-facing ridge ornament')
