"""House shells around the independent east fronts, the garden porch and the hipped main roof."""
from math import sqrt
import numpy as np
from shapely.geometry import box,Polygon
from materials import *
from joinery import window
from northern_front import BIG,SMALL,FLOOR
from staircase import add_stair

def roof_panel(f,vertices,material,label,thickness=.115):
    # vertices specify the outer upper surface. Normalize face winding upward.
    verts=np.array([f.point(*p)for p in vertices])
    if np.cross(verts[1]-verts[0],verts[2]-verts[1])[2]<0:verts=verts[::-1]
    n=len(verts);xyz=list(verts-np.array([0,0,thickness]))+list(verts)
    faces=[]
    for j in range(1,n-1):
        faces.extend([(0,j+1,j),(n,n+j,n+j+1)])
    faces.extend((j,(j+1)%n,(j+1)%n+n,j+n)for j in range(n))
    f.b.add(xyz,faces,material,f.name+' | '+label)
def pitched(f,a,b,front,back,eave,ridge,label):
    mid=(a+b)/2
    for edge in (a,b):
        roof_panel(f,[(edge,front,eave),(edge,back,eave),(mid,back,ridge),(mid,front,ridge)],TILE,label+' clay slope')
        f.rail([(edge,front,eave-.052),(mid,front,ridge-.052)],.083,BARGE,label+' weathered verge',10)
    f.rail([(mid,front,ridge+.017),(mid,back,ridge+.017)],.071,SILL,label+' ridge tiles',10)
def garden(f,umin,dmax,lod):
    s=f.face(umin,dmax,0,-1)
    # The large arch is slightly pointed at its centre. The 1935 print shows
    # short nearly vertical shoulders and two shallow arcs to a central apex.
    side=4.35
    arch=Polygon([(.41,0),(side-.33,0),(side-.33,2.29),(side-.40,2.52),
       (side-.57,2.64),(2.67,2.76),(2.19,2.86),(1.79,2.77),(.70,2.65),(.49,2.50),(.41,2.29)])
    s.solid(box(0,.02,side,3.12).difference(arch),-.27,0,CREAM,'garden Tudor arch and supporting piers')
    for x in [-.01,side-.22]:
        butt=Polygon([(x-.13,.04),(x+.36,.04),(x+.28,1.61),(x+.19,2.02),(x+.19,2.43),(x-.014,2.43)])
        s.solid(butt,.005,.236,CREAM,'slender buttress at garden arch')
    s.rect(.22,side-.16,.025,.093,-1.69,.14,STEP,'garden porch raised paving')
    s.rect(.14,side-.07,2.94,3.10,-1.73,.065,OAK,'garden loggia floor and fascia')
    back=box(0,.1,side,2.96).difference(box(1.19,.11,2.20,2.64))
    s.solid(back,-1.92,-1.72,CREAM,'recessed garden porch rear wall')
    s.rect(1.19,2.20,.11,2.64,-1.96,-1.935,DOOR,'garden porch door in recess')
    s.rect(.0,side,3.12,5.95,-1.93,-1.71,CREAM,'upper veranda internal wall')
    window(s,1.18,2.24,3.38,5.24,-1.696,3,4,'upper loggia rear casement',lod,False)
    for x in (.14,1.40,2.85,side-.14):
        s.rect(x-.073,x+.073,3.10,5.86,-.11,.05,OAK,'open loggia timber post')
        for sign in (-1,1):
            if .05<x+sign*.48<side-.06:s.band([(x,5.26),(x+sign*.45,5.77)],.086,-.07,.032,OAK,'garden veranda knee brace')
    for z in (3.22,3.79,3.90):s.rect(.07,side-.07,z-.047,z+.047,-.13,.029,OAK,'garden veranda handrail')
    for i in range(16 if not lod else 10):
        x=.25+(side-.49)*i/(15 if not lod else 9)
        s.rect(x-.034,x+.034,3.24,3.75,-.085,.012,OAK,'garden loggia baluster')
    s.rect(.01,side-.01,5.68,5.84,-.14,.08,OAK,'garden canopy tie')
    # A second, plastered gable along the same end carries large rectangular lights in both floors.
    g0,g1=side,9.03;gm=(g0+g1)/2;ze=5.95;peak=8.64
    win=[(gm-.81,.97,gm+.81,2.37),(gm-.80,3.79,gm+.80,5.20)]
    section=Polygon([(g0,0),(g1,0),(g1,ze),(gm,peak),(g0,ze)])
    for x,z,xx,zz in win:section=section.difference(box(x,z,xx,zz))
    s.solid(section,-.25,0,CREAM,'plaster garden gable with two floor openings')
    for x,z,xx,zz in win:window(s,x,xx,z,zz,0,5,4,'garden-end broad window',lod)
    s.rect(g1-.006,dmax-1.40,.02,5.78,-2.32,-2.10,CREAM,'short lateral return behind outdoor stair')
    # Coordinates of this roof ridge run northward from the end gable.
    m=dmax-gm;lo=dmax-g1-.18;hi=dmax-g0+.17
    for edge in (lo,hi):
        roof_panel(f,[(umin-.25,edge,ze+.08),(umin+4.65,edge,ze+.08),(umin+4.65,m,peak+.07),(umin-.25,m,peak+.07)],TILE,'garden end gabled roof')
        f.rail([(umin-.25,edge,ze+.03),(umin-.25,m,peak+.02)],.074,BARGE,'garden end verge')
    roof_panel(f,[(umin-.19,dmax+.18,5.70),(umin+3.4,dmax+.18,5.70),(umin+3.4,dmax-side,7.89),(umin-.19,dmax-side,7.89)],TILE,'loggia roof area')
def add_body(f,lod=False,bays=(BIG,SMALL)):
    north=f.name=='1-2';umin=-6.72 if north else -6.55;umax=6.72 if north else 6.85;depth=11.28 if north else 11.62
    def plate(umin,umax,d0,d1,z,h,mat,label):
        f.rect(umin,umax,z,z+h,-d1,-d0,mat,label)
    plate(umin,umax,1.56,depth,.0,.08,STEP,'floor within garden shell')
    plate(-1.08,umax,.13,1.56,.0,.08,STEP,'floor behind lane front')
    plate(umin+.12,umax-.12,1.64,depth-.13,(3.43 if north else 3.65)-.16,.16,STEP,'upper floor in original roofed range')
    add_stair(f,lod)
    # Streetward wall behind the climbing stair. End photo shows one tall upper window.
    recessed=box(umin,.02,-1.035,6.50)
    x0,x1=umin+.91,umin+1.95
    recessed=recessed.difference(box(x0,4.09,x1,5.84))
    f.solid(recessed,-1.82,-1.55,CREAM,'cream return behind external stair')
    window(f,x0,x1,4.09,5.84,-1.55,3,4,'stair-side upper casement',lod)
    garden(f,umin,depth,lod)
    # The two blind returns are simplified where the garden tree canopy hides alterations.
    rear=f.face(umax,depth,-1,0)
    rear.rect(.01,umax-umin-.01,.02,5.78,-.235,0,CREAM,'garden back enclosure')
    end=f.face(umax,0,0,1)
    end.rect(.02,depth-.02,.02,5.81,-.23,0,CREAM,'northern return wall')
    # A long hipped roof crosses the pair of street gables. Oblique southern print
    # also records a hipped dormer with vertical glazing in its garden slope.
    ua,ub=umin+.22,umax+.19;dlo,dhi=1.20,depth+.18;mid=(dhi+dlo)/2
    za,zt=6.35,9.46;ra,rb=ua+2.05,ub-2.17
    for edge in (dlo,dhi):
        roof_panel(f,[(ua,edge,za),(ub,edge,za),(rb,mid,zt),(ra,mid,zt)],TILE,'hipped main roof')
    for u,r in [(ua,ra),(ub,rb)]:roof_panel(f,[(u,dlo,za),(r,mid,zt),(u,dhi,za)],TILE,'main roof hip')
    for spec,n in zip(bays,('principal','projecting')):
        a,b,e,crest,front=spec
        # Close the clay return over the plane of the main hipped roof. The
        # large cross ridge is taller and runs farther into the building than
        # the short projecting window bay.
        if n=='principal':
            for u,sgn in [(a,-1),(b,1)]:
                side=f.face(u,4.17,0,-1 if sgn==-1 else 1)
                start=0 if sgn==-1 else -4.17
                side.rect(start,start+4.17,3.44,e,-.17,.0,CREAM,'plastered cross-gable flank')
            for edge in (a-.19,b+.19):
                roof_panel(f,[(edge,4.17,e+.033),(edge,6.18,7.44),((a+b)/2,6.18,9.48),((a+b)/2,4.17,crest+.093)],TILE,'cross ridge running into main hip')
        pitched(f,a-.19,b+.19,-front-.22,4.17 if n=='principal' else 2.97,e+.033,crest+.093,n+' lane gable')
    chimney= -2.63 if north else -2.51
    plate(chimney-.31,chimney+.30,2.18,2.97,5.72,5.94,BRICK,'paired-flue brick chimney shaft')
    for z,w,h in ((11.36,.06,.13),(11.55,.095,.21),(11.76,.045,.09)):
        plate(chimney-.31-w,chimney+.30+w,2.18-w,2.97+w,z,h,BRICK,'stepped red chimney head')
    for j in range(2):plate(chimney-.21,chimney+.20,2.23+j*.34,2.52+j*.34,11.85,.012,DARK,'two open chimney flues')
    # Sash dormer overlooks the garden on the broad slope.
    dorm=f.face(1.20,depth-1.24,-1,0); dorm.rect(-.72,.72,6.51,7.98,-.19,.0,OAK,'garden dormer front')
    window(dorm,-.57,.57,6.64,7.83,.245,4,3,'garden dormer window',lod,False)
    for mirror in (-1,1):
        roof_panel(f,[(1.2+mirror*.90,depth-.90,7.92),(1.2+mirror*.90,depth-2.58,7.92),
                      (1.2,depth-2.15,8.56),(1.2,depth-1.74,8.56)],TILE,'garden dormer hip flank')
    roof_panel(f,[(.30,depth-.90,7.92),(2.10,depth-.90,7.92),(1.20,depth-1.74,8.56)],TILE,'garden dormer front hip')
