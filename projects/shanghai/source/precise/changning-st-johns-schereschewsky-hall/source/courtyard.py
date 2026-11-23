"""Three sides of the southern courtyard from ECUPl's north-facing courtyard photograph."""
import numpy as np
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade
def install(b,lod,arch):
    half=arch.COURT/2;outer=arch.WIDTH/2
    first=arch.DEPTH;last=46.40;pitch=(last-first)/11
    floor=arch.FLOOR
    # Eight bays are identifiable in the published north-facing crop. Eleven fit the
    # courtyard in the campus aerial and minimize the independent pier and bay-centre residuals from both ends.
    def gallery(f,spans,roof,bottom_rail=True,accent=None):
        cuts=[]
        for k,(u,p) in enumerate(spans):
            width=p-.42;bottom=.78
            lower=arch.curve(u,bottom,3.00,4.24,width,8 if lod else 15)
            top=arch.curve(u,floor+.065,roof-.67,roof-.30,width,8 if lod else 14,width*.28)
            cuts.extend([lower,top])
            arch.hood(f,lower,2.99,arch.RED,'lower brick arch head',.179)
            arch.hood(f,top,roof-.70,arch.RED,'upper flattened arch head',.105)
            if bottom_rail:arch.lattice(f,u,.80,width,.83,lod,'ground gallery railing')
            arch.lattice(f,u,floor+.06,width,.88,lod,'upper timber gallery railing')
        wall=box(-f.length/2,0,f.length/2,roof-.065).difference(unary_union(cuts))
        f.prism(wall,-.31,0,accent or arch.BRICK,'courtyard pier and arched wall')
        arch.projecting_bands(f,wall,[(1.64,.11),(3.01,.085),(floor-.05,.13),(6.05,.098),(7.24,.092)])
        f.box(0,.50,f.length,.58,.32,-.12,arch.STONE,'gallery stone base')
        f.box(0,floor-.115,f.length,.105,.38,-.065,arch.STONE,'gallery belt')
        f.box(0,roof-.018,f.length,.10,.54,-.13,arch.DARK,'upper eave beam')
    for side in (-1,1):
        x=half*side
        a,c=((x,first),(x,last)) if side<0 else ((x,last),(x,first))
        f=Facade(b,a,c,'South court / west arcade' if side<0 else 'South court / east arcade')
        spans=[((i-5)*pitch,pitch)for i in range(11)]
        gallery(f,spans,arch.COURT_EAVE)
        centre=(first+last)/2;corridor=2.10
        backx=x+side*corridor
        back=Facade(b,(backx,a[1]),(backx,c[1]),'Side gallery/recessed wall')
        windows=[];doors=[]
        for i,(u,p) in enumerate(spans):
            for h in [0.,floor]:
                if i%3==1:
                    doors.append(box(u-.58,h+.29,u+.58,h+2.69))
                else:windows.append(box(u-.76,h+1.15,u+.76,h+2.75))
        back.wall(0,arch.COURT_EAVE,windows+doors,material=arch.BRICK)
        for q in windows:back.window(q,2,3,arch.DARK,False,arch.GLASS,'passage window')
        for q in doors:back.prism(q,-.24,-.20,arch.RAIL,'passage door')
        for h in [.23,floor-.115]:
            b.box((x+side*corridor/2,centre,h),(corridor+.18,last-first,.17),arch.STONE,label='Side galleries/continuous passage floor')
        for bay in [2,8]:
            y=first+(bay+.5)*pitch
            for step in range(3):
                b.box((x-side*(.58-.19*step),y,.071*(step+1)),(.25,1.11,.142*(step+1)),arch.STONE,label='Side galleries/lawn steps')
        # The two roof edges and their ridge are measurable in both aerials. Only
        # the court-facing elevation has enough photographs to recover the whole arcade.
        xr=side*(half+outer)/2;xi=x-side*.48;xo=side*(outer+1.30)
        h0=arch.COURT_EAVE+.07
        section=Polygon([(min(xi,xo),h0),(xr,11.13),(max(xi,xo),h0),
                         (max(xi,xo),h0-.13),(xr,11.00),(min(xi,xo),h0-.13)])
        b.prism(section,-last+.03,-first-.07,lambda x,z,d:(x,-d,z),arch.TILE,'Side wing/dual-pitched tile roof')
        b.tube([(xr,first+.12,11.165),(xr,last-.13,11.165)],.063,arch.TILE,8,'Side wing/ridge')
        # Plain return mass spans the aerially visible teaching wing. Outer elevations
        # receive no count of street windows in the absence of a calibrated exterior.
        b.box((side*outer,centre,arch.COURT_EAVE/2),(.29,last-first,arch.COURT_EAVE),arch.BRICK,label='Side wing/outer shell')
    centre_x=-.22;width=8.40;fa=Facade(b,(centre_x-width/2,last),(centre_x+width/2,last),'Cross wing / central three-bay pavilion')
    central_width=width/3
    gallery(fa,[(i*central_width,central_width)for i in [-1,0,1]],8.40,True,arch.WHITE)
    outline=box(-width/2,8.37,width/2,9.46)
    fa.prism(outline,-.31,.002,arch.WHITE,'three-medallion pavilion gable')
    for x,z in [(-2.59,8.68),(.01,8.77),(2.72,8.76)]:
        disk=Point(x,z).buffer(.35 if abs(x)>1 else .43,quad_segs=8 if lod else 16)
        fa.prism(disk,.012,.073,arch.RED if abs(x)>1 else arch.STONE,'circular medallion')
        fa.prism(disk.buffer(.038).difference(disk),.015,.092,arch.RED,'medallion raised border')
    # Seen in the 2026 frontal photograph of the bust: a red five-pointed star
    # lies inside the central roundel, and the flanking disks have red borders.
    a=np.linspace(np.pi/2,np.pi/2+np.pi*2,11)[:-1]
    badge=Polygon([(.01+(.227 if i%2==0 else .094)*np.cos(q),8.77+(.227 if i%2==0 else .094)*np.sin(q))for i,q in enumerate(a)])
    fa.prism(badge,.081,.095,arch.RED,'central roundel five-pointed star')
    pediment=Facade(b,(centre_x-1.08,last+.87),(centre_x+1.08,last+.87),'Cross wing / recessed white pediment')
    face=Polygon([(-1.08,10.09),(1.08,10.09),(0,11.27)])
    eye=Point(0,10.53).buffer(.154,quad_segs=10)
    pediment.prism(face.difference(eye),-.16,.012,arch.WHITE,'upper gable')
    pediment.prism(eye,-.11,-.09,arch.DARK,'pediment aperture')
    halfdepth=3.80;cy=last+halfdepth
    for side in [-1,1]:
        left,right=sorted([side*half,centre_x+side*width/2]);f=Facade(b,(left,last+.40),(right,last+.40),'Cross wing / outer arcade')
        gap=(right-left)/2
        gallery(f,[(-gap/2,gap),(gap/2,gap)],arch.COURT_EAVE)
    # The cross-wing roof extends to the outer side walls. Its ridge can be traced
    # independently from the front-wing roof in the two orthophotographs.
    sec=Polygon([(last-.47,8.38),(cy,10.64),(last+2*halfdepth+.56,8.38),
                  (last+2*halfdepth+.56,8.25),(cy,10.51),(last-.47,8.25)])
    b.prism(sec,-outer-.60,outer+.60,lambda y,z,x:(x,y,z),arch.TILE,'Cross wing/full tile shell')
    b.tube([(-outer+.22,cy,10.72),(outer-.22,cy,10.72)],.077,arch.TILE,9,'Cross wing/tile ridge')
    # The school northward image has a lower transverse swept eave between its
    # three medallions and a short, raised white gable. Only the central triangle is plaster.
    from rear_courts import folded_roof
    xs=np.linspace(-width/2-.34,width/2+.34,21)
    pts=[];faces=[]
    for row,(dy,eave,rise) in enumerate([(-.62,9.38,.65),(-.23,9.54,.38),(.35,9.88,.19),(.95,10.19,.065)]):
        for x in xs:
            k=abs(x)/(width/2+.34);pts.append((centre_x+x,last+dy,eave+rise*k**5))
        if row:
            for i in range(len(xs)-1):
                old=(row-1)*len(xs)+i;new=row*len(xs)+i
                faces.append((old,old+1,new+1,new))
    folded_roof(b,pts,faces,arch.TILE,'Cross wing / lower swept eave')
    for side in [-1,1]:
        x=side*(width/2+.34)
        b.tube([(centre_x+x-side*.43,last-.60,9.80),(centre_x+x,last-.62,10.03),(centre_x+x+side*.16,last-.64,10.25)],.054,arch.TILE,8,'Cross wing/swept tip')
    higher=[(-1.17,10.14),(0,11.38),(1.17,10.14),(1.17,10.04),(0,11.28),(-1.17,10.04)]
    b.prism(Polygon([(x+centre_x,z)for x,z in higher]),-(last+3.21),-(last+.78),lambda x,z,d:(x,-d,z),arch.TILE,'Cross wing / upper gable roof')
    f=Facade(b,(-half,last+2.75),(half,last+2.75),'Cross wing / gallery rear face')
    openings=[box(x-.48,.12,x+.48,2.72)for x in [-7.7,-5.1,-2.5,0,2.5,5.1,7.7]]
    f.wall(0,8.37,holes=openings,material=arch.BRICK)
    for q in openings:f.prism(q,-.21,-.18,arch.RAIL,'rear door')
    for h in [.20,floor-.11]:
        b.box((0,last+1.54,h),(2*half,2.95,.17),arch.STONE,label='Cross wing/passage slab')

    # The institutional photograph and the 2004 rear portrait both show a pale
    # pebble path on the centreline, with closely cut lawn either side.
    from shapely.geometry import box as footprint
    court=footprint(-half+.02,first+.04,half-.02,last-.05)
    middle=footprint(-.86,first+.03,.86,last-.02)
    margins=court.difference(court.buffer(-.68,join_style=2))
    walkway=unary_union([middle,margins]).intersection(court)
    b.plan_prism(walkway,-.09,-.014,'court pebble paving','Courtyard/pebble path')
    b.plan_prism(court.difference(walkway.buffer(.014,join_style=2)),-.072,-.008,'lawn grass','Courtyard/grass on two sides of path')
    back=box(-outer,last+2*halfdepth-.30,outer,last+2*halfdepth+.0)
    b.plan_prism(back,0,8.28,arch.BRICK,'Cross wing/rear closure to the northern courts')
