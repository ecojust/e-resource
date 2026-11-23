"""House shells around the independent east fronts, the garden porch and the hipped main roof."""
from math import sqrt
import numpy as np
from shapely.geometry import box,Polygon
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient
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
def clipped_main_roof(f,vertices,mask,label):
    """Trim the hipped roof to the photographed and mapped north-west recess."""
    if mask is None:
        roof_panel(f,vertices,TILE,label)
        return
    uvz=np.asarray(vertices); uv=uvz[:,:2]
    face=Polygon(uv)
    clipped=face.intersection(mask)
    if clipped.equals(face):
        roof_panel(f,vertices,TILE,label)
        return
    slope=np.linalg.lstsq(np.c_[uv,np.ones(len(uv))],uvz[:,2],rcond=None)[0]
    for poly in ([clipped] if clipped.geom_type=='Polygon' else clipped.geoms):
        if poly.is_empty or poly.area<.001:continue
        poly=orient(poly,sign=1);points=list(poly.exterior.coords)[:-1];n=len(points)
        ids={p:i for i,p in enumerate(points)};faces=[]
        xyz=[f.point(u,d,slope@[u,d,1]-t)for t in (.115,0)for u,d in points]
        for tri in constrained_delaunay_triangles(poly).geoms:
            a,b,c=[ids[x]for x in list(orient(tri,sign=1).exterior.coords)[:3]]
            faces.extend([(a,c,b),(a+n,b+n,c+n)])
        faces.extend((i,(i+1)%n,(i+1)%n+n,i+n)for i in range(n))
        f.b.add(xyz,faces,TILE,f.name+' | '+label)
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
    g0,g1=side,9.03;gm=(g0+g1)/2;ze=6.36;peak=9.00
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
    north=f.name=='1-2';umin=-6.72 if north else -6.55;umax=6.72 if north else 6.85;depth=11.65 if north else 12.90
    def plate(umin,umax,d0,d1,z,h,mat,label):
        f.rect(umin,umax,z,z+h,-d1,-d0,mat,label)
    # The north house has a north-west re-entrant corner on the original
    # city footprint that is also visible between the 2021 roof and the trees.
    notch_u,notch_d=3.20,6.50
    def indoor_slab(a,b,d0,d1,z,h,label):
        if north:
            plate(a,notch_u-.13,d0,d1,z,h,STEP,label)
            plate(notch_u-.13,b,d0,notch_d-.13,z,h,STEP,label)
        else:plate(a,b,d0,d1,z,h,STEP,label)
    indoor_slab(umin,umax,1.56,depth,.0,.08,'floor within garden shell')
    plate(-1.08,umax,.13,1.56,.0,.08,STEP,'floor behind lane front')
    indoor_slab(umin+.12,umax-.12,1.64,depth-.13,(3.43 if north else 3.65)-.16,.16,'upper floor in original roofed range')
    add_stair(f,lod)
    # Streetward wall behind the climbing stair. End photo shows one tall upper window.
    recessed=box(umin,.02,-1.035,7.04).difference(box(-2.70,3.85,-1.01,6.50))
    x0,x1=(-5.20,-4.15) if north else (-5.20,-4.03)
    recessed=recessed.difference(box(x0,4.78,x1,6.33))
    f.solid(recessed,-1.82,-1.55,CREAM,'cream return behind external stair')
    window(f,x0,x1,4.78,6.33,-1.55,3,4,'stair-side upper casement',lod)
    f.rect(-2.78,-1.00,3.83,6.55,-2.52,-2.48,DARK,'shaded upper entrance behind stair landing')
    f.rect(-2.67,-1.11,6.43,6.53,-1.62,-1.49,OAK,'tie at stair-head porch')
    garden(f,umin,depth-(2.03 if north else 1.70),lod)
    # The two blind returns are simplified where the garden tree canopy hides alterations.
    rear=f.face(umax,depth,-1,0)
    rear.rect((umax-notch_u if north else .01),umax-umin-.01,.02,6.38,-.235,0,CREAM,'garden back enclosure')
    end=f.face(umax,0,0,1)
    d_end=notch_d if north else depth
    end.rect(.02,d_end-.015,.02,3.43 if north else 3.65,-.23,0,BRICK,'red brick garden return')
    panel=box(.02,3.43 if north else 3.65,d_end-.015,6.40)
    # The side elevation visible in Gao's photograph 09 has dark horizontal
    # and vertical members in plaster. Later garden fittings are omitted.
    holes=[box(1.39,4.30,2.18,5.72),box(3.01,4.30,3.78,5.72)]
    for opening in holes:panel=panel.difference(opening)
    end.solid(panel,-.23,0,CREAM,'plastered garden return upper storey')
    for r in holes:
        a,z,b,top=r.bounds;window(end,a,b,z,top,0,2,3,'garden return sash',lod,False)
    for level in [3.54 if north else 3.76,4.23,6.23]:
        end.rect(.015,min(5.2,d_end-.024),level-.062,level+.062,.005,.064,OAK,'garden return framing rail')
    for x in [.13,1.25,2.40,4.04]:
        end.rect(x-.071,x+.071,3.53 if north else 3.75,6.30,.009,.066,OAK,'garden return stud')
    # A long hipped roof crosses the pair of street gables. Oblique southern print
    # also records a hipped dormer with vertical glazing in its garden slope.
    ua,ub=umin+.22,umax+.19;dlo,dhi=1.20,depth+.18;mid=(dhi+dlo)/2
    za,zt=6.35,9.46;ra,rb=ua+2.05,ub-2.17
    mask=box(ua-.5,dlo-.5,ub+.5,dhi+.5).difference(box(notch_u+.13,notch_d+.13,ub+1,dhi+1)) if north else None
    for edge in (dlo,dhi):
        clipped_main_roof(f,[(ua,edge,za),(ub,edge,za),(rb,mid,zt),(ra,mid,zt)],mask,'hipped main roof')
    for u,r in [(ua,ra),(ub,rb)]:clipped_main_roof(f,[(u,dlo,za),(r,mid,zt),(u,dhi,za)],mask,'main roof hip')
    if north:
        def height(u,d):
            pct=min(1.,(ub-u)/(ub-rb),(dhi-d)/(dhi-mid),(d-dlo)/(mid-dlo))
            return za+(zt-za)*pct-.05
        # West-facing recess wall then its north-facing return; both follow the hip to its soffit.
        setback=f.face(umax,notch_d,-1,0)
        span=umax-notch_u
        top=[(s,height(umax-s,notch_d)) for s in np.linspace(0,span,10)]
        setback.solid(Polygon([(0,.02),(span,.02),*reversed(top)]),-.20,0,CREAM,'west face of original recessed corner')
        returnwall=f.face(notch_u,notch_d,0,1)
        top=[(s,height(notch_u,notch_d+s))for s in np.linspace(0,depth-notch_d,10)]
        returnwall.solid(Polygon([(0,.02),(depth-notch_d,.02),*reversed(top)]),-.20,.0,CREAM,'north return of original recessed corner')
    for spec,n in zip(bays,('principal','projecting')):
        a,b,e,crest,front=spec
        # Close the clay return over the plane of the main hipped roof. The
        # large cross ridge is taller and runs farther into the building than
        # the short projecting window bay.
        if n=='principal':
            for u,sgn in [(a,-1),(b,1)]:
                side=f.face(u,4.17,0,-1 if sgn==-1 else 1)
                start=0 if sgn==-1 else -4.17
                web=box(start,3.44,start+4.17,e)
                if sgn==-1:
                    opening=box(2.60,3.84,4.00,6.62)
                    web=web.difference(opening)
                    side.solid(opening,-.55,-.52,DARK,'shadowed side of porch above brick stair')
                    side.rect(2.70,3.72,3.89,5.99,-.50,-.45,DOOR,'upper dwelling door within porch')
                    side.rect(2.62,3.99,6.48,6.62,-.10,.014,OAK,'porch head beam')
                side.solid(web,-.17,.0,CREAM,'plastered cross-gable flank')
            for edge in (a-.19,b+.19):
                roof_panel(f,[(edge,4.17,e+.033),(edge,6.18,7.44),((a+b)/2,6.18,9.48),((a+b)/2,4.17,crest+.093)],TILE,'cross ridge running into main hip')
        pitched(f,a-.19,b+.19,-front-.22,4.17 if n=='principal' else 2.97,e+.033,crest+.093,n+' lane gable')
    chimney=-2.26 if north else -2.47
    plate(chimney-.38,chimney+.38,2.10,3.09,5.76,2.98,CREAM,'chimney haunch below twin shafts')
    plate(chimney-.43,chimney+.43,2.05,3.14,8.71,.13,SILL,'projecting ledge on chimney haunch')
    for flue in range(2):
        d=2.135+flue*.476
        plate(chimney-.262,chimney+.262,d,d+.444,8.80,2.63,BRICK,'red brick chimney shaft '+str(flue+1))
        for z,wide,h in [(11.21,.033,.105),(11.36,.071,.16),(11.52,.035,.087)]:
            plate(chimney-.262-wide,chimney+.262+wide,d-wide,d+.444+wide,z,h,BRICK,'corbelled individual flue cap')
        plate(chimney-.182,chimney+.182,d+.064,d+.38,11.607,.012,DARK,'dark chimney flue opening')
    # Sash dormer overlooks the garden on the broad slope.
    dorm=f.face(1.20,depth-1.24,-1,0); dorm.rect(-.72,.72,6.51,7.98,-.19,.0,OAK,'garden dormer front')
    window(dorm,-.57,.57,6.64,7.83,.245,4,3,'garden dormer window',lod,False)
    for mirror in (-1,1):
        roof_panel(f,[(1.2+mirror*.90,depth-.90,7.92),(1.2+mirror*.90,depth-2.58,7.92),
                      (1.2,depth-2.15,8.56),(1.2,depth-1.74,8.56)],TILE,'garden dormer hip flank')
    roof_panel(f,[(.30,depth-.90,7.92),(2.10,depth-.90,7.92),(1.20,depth-1.74,8.56)],TILE,'garden dormer front hip')
