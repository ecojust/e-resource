"""Three sides of the southern courtyard from ECUPl's north-facing courtyard photograph."""
import numpy as np
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union
from photo_architecture import Facade
def install(b,lod,arch):
    half=arch.COURT/2;outer=arch.WIDTH/2
    first=arch.DEPTH;last=first+9*3.138;pitch=(last-first)/9
    floor=arch.FLOOR
    # Eight bays are identifiable in the published north-facing crop. The ninth fits the
    # independently measured return length in both aerials and is partly behind the photographer.
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
        spans=[((i-4)*pitch,pitch)for i in range(9)]
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
        for bay in [2,6]:
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
    width=7.66;fa=Facade(b,(-width/2,last),(width/2,last),'Cross wing / central three-bay pavilion')
    central_width=width/3
    gallery(fa,[(i*central_width,central_width)for i in [-1,0,1]],8.40,True,arch.WHITE)
    outline=Polygon([(-width/2,8.38),(width/2,8.38),(width/2,9.28),(0,10.24),(-width/2,9.28)])
    fa.prism(outline,-.31,.002,arch.WHITE,'three-medallion pavilion gable')
    for x in [-2.3,0,2.3]:
        disk=Point(x,8.92).buffer(.35 if x else .43,quad_segs=8 if lod else 16)
        fa.prism(disk,.012,.073,arch.RED if x else arch.STONE,'circular medallion')
        fa.prism(disk.buffer(.038).difference(disk),.015,.092,arch.RED,'medallion raised border')
    gable=Point(0,9.77).buffer(.18,quad_segs=9)
    fa.prism(gable,.009,.036,arch.DARK,'pediment round opening')
    halfdepth=4.45;cy=last+halfdepth
    for side in [-1,1]:
        left,right=sorted([side*half,side*width/2]);f=Facade(b,(left,last+.40),(right,last+.40),'Cross wing / outer arcade')
        gap=(right-left)/2
        gallery(f,[(-gap/2,gap),(gap/2,gap)],arch.COURT_EAVE)
    # The cross-wing roof extends to the outer side walls. Its ridge can be traced
    # independently from the front-wing roof in the two orthophotographs.
    sec=Polygon([(last-.47,8.38),(cy,10.64),(last+2*halfdepth+.56,8.38),
                  (last+2*halfdepth+.56,8.25),(cy,10.51),(last-.47,8.25)])
    b.prism(sec,-outer-.60,outer+.60,lambda y,z,x:(x,y,z),arch.TILE,'Cross wing/full tile shell')
    b.tube([(-outer+.22,cy,10.72),(outer-.22,cy,10.72)],.077,arch.TILE,9,'Cross wing/tile ridge')
    # The raised three-bay face has a secondary Chinese pediment and upturned ends.
    xs=np.linspace(-width/2-.34,width/2+.34,9)
    def heights(x):
        t=abs(x)/(width/2+.34)
        return 10.37-1.31*t+.39*t**6
    upper=[(x,heights(x))for x in xs]
    lower=[(x,z-.105)for x,z in reversed(upper)]
    b.prism(Polygon(upper+lower),-(last+4.32),-(last-.39),lambda x,z,d:(x,-d,z),arch.TILE,'Cross wing/pavilion tile cap')
    for side in [-1,1]:
        x=side*(width/2+.34)
        b.tube([(x-side*.48,last-.39,heights(x-side*.48)+.05),(x,last-.39,heights(x)+.05),(x+side*.20,last-.42,heights(x)+.22)],.052,arch.TILE,7,'Cross wing/pavilion swept corner')
    f=Facade(b,(-half,last+2.75),(half,last+2.75),'Cross wing / gallery rear face')
    openings=[box(x-.48,.12,x+.48,2.72)for x in [-7.7,-5.1,-2.5,0,2.5,5.1,7.7]]
    f.wall(0,8.37,holes=openings,material=arch.BRICK)
    for q in openings:f.prism(q,-.21,-.18,arch.RAIL,'rear door')
    for h in [.20,floor-.11]:
        b.box((0,last+1.54,h),(2*half,2.95,.17),arch.STONE,label='Cross wing/passage slab')
