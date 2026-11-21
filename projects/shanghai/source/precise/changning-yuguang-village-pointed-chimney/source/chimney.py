"""The three-slot long face and single-slot end of a Yuguang Village roof chimney."""
from math import cos, pi, sin
from random import Random
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

def finish(rgb, roughness, metal=0.0):
    def channel(v):
        v=v/255
        return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
    return {'color':[channel(v) for v in rgb],'roughness':roughness,'metallic':metal}

PALETTE={'roughcast':finish((205,198,175),.96),'coarse lime grain':finish((230,222,201),1),
         'sand grain':finish((170,163,142),.95),'vent reveal':finish((166,147,109),.94),
         'shaft interior':finish((91,82,69),1),'dark metal flashing':finish((86,85,79),.68,.48),
         'weathered seam':finish((130,128,116),.72,.3)}

def crown(x,width,eaves,rise):
    return eaves+rise*(1-(abs(x)/width)**1.8)

def arched_slot(mid,half,bottom,spring,rise,detail):
    # Two curved shoulders approach a pointed head; the extruded polygon leaves
    # the full depth of the external screen open.
    pts=[(mid-half,bottom),(mid+half,bottom),(mid+half,spring)]
    for i in range(1,detail+1):
        u=i/detail
        pts.append((mid+half*cos(u*pi/2),spring+rise*(sin(u*pi/2)**1.45)))
    for i in range(detail-1,-1,-1):
        u=i/detail
        pts.append((mid-half*cos(u*pi/2),spring+rise*(sin(u*pi/2)**1.45)))
    return Polygon(pts)

def screen_outline(width,eaves,rise,detail):
    return Polygon([(-width,.10),(width,.10)]+
                   [(width-2*width*i/detail,crown(width-2*width*i/detail,width,eaves,rise))for i in range(detail+1)])

def add_building(b,lod=False):
    n=8 if lod else 30
    length=.70
    depth=.25
    def prism(panel,side,poly,a,c,mat):
        if side=='long':
            b.prism(poly,-c,-a,lambda u,z,v:(u,-v,z),mat,panel)
        else:
            b.prism(poly,-c,-a,lambda u,z,v:(v,u,z),mat,panel)
    faces=[
       ('long',length,1.59,.43,[-.40,0,.40],[1.46,1.67,1.46],[.19,.27,.19],.102,-depth,-depth+.10),
       ('end',depth,1.80,.24,[0],[1.71],[.20],.086,-length-.014,-length+.094)]
    for side,radius,eaves,rise,centres,springs,rises,half,outer,inner in faces:
        outline=screen_outline(radius,eaves,rise,n*2)
        holes=[arched_slot(x,half,.981,z,top,n)for x,z,top in zip(centres,springs,rises)]
        panel=outline.difference(unary_union(holes))
        prism(side+' roughcast screen',side,panel,outer,inner,'roughcast')
        for i,hole in enumerate(holes):
            edge=hole.difference(hole.buffer(-.006,join_style='mitre'))
            prism(side+' slot '+str(i+1)+' internal rebate',side,edge,outer+.016,inner+.006,'vent reveal')
        # The reverse lining is recessed well behind each aperture.
        prism(side+' soot-darkened inner lining',side,outline.buffer(-.025).intersection(box(-radius,.88,radius,eaves+rise)),inner+.069,inner+.089,'shaft interior')
        rng=Random(20200417+(side=='end'))
        for material in ('coarse lime grain','sand grain'):
            pts=[];tris=[]
            for i in range((460 if lod else 2600) if side=='long' else (180 if lod else 930)):
                u=rng.uniform(-radius+.008,radius-.008);z=rng.uniform(.106,eaves+rise-.005);size=rng.uniform(.0016,.0048)
                if not panel.contains(Point(u,z)) or any(h.distance(Point(u,z))<.007 for h in holes):continue
                def xyz(u,z,dist):return (u,dist,z) if side=='long' else (-dist,u,z)
                start=len(pts)
                pts.extend([xyz(u-size,z-size*.35,outer-.00025),xyz(u+size,z-size*.44,outer-.00025),xyz(u,z+size,outer-.00025),xyz(u+.10*size,z+.04*size,outer-.002)])
                tris.extend([(start,start+1,start+3),(start+1,start+2,start+3),(start+2,start,start+3)])
            b.add(pts,tris,material,side+' '+material)
    # Below all openings the shaft continues around the back. Unphotographed
    # upper exhaust channels and chimney pots are excluded.
    b.box((0,0,.50),(1.385,.486,1.0),'roughcast',label='lower rectangular shaft')
    b.box((0,-.255,.066),(1.455,.042,.118),'dark metal flashing',label='front apron flashing')
    b.box((.709,0,.066),(.042,.535,.118),'dark metal flashing',label='return flashing')
    b.box((0,-.278,.118),(1.451,.012,.015),'weathered seam',label='leading folded metal seam')
    b.box((.731,0,.118),(.012,.527,.015),'weathered seam',label='return folded seam')
