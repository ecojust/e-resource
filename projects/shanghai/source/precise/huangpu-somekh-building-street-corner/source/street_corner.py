"""The reopened round bank porch, projecting iron balconies and repaired low drum."""
from pathlib import Path
from math import cos,sin,radians,pi
import json
import numpy as np
from shapely.geometry import Polygon,LineString,box
from shapely import affinity
from photo_architecture import Facade,opening
from sign_lettering import lettering_shapes
from finish import WALL,GRANITE,TRIM,BED,BASE,IRON,SASH,GLASS,DOOR,TERRAZZO,CAP,LETTER
from south_front import rail,arch_ring
REG=json.loads(Path(__file__).with_name('frontage-registration.json').read_text())
CENTER=np.array(REG['southeast_circle_center_m'])
R=REG['radius_m']
SWEEP=radians(REG['corner_sweep_deg'])
SOUTH=-pi/2
MID=SOUTH+SWEEP/2
END=SOUTH+SWEEP
FONT=Path(__file__).parent/'fascia_font/SomekhFasciaStudy.otf'

def radial(angle):
    return np.array([cos(angle),sin(angle)])

def point(angle,radius):
    return CENTER+radial(angle)*radius

def radial_face(builder,theta,distance,label):
    mid=point(theta,distance)
    u=radial(theta+pi/2)
    return Facade(builder,mid-u,mid+u,label)

def sector(inner,outer,a,b,steps):
    angles=np.linspace(a,b,steps+1)
    return Polygon([*[point(t,outer) for t in angles],*[point(t,inner)for t in angles[::-1]]])

def band(builder,r_in,r_out,z0,z1,material,n,lod,a=SOUTH,b=END,label='curved stone course'):
    steps=max(4,round(n*(b-a)/SWEEP))
    builder.plan_prism(sector(r_in,r_out,a,b,steps),z0,z1,material,label)

def name_band(builder,text,z,width,height,radius,lod):
    # The English and Chinese inscriptions follow the cylindrical face. A separate
    # tangent at each glyph avoids burying the end letters inside the curved beam.
    for _,glyph in lettering_shapes(text,width,height,font=FONT):
        a,_,b,_=glyph.bounds
        u=(a+b)/2
        face=radial_face(builder,MID+u/radius,radius,'corner name')
        local=affinity.translate(glyph,xoff=-u,yoff=z).simplify(.005 if lod else .0015,preserve_topology=True)
        face.prism(local,-.008,.034,LETTER,'relief lettering')

def porch(builder,lod):
    segments=18 if lod else 42
    # Only the outer lip meets the raised street. The shallow steps sit at the recessed door.
    band(builder,R-2.06,R+.035,-.055,.045,TERRAZZO,segments,lod,label='terrazzo pavement')
    door_face=radial_face(builder,MID,R-1.55,'corner inner door')
    u=1.16
    door_hole=box(-u,.07,u,4.12)
    wall=box(-1.38,0,1.38,4.81).difference(door_hole)
    door_face.prism(wall,-.38,.016,WALL,'recessed door jambs')
    door_face.prism(door_hole,-.17,-.095,GLASS,'inner glazed double door')
    frame=door_hole.difference(box(-u+.10,.17,u-.10,4.02))
    door_face.prism(frame,-.09,.035,DOOR,'inner door frame')
    for x in (-u/2,u/2):
        door_face.box(x,.68,1.06,.88,.13,-.045,DOOR,'wood door lower panels')
        door_face.box(x,2.9,1.08,.075,.09,-.02,DOOR,'door glazing rail')
        for xx in (-.31,0,.31):
            door_face.box(x+xx,2.19,.025,1.94,.043,.015,IRON,'inner door iron grille')
    door_face.box(0,2.10,.075,4.04,.13,-.012,DOOR,'center stile')
    for i in range(2):
        door_face.box(0,.10+i*.09,2.45-i*.08,.125, .34,.20-i*.26,TERRAZZO,'inner threshold steps')
    for theta in (MID-SWEEP*.247,MID+SWEEP*.247):
        cx,cy=point(theta,R-.29)
        profile=[(.045,.31),(.13,.33),(.19,.31),(.24,.28),(.31,.295),(.37,.245),
                 (3.96,.220),(4.06,.24),(4.12,.255),(4.19,.29),(4.25,.34),(4.32,.35)]
        builder.lathe((cx,cy),profile,GRANITE,16 if lod else 30,'porch freestanding granite columns')
        face=radial_face(builder,theta,R-.29,'porch capitals')
        face.box(0,4.34,.77,.14,.73,0,TRIM,'abacus')
        for side in (-1,1):
            curve=[face.point(side*.25+.092*cos(t),4.22+.079*sin(t),.258)for t in np.linspace(0,2*pi,11 if lod else 21)]
            builder.tube(curve,.025,TRIM,6,'porch capital volutes')
    # Two side abutments (not a full cylindrical ground wall) leave the portico open.
    back_center=point(MID,R-1.55)
    tangent=radial(MID+pi/2)
    for s in (-1,1):
        t=SOUTH if s<0 else END
        edge=point(t,R)
        rear=back_center+s*1.36*tangent
        edge_inner=point(t,R-1.36)
        # Order by the actual ground plan: use the street corner, back wall and inner return.
        shell=Polygon([edge,point(t+s*.055,R),rear+s*.18*tangent,rear,edge_inner]).buffer(0)
        if shell.area>.03:builder.plan_prism(shell,.045,4.55,WALL,'portico sides')
    for z0,z1,out,mat in [(4.43,4.59,.14,TRIM),(4.59,4.91,.03,GRANITE),(4.91,5.44,.08,WALL),
                           (5.44,5.55,.26,TRIM),(5.55,5.98,.17,GRANITE),(5.98,6.12,.29,TRIM)]:
        band(builder,R-1.74,R+out,z0,z1,mat,segments,lod,label='curved entrance fascia')
    name_band(builder,'樓大美沙',5.13,2.10,.33,R+.09,lod)
    name_band(builder,'THE SOMEKH BUILDING',5.76,3.93,.129,R+.18,lod)

def round_floors(builder,lod,levels,height):
    # Three window faces across the round corner are divided by actual stone piers.
    samples=[0,.206,.32,.68,.794,1.]
    for i,(lo,hi) in enumerate(zip(samples,samples[1:])):
        a,b=SOUTH+SWEEP*lo,SOUTH+SWEEP*hi
        left,right=point(a,R),point(b,R)
        face=Facade(builder,left,right,'corner bay')
        w=face.length;holes=[]
        if i in (0,2,4):
            # Round projecting balconies documented on both middle floors and the attic.
            width=.82 if i!=2 else 1.42
            for row,(bottom,top) in enumerate(levels):
                opening_shape=opening(0,bottom,width,top-bottom,.15 if row==2 else 0,12 if lod else 20)
                holes.append(opening_shape)
                face.window(opening_shape,columns=2,rows=3,frame=SASH,glass=GLASS,trim=False,label='corner steel casements')
                arch_ring(face,opening_shape,.10,GRANITE,.12,'corner sash edge')
                if row>0:rail(face,0,bottom-.03,width+.12,lod,balcony=row<3)
        else:
            for row,(bottom,top) in enumerate(levels):
                face.box(0,(bottom+top)/2,.28,top-bottom+.44,.21,.045,GRANITE,'pier in curved wall')
                if row>=2:
                    for side in (-1,1):
                        f=Polygon([(0,top-.40),(side*.13,top-.29),(side*.09,top-.01),(0,top-.16)])
                        face.prism(f,.12,.22,TRIM,'carved corner pier leaves')
        face.wall(6.08,height,holes,thickness=1.36,material=WALL)
    n=22 if lod else 52
    for z0,z1,out in [(6.81,6.94,.20),(18.10,18.25,.22),(18.25,18.43,.39),(18.43,18.54,.52),
                       (22.15,22.31,.24),(22.31,22.48,.43),(22.48,22.60,.55)]:
        band(builder,R-1.36,R+out,z0,z1,TRIM,n,lod)
    for theta in np.linspace(SOUTH+.025,END-.025,15 if lod else 23):
        face=radial_face(builder,theta,R+.21,'corner cornice')
        face.box(0,18.14,.12,.21,.37,0,TRIM,'dentils')

def drum(builder,lod):
    # The conservation architect's interior photograph shows an open rear rim
    # and daylight through the arched openings. The original tall dome is gone.
    radius=R-.22
    count=6
    subdivisions=8 if lod else 16
    for i in range(count):
        theta=MID+i*2*pi/count
        a=theta-pi/count;b=theta+pi/count
        half=radius*pi/count
        hole=opening(0,23.45,.63,.84,.315,12 if lod else 24)
        body=box(-half,22.38,half,25.53).difference(hole)
        surround=hole.buffer(.105,join_style='mitre').difference(hole)
        def mapper(u,z,d):return (*point(theta+u/radius,radius+d),z)
        edges=np.linspace(-half,half,subdivisions+1)
        for lo,hi in zip(edges,edges[1:]):
            strip=box(lo,22.,hi,26.)
            builder.prism(body.intersection(strip),-.35,0,mapper,WALL,'open drum curved wall')
            builder.prism(surround.intersection(strip),-.018,.12,mapper,TRIM,'drum window archivolt')
        for sign in (-1,1):
            face=radial_face(builder,theta+sign*pi/count*.92,radius,'open drum')
            face.box(0,23.38,.13,1.49,.21,.042,TRIM,'drum panel joint')
        band(builder,radius-.40,radius+.072,25.52,25.67,TRIM,subdivisions*count,lod,a,b,'open drum coping')
        band(builder,radius-.38,radius+.15,22.43,22.57,TRIM,subdivisions*count,lod,a,b,'drum base course')
    floor=Polygon([point(t,radius-.21)for t in np.linspace(0,2*pi,49 if lod else 97)[:-1]])
    builder.plan_prism(floor,22.32,22.41,BASE,'base inside open drum')

def add_corner(builder,lod,levels,height):
    porch(builder,lod)
    round_floors(builder,lod,levels,height)
    drum(builder,lod)
