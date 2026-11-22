"""The three separate lower arches and two pierced faces of the projecting balcony."""
import numpy as np
from scipy.optimize import least_squares
from shapely.geometry import Polygon,Point,box,LineString
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from registration import projected,plane,wall
from green_gable import CREAM,SASH,GLASS

TOP=float(plane([[210,557]],1,-.27)[0,2])
FRONT_POINTS=plane([[210,557],[353,505],[578,507]],2,TOP)
FOOT_PIXELS=[[215,634],[356,596],[579,596]]
BOTTOMS=[float(least_squares(lambda z:projected([[*q[:2],z[0]]])[0]-u,[TOP-.9]).x[0])for q,u in zip(FRONT_POINTS,FOOT_PIXELS)]
BASE=float(np.median(BOTTOMS))
ROUGH='Pebbled grey buff wall'
RELIEF='Cream cast fret'
BODY='Weathered cream parapet'
LIP='Pale coping stone'
SHADOW='Brown drip course'
def lower_windows(b,lod):
    f=Facade(b,(-.5,0),(.5,0),'Three arches')
    source=[[(216,425),(303,429),(259,388)],[(344,429),(429,431),(386,391)],[(469,430),(546,433),(505,396)]]
    apertures=[]
    for uv in source:
        l,r,head=wall(uv);spring=(l[1]+r[1])/2;w=r[0]-l[0]
        apertures.append(opening((l[0]+r[0])/2,BASE+.10,w,head[1]-BASE-.10,head[1]-spring,15 if lod else 34))
    left,right=-2.72,2.58
    shell=Polygon([(left,BASE-.86),(right,BASE-.86),(right,1.43),(left,1.56)])
    f.prism(shell.difference(unary_union(apertures)),-.32,0,ROUGH,'pierced principal wall')
    for i,shape in enumerate(apertures):
        label='Window '+str(i+1)
        x0,z0,x1,z1=shape.bounds;cx=(x0+x1)/2
        aperture=shape.buffer(-.053,join_style=2)
        f.prism(shape.difference(aperture),-.13,-.040,SASH,label+' curved wood frame')
        sash=[]
        for p,w in [(.25,.025),(.50,.060),(.75,.025)]:
            x=x0+(x1-x0)*p;sash.append(box(x-w/2,z0-.02,x+w/2,z1+.02))
        main_rail=float(wall([[(216+128*i+42),458+i*2]])[0,1])
        for z,w in [(main_rail,.157),(-.98,.037),(-1.53,.036),(.082,.026)]:
            sash.append(box(x0-.01,z-w/2,x1+.01,z+w/2))
        grid=unary_union(sash)
        f.prism(aperture.intersection(grid),-.096,-.051,SASH,label+' transom and glazing bars')
        panes=sorted(aperture.difference(grid).geoms,key=lambda p:(round(p.centroid.y,1),p.centroid.x))
        for j,p in enumerate(panes):
            f.prism(p.buffer(.005,join_style=2),-.135,-.128,GLASS[(j//3+i)%3],label+' glazing')
        f.prism(box(x0-.048,z0-.04,x1+.048,z0),-.015,.062,LIP,label+' lower sill')
    # The main wall discontinues behind the balcony. Its two short returns close the section.
    for x,d in [(left,-1),(right,1)]:
        b.box((x-d*.088,.67,(1.39+BASE-.86)/2),(.176,1.04,1.39-BASE+.86),ROUGH,label='Three arches/short side return')
def coords_on_face(face,uv):
    a=face.center[:2];n=face.n[:2]
    from registration import P,C
    eye=np.array(C['eye_enu_m']);ray=np.linalg.solve(P[:,:3],[*uv,1.])
    q=eye+ray*((a-eye[:2])@n/(ray[:2]@n))
    return float((q-face.center)@face.t),float(q[2])
def lattice(face,lod,uv,tag):
    # Cross and surrounding circular band remain separate from the frame on the diagonal corners.
    center,z=coords_on_face(face,uv)
    half_width=.443 if tag=='splayed'else .345
    # The face at a much sharper angle presents a narrow panel in the street image.
    height=TOP-BASE-.12
    opening=box(center-half_width,BASE+.055,center+half_width,BASE+.055+height)
    face.prism(box(-face.length/2,BASE,face.length/2,TOP).difference(opening),-.157,0,BODY,tag+' front with actual opening')
    x0,z0,x1,z1=opening.bounds
    inset=opening.buffer(-.023,join_style=2)
    face.prism(opening.difference(inset),-.118,.026,RELIEF,tag+' inset border')
    from shapely import affinity
    c=((x0+x1)/2,(z0+z1)/2);rx=(x1-x0)/2-.040;rz=(z1-z0)/2-.041
    outer=affinity.scale(Point(0,0).buffer(1,quad_segs=12 if lod else 26),rx,rz,origin=(0,0))
    inner=affinity.scale(Point(0,0).buffer(1,quad_segs=12 if lod else 26),rx-.057,rz-.062,origin=(0,0))
    ring=affinity.translate(outer.difference(inner),*c)
    ds=[LineString([(x0+.015,z0+.024),(x1-.027,z1-.021)]),LineString([(x0+.018,z1-.025),(x1-.019,z0+.022)])]
    web=unary_union([ring,*[ln.buffer(.045,cap_style=2)for ln in ds]]).intersection(inset)
    face.prism(web,-.112,-.008,RELIEF,tag+' circular and saltire fret')
    # The light on each diagonal also shows a narrower bevel at the mould face.
    front=web.buffer(-.009,join_style=2)
    face.prism(front,-.009,.002,LIP,tag+' fret raised face')
def balcony(b,lod):
    xy=FRONT_POINTS[:,:2];plan=Polygon([*xy,[2.28,.085],[-2.24,.12]])
    assert plan.is_valid
    deck=plan.buffer(.047,join_style=2)
    b.plan_prism(deck,BASE-.155,BASE,'Sandy stone slab','Balcony/slab and paving')
    b.plan_prism(deck.buffer(.017,join_style=2),BASE-.191,BASE-.148,SHADOW,'Balcony/lower drip moulding')
    b.plan_prism(deck.buffer(.030,join_style=2),BASE-.126,BASE-.082,LIP,'Balcony/stone edge roll')
    points=[*xy,[2.28,.085]]
    for i,(a,c) in enumerate(zip(points[:-1],points[1:])):
        name=['splayed','front','return'][i];face=Facade(b,a,c,'Balcony '+name)
        if i<2:lattice(face,lod,[[285,575],[458,548]][i],name)
        else:face.prism(box(-face.length/2,BASE,face.length/2,TOP),-.157,0,BODY,'side return')
        for z,h,d,mat,label in [(TOP+.014,.059,.235,LIP,'stone coping'),(TOP-.035,.037,.195,SHADOW,'coping drip'),(BASE+.018,.042,.184,LIP,'bottom bead')]:
            face.box(0,z,face.length+.034,h,d,-.065,mat,label)
    # The front projects over the lower bay. Keep only the visible stone band beneath.
    for i,(a,c) in enumerate(zip(points[:-1],points[1:])):
        face=Facade(b,a,c,'Bay below balcony')
        if i<2:
            face.prism(box(-face.length/2,BASE-.76,face.length/2,BASE-.18),-.16,-.042,ROUGH,'pebbled solid frieze')
            face.box(0,BASE-.72,face.length+.04,.078,.255,-.045,LIP,'string course')
    f=Facade(b,(-.5,0),(.5,0),'Pipe at right')
    line=[[2.36,-.074,1.39],[2.36,-.084,1.25],[2.31,-.115,1.19],[2.31,-.115,BASE-.84]]
    b.tube(line,.046,'Pale drainpipe',8 if lod else 14,'Pipe at right/round downpipe')
    for z in [.99,.12,-.91,-1.96,-2.93]:
        b.tube([[2.31,-.115,z-.020],[2.31,-.115,z+.020]],.055,'Pipe collar',8 if lod else 14,'Pipe at right/joints')

def pebble_finish(b,lod):
    """Small projecting chips on the original rough-cast street wall, between the three window cuts."""
    rng=np.random.default_rng(24051920)
    per=390 if lod else 1660
    colors=['Aggregate warm chip','Aggregate dark chip','Aggregate chalk chip']
    data=[([],[])for _ in colors]
    window_x=[(-2.04,-.95),(-.54,.54),(.94,1.95)]
    for n in range(per):
        x=rng.uniform(-2.70,2.56);z=rng.uniform(BASE-.83,1.39)
        if z<.55 and any(lo<x<hi for lo,hi in window_x):continue
        radius=rng.uniform(.006,.015)
        a=rng.uniform(0,np.pi*2);nside=4 if lod else 5
        pts=[(x+radius*np.cos(a+t*2*np.pi/nside),.001,z+.68*radius*np.sin(a+t*2*np.pi/nside))for t in range(nside)]
        verts,faces=data[n%3];v=len(verts);verts.extend([*pts,(x-.002,-radius*.38,z+.001),(x,.006,z)])
        for i in range(nside):
            j=(i+1)%nside;faces.extend([(v+i,v+j,v+nside),(v+j,v+i,v+nside+1)])
    for mat,(v,f)in zip(colors,data):b.add(v,f,mat,'Three arches/roughcast chips '+mat.split()[1])
