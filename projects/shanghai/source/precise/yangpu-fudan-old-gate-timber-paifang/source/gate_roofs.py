"""Curved tiled eaves, barrel ridges and the four lifted corners of the old gate."""
import math
import numpy as np
from shapely.geometry import Polygon
TILE='Fudan | dark grey clay'
NOSE='Fudan | grey ridge tile'
TIMBER='Fudan | weathered cypress'
DARK='Fudan | dark eave timber'
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
    ridge_y=center_y if ridge_y is None else ridge_y
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
        count=(20 if lod else 35) if not small else (6 if lod else 10)
        for k in range(count+1):
            a=k/count
            pts=[]
            for t in np.linspace(0,1,steps+1):
                x,y,h=fit(a,t);pts.append([x,y,h+.021])
            b.tube(pts,.027 if small else .039,NOSE,5 if lod else 8,label+'/covered tile roll '+str(k))
        pts=[list(fit(a,0))for a in np.linspace(0,1,nx+1)]
        for p in pts:p[2]-=.092 if not small else .059
        b.tube(pts,.049 if small else .069,TIMBER if not small else TILE,6 if lod else 10,label+'/eave fascia')
    for sign in (-1,1):
        # Fan the end field into the end of the horizontal ridge. The final
        # narrow slice is solid at the ridge, so no singular top edge is extruded.
        def hip(a,t):
            h=z(1.,t)
            e=(abs(2*a-1)**2.7)
            h-=(tip-base)*(1-e)*(1-t)**1.55
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
        width0=.35 if small else .58;rise=.25 if small else .41
        x=center+sign*(ridge-.39 if not small else ridge-.19)
        curve=[(0,0),(.46,.02),(.66,.19),(.61,.43),(.76,.70),(1,.75),(.82,.95),(.57,1.00),(.35,.78),(.22,.49),(.02,.38)]
        outline=Polygon([(x+sign*a*width0,high+.07+z*rise)for a,z in curve])
        b.prism(outline,-.053,.053,lambda x,h,d:(x,ridge_y-d,h),NOSE,label+'/ridge terminal curl')
