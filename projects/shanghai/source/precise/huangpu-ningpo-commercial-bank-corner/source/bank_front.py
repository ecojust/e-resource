"""The cut-corner portal and adjacent street bays of the Ningpo Commercial Bank."""
from math import cos, sin, pi
from pathlib import Path
import json

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from granite import texture_uv
from ornaments import add_corner_ornaments, ellipse_shape

SOURCE = Path(__file__).resolve().parent
EDGES = json.loads((SOURCE/'frontage-registration.json').read_bytes())['visible_edges_local_m']
GRANITE = 'bush-hammered granite'
TRIM = 'dressed warm grey stone'
JOINT = 'recessed granite joint'
DARK = 'dark bronze'
GLASS = 'recessed blue-grey glazing'
ROOF = 'roof flashing'
PALETTE = {
    GRANITE: {'color':[1,1,1], 'roughness':.90, 'texture':str(SOURCE/'granite.png')},
    TRIM: {'color':[.61,.56,.50], 'roughness':.79},
    JOINT: {'color':[.44,.40,.36], 'roughness':.92},
    DARK: {'color':[.19,.195,.19], 'roughness':.48, 'metallic':.32},
    GLASS: {'color':[.28,.35,.40], 'roughness':.30, 'metallic':.13},
    ROOF: {'color':[.38,.38,.37], 'roughness':.85},
}

def masonry(face, bottom, top, holes, distant):
    """Use one continuous backing with shallow coursing around the actual openings."""
    surface=face.wall(bottom,top,holes,.43,JOINT)
    course=.54 if bottom==0 else .68
    half=face.length/2
    n=0
    while bottom+n*course<top:
        lo=bottom+n*course
        hi=min(top,lo+course)
        length=(2.27 if bottom==0 else 2.70)*(1.28 if distant else 1)
        start=-half-(length*.52 if n%2 else 0)
        while start<half:
            tile=box(max(-half,start+.009),lo+.009,min(half,start+length-.009),hi-.009)
            if tile.area>.005:
                face.prism(tile.intersection(surface),-.008,.029,GRANITE,'ashlar face')
            start+=length
        n+=1

def frame(face, aperture, columns, rows, name):
    # The arched openings, window surrounds and door steps have different sills.
    # Keep the frame recessed inside the real cut while leaving the sill to each bay.
    x0,z0,x1,z1=aperture.bounds
    inner=aperture.buffer(-.09,join_style='mitre')
    outer=aperture.buffer(-.025,join_style='mitre')
    face.prism(aperture.buffer(.012,join_style='mitre'),-.34,-.32,GLASS,name+' glass')
    bars=[]
    for k in range(1,columns):
        x=x0+(x1-x0)*k/columns
        bars.append(box(x-.028,z0,x+.028,z1))
    for k in range(1,rows):
        z=z0+(z1-z0)*k/rows
        bars.append(box(x0,z-.027,x1,z+.027))
    panes=inner.difference(unary_union(bars))
    face.prism(outer.difference(panes),-.27,-.16,DARK,name+' frame')

def voussoirs(face, half_width, spring, rise, distant):
    # The joints radiate from the intrados and continue up to the projecting keystone.
    count=11 if distant else 17
    for i in range(count):
        start=pi*i/count+.008
        end=pi*(i+1)/count-.008
        steps=3 if distant else 5
        arc=[start+(end-start)*s/steps for s in range(steps+1)]
        crown=i==count//2
        delta=.41 if crown else .31
        ring=[(half_width*cos(t),spring+rise*sin(t))for t in arc]
        ring.extend(((half_width+delta)*cos(t),spring+(rise+delta)*sin(t))for t in reversed(arc))
        face.prism(Polygon(ring),.011,.107 if crown else .086,TRIM,'central wedge' if crown else 'radiating arch stone')

def lower(face, center, distant):
    width=2.70 if center else 2.28
    bottom=.24 if center else .95
    spring=4.12
    cap=1.05 if center else 1.24
    hole=opening(0,bottom,width,spring+cap-bottom,cap,16 if distant else 32)
    masonry(face,0,6.35,[hole],distant)
    frame(face,hole,2 if center else 3,1,'double entrance' if center else 'street arch glass')
    for u in (-width/2-.105,width/2+.105):
        face.box(u,(spring+bottom)/2,.21,spring-bottom,.13,.04,TRIM,'arch jamb')
    voussoirs(face,width/2,spring,cap,distant)
    face.box(0,spring-.32,width,.092,.075,-.205,DARK,'transom')
    if center:
        for u in (-.54,.54):
            face.box(u,1.42,.048,.48,.11,-.17,DARK,'paired door pull')
        for u in (-1.98,1.98):
            point=face.point(u,0,.34)
            ordinates=[(.02,.43),(.22,.43),(.30,.39),(.36,.43),(.45,.37),(.56,.31),
                       (5.67,.29),(5.76,.34),(5.82,.37),(5.98,.38),(6.08,.43)]
            face.builder.lathe(point[:2],ordinates,TRIM,16 if distant else 32,'corner portico lower column')
            face.box(u,6.17,.92,.19,.83,.34,TRIM,'lower column abacus')
        for i in range(3):
            face.box(0,.035+i*.082,2.65,.07,.45-i*.08,.18-i*.075,TRIM,'shallow entrance tread')
    else:
        for u in [-.74,-.38,0,.38,.74]:
            bounds=hole.intersection(LineString([(u,bottom),(u,6.32)])).bounds
            height=bounds[3]-bottom
            face.box(u,bottom+height/2,.027,height,.042,-.18,DARK,'arched grille upright')
        for z in (1.30,2.76,3.90,4.52):
            span=hole.intersection(LineString([(-2,z),(2,z)])).bounds
            face.box(0,z,span[2]-span[0],.036,.045,-.16,DARK,'street grille crossrail')
        face.box(0,.86,width+.28,.17,.28,.10,TRIM,'granite street sill')

def profiles(face, bands):
    for z,h,projection in bands:
        face.box(0,z,face.length,h,.12+projection,projection/2,TRIM,'continuous cornice course')

def curved_base(builder, z, halfwidth, chord, sag, height, name, distant):
    steps=10 if distant else 28
    front=[(halfwidth*(2*i/steps-1),chord-sag*(1-(2*i/steps-1)**2))for i in range(steps+1)]
    plate=Polygon([*front,(halfwidth,.32),(-halfwidth,.32)])
    builder.plan_prism(plate,z-height,z,TRIM,name)

def main_upper(face, distant):
    middle=box(-1.24,7.38,1.24,10.78)
    oval=ellipse_shape(0,14.04,.50,.85,distant)
    masonry(face,6.35,17.44,[middle,oval],distant)
    frame(face,middle,3,3,'tall balcony window')
    surround=middle.buffer(.15,join_style='mitre').difference(middle.buffer(.012))
    face.prism(surround,.027,.136,TRIM,'second floor window architrave')
    for z,w,h in [(10.94,2.83,.14),(11.09,3.00,.12),(11.75,2.65,.11),(12.02,2.75,.10)]:
        face.box(0,z,w,h,.23,.10,TRIM,'stepped stone between upper openings')
    for u in (-1.97,1.97):
        point=face.point(u,0,.26)
        profile=[(7.08,.47),(7.25,.47),(7.31,.41),(7.39,.44),(7.47,.40),(7.56,.37),(9.0,.37),(15.44,.31),(15.46,.33)]
        face.builder.lathe(point[:2],profile,TRIM,20 if distant else 36,'giant order shaft')
    curved_base(face.builder,7.18,1.81,-.52,.43,.37,'projecting balcony sill',distant)
    curved_base(face.builder,17.66,1.43,0,.32,.29,'curved parapet plinth',distant)
    add_corner_ornaments(face.builder,distant,materials={'stone':GRANITE,'trim':TRIM,'metal':DARK,'glass':GLASS})
    # The stone end screens rise above the short central roof balustrade.
    for sign in (-1,1):
        lo,hi=1.36,2.83
        polygon=Polygon([(sign*lo,17.49),(sign*hi,17.49),(sign*hi,18.80),(sign*lo,18.54)])
        face.prism(polygon,-.34,.029,GRANITE,'stone parapet end screen')
        lid=Polygon([(sign*lo,18.51),(sign*hi,18.77),(sign*hi,18.93),(sign*lo,18.67)])
        face.prism(lid,-.39,.106,TRIM,'parapet coping')

def wing_upper(face,distant):
    mid=box(-.94,7.65,.94,10.62)
    top=box(-.82,12.47,.82,14.78)
    masonry(face,6.35,17.44,[mid,top],distant)
    for hole,n in [(mid,'principal floor window'),(top,'top floor window')]:
        frame(face,hole,2,2,n)
        face.prism(hole.buffer(.15,join_style='mitre').difference(hole),.026,.12,TRIM,n+' architrave')
    for z,width in [(7.57,2.22),(10.79,2.27),(12.38,2.19)]:
        face.box(0,z,width,.15,.26,.125,TRIM,'street sill and lintel')
    lunette=opening(0,14.84,1.92,1.15,.93,14 if distant else 26)
    face.prism(lunette,.018,.11,GRANITE,'carved lunette tympanum')
    top_ring=lunette.buffer(.095).difference(lunette)
    face.prism(top_ring,.031,.162,TRIM,'arched lunette border')
    for i in range(-2,3):
        angle=pi/2+i*.36
        start=face.point(.20*cos(angle),15.00+.20*sin(angle),.117)
        end=face.point(.69*cos(angle),15.00+.60*sin(angle),.117)
        face.builder.tube([start,end],.022 if distant else .030,TRIM,5 if distant else 8,'simplified foliate lunette')
    for sign in (-1,1):
        face.box(sign*1.26,14.28,.15,3.89,.21,.065,TRIM,'upper pilaster strip')
    tympanum=Polygon([(-1.57,16.16),(0,17.20),(1.57,16.16)])
    face.prism(tympanum,-.05,.16,GRANITE,'triangular pediment')
    for sign in (-1,1):
        edge=LineString([(sign*1.67,16.15),(0,17.27)]).buffer(.095,cap_style='flat',join_style='mitre')
        face.prism(edge,.048,.27,TRIM,'sloping pediment moulding')
    face.box(0,16.10,3.31,.17,.30,.12,TRIM,'pediment sill')

def add_building(builder,distant):
    labels=['Beijing Road bay','cut corner','Jiangxi Road bay']
    for i,(a,b) in enumerate(zip(EDGES,EDGES[1:])):
        face=Facade(builder,a,b,labels[i])
        central=i==1
        lower(face,central,distant)
        if central:
            main_upper(face,distant)
        else:
            wing_upper(face,distant)
        profiles(face,[(.15,.27,.12),(6.34,.24,.22),(6.65,.35,.30),(6.88,.13,.36),
                       (7.00,.14,.44),(16.23,.18,.20),(16.93,.13,.28),(17.20,.23,.34),(17.46,.16,.41)])
        count=round(face.length/.49)
        for k in range(count):
            u=(k+.5)*face.length/count-face.length/2
            face.box(u,17.036,.16,.14,.19,.17,TRIM,'cornice dentil')
    roof=LineString(EDGES).buffer(1.54,single_sided=True,join_style='mitre',cap_style='flat')
    builder.plan_prism(roof,17.32,17.45,ROOF,'visible strip behind street cornice')
    for part in builder.parts:
        if part['material']==GRANITE:
            part['texcoords']=[(u,1-v) for u,v in (texture_uv(*p) for p in part['vertices'])]
