"""The chapel gable, raking blind arcade and radial glass window in the 2020 photograph."""
from math import cos, pi, sin
from pathlib import Path

import numpy as np
from PIL import Image
from shapely.geometry import LineString, Point, Polygon, box

HERE = Path(__file__).resolve().parent
SPAN = 3.92
EAVE = 1.39
APEX = 3.99
CENTRE = 1.38
RADIUS = .99
WALL = 'Weathered grey roughcast'
STONE = 'Limestone face'
RETURN = 'Shaded inner reveal'
SOFFIT = 'Raking plaster arches'
CAP = 'Clay grey coping'
CAME = 'Dark metal glazing bars'
OLIVE = 'Muted amber green glass'
TEAL = 'Blue green inner panes'
AMBER = 'Terracotta central pane'
PALETTE = {name: dict(color=color, roughness=rough) for name, color, rough in [
    (WALL,[.56,.53,.49],.99),(STONE,[.86,.84,.76],.90),(RETURN,[.53,.53,.49],.92),
    (SOFFIT,[.82,.81,.76],.94),(CAP,[.32,.23,.20],.85),(CAME,[.045,.042,.036],.55),
    (OLIVE,[.32,.32,.22],.36),(TEAL,[.095,.26,.24],.35),(AMBER,[.34,.21,.17],.45)]}

def texture():
    path = HERE/'roughcast.png'
    if not path.exists():
        rng = np.random.default_rng(463)
        grit = rng.normal(209,8,(240,288))
        grit += 3*np.cos(np.arange(288)[None,:]/34) + 1.8*np.sin(np.arange(240)[:,None]/18)
        image = np.stack((grit+1,grit,grit-1.5),axis=-1)
        Image.fromarray(np.uint8(np.clip(image,0,255))).quantize(96).save(path)
    PALETTE[WALL]['texture'] = str(path)

def face(builder, outline, near, far, material, label):
    builder.prism(outline,-far,-near,lambda x,z,d:(x,-d,z),material,label)

def top(x):
    return APEX - abs(x)*(APEX-EAVE)/SPAN

def polar(radius, angle):
    return radius*cos(angle), CENTRE+radius*sin(angle)

def band(builder, profile, segments, material, label):
    vertices = []
    faces = []
    for radius, depth in profile:
        for i in range(segments):
            x,z = polar(radius,2*pi*i/segments)
            vertices.append((x,depth,z))
    for row in range(len(profile)-1):
        for i in range(segments):
            j=(i+1)%segments
            faces.append([row*segments+i,row*segments+j,(row+1)*segments+j,(row+1)*segments+i])
    builder.add(vertices,faces,material,label)

def inner_radius(a):
    # The inner colored ring follows a shallow, twelve-lobed line.
    return .436+.025*cos(12*a)

def glazing(builder, far):
    count=48 if far else 96
    half=2 if far else 5
    for i in range(24):
        a0=i*pi/12
        angles=[a0+j*pi/(12*half) for j in range(half+1)]
        outer=[polar(.891,a) for a in angles]
        inner=[polar(inner_radius(a),a) for a in angles]
        core=[polar(.095,a) for a in angles]
        face(builder,Polygon(outer+inner[::-1]),.099,.119,OLIVE,'Outer pane '+str(i+1))
        face(builder,Polygon(inner+core[::-1]),.096,.118,TEAL,'Inner pane '+str(i+1))
        spoke=LineString([polar(.095,a0),polar(.891,a0)]).buffer(.007,cap_style=2)
        face(builder,spoke,.075,.106,CAME,'Radial lead '+str(i+1))
    curve=[polar(inner_radius(2*pi*j/count),2*pi*j/count) for j in range(count+1)]
    face(builder,LineString(curve).buffer(.009,join_style=1),.074,.103,CAME,'Scalloped lead ring')
    centre=Point(0,CENTRE).buffer(.098,resolution=count//4)
    face(builder,centre,.090,.117,AMBER,'Central glass rondel')
    band(builder,[(.103,.102),(.103,.072),(.087,.072),(.087,.096)],count,CAME,'Centre lead')
    band(builder,[(.863,.068),(.856,.014),(.825,.006),(.807,.025),(.807,.099)],count,CAME,'Recessed glazing rebate')

def add_building(builder,far=False):
    texture()
    count=48 if far else 96
    shell=Polygon([(-SPAN,-.12),(SPAN,-.12),(SPAN,EAVE),(0,APEX),(-SPAN,EAVE)])
    opening=Point(0,CENTRE).buffer(.993,resolution=count//4)
    face(builder,shell.difference(opening),.001,.38,WALL,'Roughcast gable with circular opening')
    points=builder.parts[-1]['vertices']
    builder.parts[-1]['texcoords']=[[(x+SPAN)/(2*SPAN),(z+.12)/(APEX+.12)] for x,y,z in points]
    profile=[(1.001,.023),(1.006,-.036),(.994,-.069),(.868,-.068),(.848,-.041)]
    band(builder,profile,count,STONE,'Raised pale oculus surround')
    band(builder,[(.848,-.041),(.846,-.002),(.872,.068),(.889,.100)],count,RETURN,'Splayed reveal')
    glazing(builder,far)
    # Each raking bay has a horizontal spring line and a genuinely inset semicircular head.
    for side in (-1,1):
        for i in range(14):
            l,r=sorted([side*SPAN*i/14,side*SPAN*(i+1)/14])
            mid=(l+r)/2
            shoulder=top(mid)-.375
            outline=Polygon([(l,shoulder-.059),(r,shoulder-.059),(r,top(r)-.052),(l,top(l)-.052)])
            radius=(r-l)*.326
            arch=Point(mid,shoulder).buffer(radius,resolution=6 if far else 12).union(box(mid-radius,shoulder-.20,mid+radius,shoulder))
            face(builder,outline.difference(arch),-.095,-.005,SOFFIT,'Raking blind arch '+str(side)+' '+str(i+1))
        l,r=sorted([0,side*SPAN])
        for offset,height,depth,mat,label in [(-.081,.055,-.120,STONE,'Pale eaves lip'),(-.027,.060,-.133,CAP,'Coping lower course'),(.030,.045,-.098,CAP,'Coping top')]:
            band_shape=Polygon([(l,top(l)+offset),(r,top(r)+offset),(r,top(r)+offset+height),(l,top(l)+offset+height)])
            face(builder,band_shape,depth,.35,mat,label+' '+str(side))
    apex=Polygon([(-.13,APEX-.079),(.13,APEX-.079),(.074,APEX+.086),(0,APEX+.18),(-.074,APEX+.086)])
    face(builder,apex,-.116,.19,SOFFIT,'Raised gable coping terminal')
