"""The east courtyard face of Xiangguang Hall after its 2017 restoration.

X follows the documented east wall toward north-northwest. Y points inside.
The roof is limited to the visible eave and its junction with the retained hall.
"""
import json
import math
from pathlib import Path

import numpy as np
from shapely import set_precision
from shapely.affinity import translate
from shapely.geometry import LineString, box
from shapely.ops import unary_union

from photo_architecture import Facade
from sign_lettering import lettering_shapes

SOURCE = Path(__file__).resolve().parent
FRAME = json.loads((SOURCE / 'frontage-registration.json').read_text())
AXES = FRAME['full_bay_bounds']
HALF = FRAME['width_m'] / 2
BACK = FRAME['rear_depth_m']
POST = 'Warm brown timber'
PANEL = 'Honey brown panels'
RELIEF = 'Carved timber relief'
SILL = 'Pale timber skirts'
SASH = 'Narrow dark wood'
GLASS = 'Blue grey upper glass'
LOW_GLASS = 'Shaded porch glazing'
BASE = 'Warm stone stair'
TILE = 'Grey roof tiles'
RIDGE = 'Grey cylindrical covers'
DARK = 'Doorway and cut surfaces'
INK = 'Black plaque'
GOLD = 'Gilded plaque lettering'
MATERIALS = {
    POST: {'color': [.46,.29,.22], 'roughness': .76},
    PANEL: {'color': [.56,.38,.28], 'roughness': .77},
    RELIEF: {'color': [.61,.42,.31], 'roughness': .76},
    SILL: {'color': [.72,.64,.49], 'roughness': .81},
    SASH: {'color': [.235,.16,.14], 'roughness': .74},
    LOW_GLASS: {'color': [.22,.25,.25], 'roughness': .39, 'metallic': .12},
    GLASS: {'color': [.33,.42,.45], 'roughness': .37, 'metallic': .12},
    BASE: {'color': [.58,.49,.39], 'roughness': .93},
    TILE: {'color': [.28,.30,.295], 'roughness': .88},
    RIDGE: {'color': [.36,.37,.35], 'roughness': .87},
    DARK: {'color': [.23,.20,.17], 'roughness': .94},
    INK: {'color': [.10,.092,.065], 'roughness': .68},
    GOLD: {'color': [.91,.72,.30], 'roughness': .58, 'metallic': .17},
}
LANDING = .55
EAVE = 6.78


def panel(face, u0, u1, z0, z1, d0, d1, material, name):
    face.box((u0+u1)/2, (z0+z1)/2, u1-u0, z1-z0,
             d1-d0, (d0+d1)/2, material, name)


def stroke(face, coords, thickness, depth, material, label):
    section = LineString(coords).buffer(thickness/2, cap_style=2, join_style=2)
    face.prism(section, depth-.02, depth+.015, material, label)


def lattice(face, u0, u1, z0, z1, leaves, depth, distant, name, glazing=GLASS):
    """Narrow casements, each with two pointed diamond lights and horizontal rails."""
    panel(face,u0,u1,z0,z1,depth-.075,depth-.025,glazing,name+' glazing')
    step=(u1-u0)/leaves
    border=.038 if distant else .035
    bars=[box(u0,z0,u1,z0+border),box(u0,z1-border,u1,z1)]
    bars.extend(box(u0+step*i-border/2,z0,u0+step*i+border/2,z1)
                for i in range(leaves+1))
    mid=(z0+z1)/2
    bars.append(box(u0,mid-.022,u1,mid+.022))
    for i in range(leaves):
        center=u0+(i+.5)*step
        for row in range(2):
            z=z0+(row+.5)*(z1-z0)/2
            rx=step*.255
            rz=(z1-z0)*.165
            # The four fine spurs reach the adjacent rail or the side of the light.
            loop=[(center,z+rz),(center+rx,z),(center,z-rz),(center-rx,z),(center,z+rz)]
            bars.append(LineString(loop).buffer(.014 if distant else .012,join_style=2))
            if not distant:
                for sign in (-1,1):
                    bars.append(box(center+min(sign*rx,sign*step/2),z-.012,
                                    center+max(sign*rx,sign*step/2),z+.012))
    face.prism(unary_union(bars),depth,depth+.031,SASH,name+' diamond lights')


def fret(face, left, right, top, depth, name, distant):
    """Open square fret hung from the beam. Stepped returns deepen towards both posts."""
    width=right-left
    unit=width/max(7,round(width/.38))
    n=round(width/unit)
    bars=[box(left,top-.065,right,top)]
    for i in range(n):
        x=left+i*unit
        for dx,drop,w,h in ((.04,.22,.05,.22),(.04,.22,.63,.047),
                             (.62,.31,.047,.13),(.62,.31,.34,.044)):
            bars.append(box(x+dx*unit,top-drop,x+(dx+w)*unit,top-drop+h))
        if not distant:
            bars.append(box(x+.25*unit,top-.105,x+.30*unit,top-.045))
    for sign in (-1,1):
        corner=left if sign==1 else right
        for i in range(3):
            pos=corner+sign*(.06+i*.16)
            z=top-(.59-i*.10)
            other=pos+sign*(.22+i*.018)
            bars.append(box(min(pos,other),z,max(pos,other),z+.055))
            bars.append(box(pos-.027,z,pos+.027,top-.15))
    face.prism(unary_union(bars),depth-.05,depth+.018,RELIEF,name+' open fret')


def floral_band(face,left,right,center_z,d,distant,name):
    """Paired leafy scrolls in the recessed horizontal frieze."""
    width=right-left
    panel(face,left,right,center_z-.24,center_z+.24,d-.10,d-.024,POST,name+' sunk band')
    panel(face,left+.025,right-.025,center_z-.204,center_z+.204,d-.038,d-.010,PANEL,name+' frieze')
    for z in (center_z-.234,center_z+.234,center_z+.142):
        panel(face,left,right,z-.023,z+.023,d-.019,d+.026,RELIEF,name+' border')
    cells=max(2,round(width/.75))
    for i in range(cells):
        x=left+(i+.5)*width/cells
        for sign in (-1,1):
            points=[]
            for t in np.linspace(0,1,6 if distant else 10):
                ang=-.35+1.57*math.pi*t
                rad=.125*(1-.51*t)
                points.append((x+sign*(.10+.062*t+rad*math.cos(ang)),center_z+rad*math.sin(ang)))
            stroke(face,points,.032 if distant else .038,d+.018,RELIEF,name+' carved scrolls')
        if not distant:
            for sign in (-1,1):
                branches=[(x-.27*sign,center_z-.068),(x-.19*sign,center_z-.115),
                          (x-.08*sign,center_z-.055),(x+.045*sign,center_z+.035)]
                stroke(face,branches,.030,d+.022,RELIEF,name+' frieze branches')
            stroke(face,[(x-.071,center_z-.082),(x,center_z+.113),(x+.071,center_z-.082)],
                   .035,d+.023,RELIEF,name+' carved buds')


def inner_closure(face,left,right,d,distant,name,door=False):
    base=LANDING+.035
    if door:
        # The photograph shows a standing gap between the two leaves.
        opening=.44
        for sign in (-1,1):
            u0,u1=sorted([sign*opening/2,sign*1.02])
            panel(face,u0,u1,base,1.72,d-.07,d,POST,name+' paired leaves')
            lattice(face,u0,u1,1.72,3.10,2,d+.015,distant,name+' leaf',LOW_GLASS)
            panel(face,u0+.07,u1-.07,.72,1.58,d-.017,d+.025,PANEL,name+' leaf panels')
        panel(face,-opening/2,opening/2,base,3.10,d-.45,d-.42,DARK,name+' inner reveal')
        for a,b in [(left,-1.02),(1.02,right)]:
            panel(face,a,b,base,1.52,d-.08,d,POST,name+' side panels')
            lattice(face,a,b,1.52,3.11,2,d+.018,distant,name+' sidelights',LOW_GLASS)
        panel(face,left,right,3.08,3.55,d-.12,d+.025,POST,name+' door lintel')
        panel(face,-1.09,1.09,2.78,3.20,d+.035,d+.104,GOLD,name+' plaque edge')
        panel(face,-1.065,1.065,2.801,3.178,d+.092,d+.132,INK,name+' plaque')
        for char,glyph in lettering_shapes('堂光香',1.63,.285,font=SOURCE/'HallPlaque.otf'):
            outline=set_precision(translate(glyph,yoff=2.990).simplify(.0018,preserve_topology=True),.0001)
            face.prism(outline,d+.128,d+.145,GOLD,name+' '+char)
    else:
        panel(face,left,right,base,1.62,d-.045,d+.024,POST,name+' base panels')
        if not distant:
            count=max(3,round((right-left)/.54))
            each=(right-left)/count
            for k in range(count):
                panel(face,left+k*each+.04,left+(k+1)*each-.04,
                      base+.09,1.52,d+.020,d+.039,PANEL,name+' lower panels')
        lattice(face,left,right,1.62,3.16,max(3,round((right-left)/.56)),d+.038,distant,name+' screen',LOW_GLASS)
        panel(face,left,right,3.16,3.57,d-.055,d+.039,POST,name+' screen head')


def gallery_bay(face,left,right,i,distant):
    name='Bay '+str(i+1)
    c=(left+right)/2
    inner_closure(face,left+.08,right-.08,-1.54,distant,name,door=i==3)
    panel(face,left,right,3.92,4.35,-.14,.095,PANEL,name+' interstorey')
    floral_band(face,left+.13,right-.13,3.76,.095,distant,name)
    fret(face,left+.14,right-.14,3.505,.057,name,distant)
    panel(face,left,right,4.30,5.01,-.085,.003,SILL,name+' panelled skirt')
    leaves=max(4,round((right-left)/.515))
    lattice(face,left+.095,right-.095,5.02,6.12,leaves,-.012,distant,name+' upper')
    panel(face,left,right,6.13,6.65,-.14,.022,POST,name+' upper head')
    if not distant:
        for j in range(1,leaves):
            u=left+j*(right-left)/leaves
            panel(face,u-.006,u+.006,4.36,4.98,.002,.015,PANEL,name+' boards')


def roof_height(x,y):
    turn=min(1,max(0,(abs(x)-(HALF-2.85))/2.85))
    dist=max(0,(y+1.02)/5.72)
    return EAVE+.95*dist+.40*dist**2+.51*turn**2*(1-.76*dist)


def eave_and_roof(b,distant):
    xs=np.linspace(-HALF-.43,HALF+.43,19 if distant else 35)
    ys=np.linspace(-1.02,BACK,6 if distant else 10)
    verts=[(x,y,roof_height(x,y))for y in ys for x in xs]
    nx=len(xs)
    faces=[(j*nx+i,j*nx+i+1,(j+1)*nx+i+1,(j+1)*nx+i)
           for j in range(len(ys)-1)for i in range(nx-1)]
    b.add(verts,faces,TILE,'East roof slope')
    # Roll tiles follow the visible eave slope. Their round noses project past the fascia.
    count=round(2*(HALF+.42)/(.36 if distant else .18))
    for x in np.linspace(-HALF-.42,HALF+.42,count):
        b.tube([(x,y,roof_height(x,y)+.034)for y in ys],.059 if distant else .047,
               RIDGE,5 if distant else 6,'Tile covers and eave ends')
    for y in (-1.02,-.82):
        b.tube([(x,y,roof_height(x,y)-.045)for x in xs],.075,POST,6,'Curved fascia')
    for y in np.arange(-.78,BACK,.64 if distant else .45):
        if not distant:
            b.tube([(x,y,roof_height(x,y)+.010)for x in xs],.014,
                   TILE,4,'Lap joints')
    for x in np.linspace(-HALF,HALF,45 if distant else 78):
        b.tube([(x,-1.00,roof_height(x,-1.0)-.12),(x,.33,roof_height(x,.33)-.14)],
               .050,SILL,5,'Underside rafters')
    # Plain timber soffit, lifted away from the roof to give the eave visible thickness.
    b.add([(x,y,z-.12)for x,y,z in verts],[tuple(reversed(f))for f in faces],POST,'Roof soffit')
    for x in [xs[0],xs[-1]]:
        v=[(x,y,roof_height(x,y)+off)for off in (-.12,0)for y in ys];n=len(ys)
        b.add(v,[(i,i+1,n+i+1,n+i)for i in range(n-1)],TILE,'Roof side edge')
    y=BACK
    b.add([(xs[0],y,.55),(xs[-1],y,.55),*[(x,y,roof_height(x,y))for x in reversed(xs)]],
          [tuple(range(len(xs)+2))],DARK,'Rear section')


def add_building(builder,distant):
    front=Facade(builder,(-HALF,0),(HALF,0),'East')
    for i,(left,right)in enumerate(zip(AXES,AXES[1:])):
        gallery_bay(front,left,right,i,distant)
    for i,x in enumerate(AXES):
        name='Column '+str(i+1)
        panel(front,x-.12,x+.12,LANDING,6.76,-.24,.108,POST,name)
        panel(front,x-.151,x+.151,LANDING,LANDING+.10,-.27,.134,BASE,name+' footing')
    panel(front,-HALF,HALF,0,LANDING,-BACK,.28,BASE,'Plinth and gallery floor')
    for j in range(4):
        depth=.28+(4-j)*.335
        panel(front,-2.70,2.70,0,(j+1)*LANDING/5,depth-.335,depth,BASE,'Four courtyard treads')
    panel(front,-HALF,HALF,3.44,3.53,-BACK,-.08,POST,'Gallery ceiling')
    for label,begin,end in [('North',(HALF,0),(HALF,BACK)),('South',(-HALF,BACK),(-HALF,0))]:
        side=Facade(builder,begin,end,label);W=side.length
        for j in range(2):
            a=-W/2+j*W/2;b=a+W/2
            inner_closure(side,a+.10,b-.10,-.84,distant,'Return '+str(j+1))
            panel(side,a,b,4.26,5.02,-.12,.013,SILL,'Return skirts')
            lattice(side,a+.1,b-.1,5.02,6.11,4,-.012,distant,'Return upper windows')
            panel(side,a,b,6.13,6.70,-.22,.025,POST,'Return lintels')
            floral_band(side,a+.10,b-.10,3.77,.082,distant,'Return')
            fret(side,a+.11,b-.11,3.51,.058,'Return',distant)
            if j:
                panel(side,a-.11,a+.11,LANDING,6.69,-.17,.08,POST,'Return column')
        # The corner study shows a lower open balustrade against the column line.
        panel(side,-W/2,W/2,.80,.89,-.11,.008,POST,'Return low rail')
        panel(side,-W/2,W/2,1.14,1.22,-.11,.008,POST,'Return handrail')
        for r in np.arange(-W/2+.16,W/2,.31 if distant else .23):
            panel(side,r-.033,r+.033,.89,1.14,-.06,-.028,PANEL,'Return balusters')
    eave_and_roof(builder,distant)
