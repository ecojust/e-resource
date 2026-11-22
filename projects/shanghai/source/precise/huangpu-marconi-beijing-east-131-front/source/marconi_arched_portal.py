"""Model the dated Beijing East Road portal from two registered street photographs.

The arch profiles were marked on the rectified 2017 front. Each profile is
returned to its own working depth along those same pinhole rays. The recess
is built with changing sections, including the back wall of the brick lunette.
"""
import json
import math
from pathlib import Path

import numpy as np
from scipy.interpolate import PchipInterpolator
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

from marconi_photo_plane import CALIBRATION, on_wall, pixel

TRACE = json.loads((Path(__file__).resolve().parents[1] / 'measurements/portal-photo-traces.json').read_text())
BOARD = TRACE['arch_board']
PITCH = (BOARD['x_m'][1] - BOARD['x_m'][0]) / BOARD['width_px']

def finish(rgb, roughness=.85, metallic=0.):
    s = np.asarray(rgb) / 255.
    v = np.where(s <= .04045, s / 12.92, ((s + .055) / 1.055)**2.4)
    return dict(color=v.tolist(), roughness=roughness, metallic=metallic)

BRICK = ['131 arch | red stretcher ' + str(i + 1) for i in range(5)]
MORTAR = '131 arch | terracotta mortar'
MOULD = '131 arch | moulded terracotta'
LIP = '131 arch | worn brick arris'
STONE = '131 portal | grey pedestal'
STEP = '131 portal | threshold stone'
TIMBER = '131 portal | brown wood'
BEAD = '131 portal | dark timber rebate'
GLASS = '131 portal | overlight glass'
GREEN = '131 portal | painted green grille'
DARK = '131 portal | recess shade'
ENAMEL = '131 portal | street-number enamel'
WHITE = '131 portal | cream lettering'
SOFFIT = '131 arch | shaded underside mortar'
SOFFIT_BRICK = ['131 arch | sheltered soffit ' + str(i+1) for i in range(4)]
LUNETTE = ['131 arch | sheltered lunette ' + str(i+1) for i in range(5)]
LUNETTE_JOINT = '131 arch | pale lunette joints'
FRAME = '131 portal | display frame'
PAPER = '131 portal | display surface'
PALETTE = {MORTAR:finish([170,129,122]), MOULD:finish([120,79,74]), LIP:finish([137,92,84]),
           STONE:finish([100,106,113]), STEP:finish([99,93,86]), TIMBER:finish([69,57,51]),
           BEAD:finish([53,43,38]), GLASS:finish([36,44,48],.40,.13),
           GREEN:finish([53,83,72],.54,.25), DARK:finish([11,13,12],.94),
           ENAMEL:finish([42,96,69],.45,.21), WHITE:finish([220,219,193],.61),
           FRAME:finish([179,177,165],.65,.15), PAPER:finish([99,107,126],.76)}
for mat, rgb in zip(BRICK, [[134,87,83],[139,90,85],[137,88,83],[132,85,82],[142,92,87]]):
    PALETTE[mat] = finish(rgb)

for mat,rgb in zip(SOFFIT_BRICK,[[49,33,31],[44,30,29],[56,38,35],[59,40,37]]):
    PALETTE[mat]=finish(rgb)
for mat,rgb in zip(LUNETTE,[[73,49,44],[70,47,44],[77,52,48],[69,46,42],[75,50,45]]):
    PALETTE[mat]=finish(rgb)
PALETTE[SOFFIT]=finish([76,53,49])
PALETTE[LUNETTE_JOINT]=finish([103,80,72])

def portal_wall_cut():
    return Polygon([(-1.48,-.016),(1.47,-.016),(1.47,4.34),(1.87,4.34),
                    (1.87,6.24),(-1.86,6.24),(-1.86,4.34),(-1.48,4.34)])

def prism(b, shape, front, back, mat, name):
    b.prism(shape, -back, -front, lambda x,z,d:(x,-d,z), mat, '131 | ' + name)

def panel(b, left, right, low, high, front, rear, mat, name):
    if right > left and high > low:
        b.box(((left+right)/2,(front+rear)/2,(low+high)/2),(right-left,rear-front,high-low),
              mat,label='131 | '+name)

def xz_at(mark, depth):
    u,v = mark
    x,z = BOARD['x_m'][0] + PITCH*u, BOARD['z_top_m'] - PITCH*v
    if depth == 0:
        return np.array([x,z])
    uv = pixel([x,0.,z])
    a,_,c = on_wall(*uv,depth)
    return np.array([a,c])

def marks_at(marks, depth):
    return np.array([xz_at(mark,depth) for mark in marks])

def profile(name, n, depth):
    marks = np.asarray(TRACE[name])
    # Uniform arc-length stations keep the shoulder bricks aligned across courses.
    arc = np.r_[0., np.cumsum(np.linalg.norm(np.diff(marks,axis=0),axis=1))]
    marks = PchipInterpolator(arc/arc[-1], marks, axis=0)(np.linspace(0.,1.,n))
    return marks_at(marks, depth)

def ring(a, c):
    return Polygon(np.vstack([a,c[::-1]]))

def under(row, bottom=-.024):
    return Polygon([*row,(row[-1,0],bottom),(row[0,0],bottom)])

def masonry(b, shape, depth, back, name, lod, pitch=.081, length=.244, bricks=BRICK, mortar=MORTAR):
    """Only the masked face is coursed. All brick edges end at a real opening."""
    prism(b,shape,depth+.006,back,mortar,name+' bedding')
    x0,z0,x1,z1 = shape.bounds
    joint = .009 if lod else .007
    for j in range(math.floor(z0/pitch), math.ceil(z1/pitch)):
        z = j*pitch
        phase = (j%2)*length*.5
        for i in range(math.floor((x0-phase)/length), math.ceil((x1-phase)/length)):
            x = phase+i*length
            tile = shape.intersection(box(x+joint/2,z+joint/2,x+length-joint/2,z+pitch-joint/2))
            if tile.area > .00005:
                prism(b,tile,depth,depth+.0064,bricks[(i+3*j)%len(bricks)],f'{name} course {j}/{i}')

def rolled_tunnel(b, a, c, ya, yc, thickness, mat, name):
    """A closed curved arch lining bounded by a front and recessed profile."""
    assert len(a)==len(c)
    for i in range(len(a)-1):
        v=[]
        for dz in (0.,thickness):
            for point,y in ((a[i],ya),(a[i+1],ya),(c[i+1],yc),(c[i],yc)):
                v.append((point[0],y,point[1]+dz))
        faces=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
        b.add(v,faces,mat,label=f'131 | {name} {i+1}')

def soffit_courses(b,a,c,ya,yc,lod,name):
    rolled_tunnel(b,a,c,ya,yc,.075,SOFFIT,name+' joints')
    # The short radial joints on the dark underside turn with the arch.
    for row in range(2 if not lod else 1):
        rows=2 if not lod else 1
        t0=(row+.023)/rows
        t1=(row+.977)/rows
        for i in range(len(a)-1):
            fr=a[i:i+2]*(1-t0)+c[i:i+2]*t0
            bk=a[i:i+2]*(1-t1)+c[i:i+2]*t1
            fr=fr*.967+fr[::-1]*.033-[0.,.008]
            bk=bk*.967+bk[::-1]*.033-[0.,.008]
            rolled_tunnel(b,fr,bk,ya*(1-t0)+yc*t0,ya*(1-t1)+yc*t1,.009,
                          SOFFIT_BRICK[(i+row)%len(SOFFIT_BRICK)],f'{name} radial {row+1}.{i+1}')

def brick_arch(b, lod):
    n = 33 if lod else 53
    outer = profile('outer_roll',n,.012)
    inner = profile('inner_arch',n,.012)
    mid = profile('inner_middle',n,.319)
    rear = profile('inner_back',n,.751)
    # The two curved springing offsets are visible even below the third wedge.
    join = np.vstack([xz_at((134,398),.012),xz_at((136,384),.012),
                      xz_at((155,361),.012),inner,xz_at((647,358),.012),
                      xz_at((669,382),.012),xz_at((671,398),.012)])
    field = portal_wall_cut().intersection(box(-2.,4.34,2.,6.24))
    wall = field.difference(under(join))
    band = ring(outer,inner)
    reds = wall.difference(band)
    masonry(b,reds,.028,.323,'flat spandrel',lod)
    prism(b,band,.014,.327,MORTAR,'radial brick arch bedding')
    # Radiating joints continue through the two shoulders. Three wedges break the course.
    for i in range(n-1):
        o0,o1 = outer[i:i+2];a0,a1 = inner[i:i+2]
        gutter = .053
        a = np.array([o0*(1-gutter)+o1*gutter,o1*(1-gutter)+o0*gutter])
        c = np.array([a0*(1-gutter)+a1*gutter,a1*(1-gutter)+a0*gutter])
        prism(b,ring(a,c),.001,.017,BRICK[i%5],f'radiating brick {i+1}')
    for j,(lo,hi,d) in enumerate(((.008,.047,-.007),(.073,.097,-.003),(.147,.175,-.011))):
        a = outer*(1-lo)+inner*lo
        c = outer*(1-hi)+inner*hi
        prism(b,ring(a,c),d,.016,MOULD,f'outer archivolt moulding {j+1}')
    midlip = mid + [0.,.049]
    backlip = rear + [0.,.033]
    soffit_courses(b,inner,mid,.012,.319,lod,'outer brick soffit')
    soffit_courses(b,mid,rear,.319,.751,lod,'deep inner soffit')
    prism(b,ring(midlip,mid),.300,.326,SOFFIT_BRICK[2],'middle curved arris')
    prism(b,ring(backlip,rear),.730,.763,SOFFIT_BRICK[2],'rear curved arris')
    # Horizontal stretcher courses remain visible above the timber head.
    shell = under(rear).intersection(box(-1.26,4.555,1.24,6.07))
    masonry(b,shell,.767,.833,'recessed brick lunette',lod,.073,.222,LUNETTE,LUNETTE_JOINT)
    backing = field.difference(box(-1.086,0.,1.086,4.564))
    prism(b,backing,.844,.938,LUNETTE[0],'rear ring and shoulder backing')
    # Behind the projecting arch ears both springings stand on a stepped
    # brick respond. The 2015 oblique shows its continuous return to the wood.
    for j,(a,c) in enumerate(((-1.462,-1.087),(1.086,1.464))):
        masonry(b,box(a,4.344,c,4.608),.379,.844,f'springing return {j+1}',lod)
    
    for j,outline in enumerate(TRACE['wedges_outline']):
        q = marks_at(outline,-.019)
        prism(b,Polygon(q),-.015,.054,MOULD,f'projecting wedge {j+1}')
        upper,lower = q[:2],q[[3,2]]
        for k,(low,high,d) in enumerate(((.016,.067,-.049),(.088,.118,-.042),(.14,.176,-.036))):
            a = upper*(1-low)+lower*low
            c = upper*(1-high)+lower*high
            prism(b,ring(a,c),d,-.012,LIP,f'wedge {j+1} stepped head {k+1}')
        for k in range(4):
            a,c=(k+.035)/4,(k+.96)/4
            r=np.array([upper[0]*(1-a)+upper[1]*a, upper[0]*(1-c)+upper[1]*c,
                        lower[0]*(1-c)+lower[1]*c, lower[0]*(1-a)+lower[1]*a])
            r[:2]=r[:2]*.817+r[[3,2]]*.183
            prism(b,Polygon(r),-.023,-.014,BRICK[(k+j)%5],f'wedge {j+1} brick flute {k+1}')
    return rear

def fluted_course(b, x, y, low, high, r0, r1, lod, name, material):
    """Extrude a circle with twelve shallow flutes; a solid through every flute."""
    n = 48 if lod else 96
    rings=[]
    for z,r in ((low,r0),(high,r1)):
        level=[]
        for i in range(n):
            phase=2*math.pi*i/n
            radius=r-.017*(.5+.5*math.cos(12*phase))**1.7
            level.append((x+radius*math.cos(phase),y+radius*math.sin(phase),z))
        rings.extend(level)
    # Triangulate each concave-but-star-shaped end around its own axis.
    rings.extend([(x,y,low),(x,y,high)])
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend([(2*n,j,i),(2*n+1,n+i,n+j),(i,j,n+j,n+i)])
    b.add(rings,faces,material,label='131 | '+name)

def leaf(b, x, base, width, height, front, name):
    shape=Polygon([(x,base),(x-width*.48,base+height*.41),(x-width*.47,base+height*.65),
                   (x-width*.29,base+height*.59),(x-width*.22,base+height*.86),
                   (x,base+height),(x+width*.18,base+height*.81),
                   (x+width*.34,base+height*.63),(x+width*.49,base+height*.63),
                   (x+width*.42,base+height*.35)])
    prism(b,shape,front,front+.039,MOULD,name+' relief')

def engaged_pier(b,x,lod,side):
    side_min,side_max=(-1.48,-.986) if x<0 else (.987,1.47)
    panel(b,side_min,side_max,0.,.77,.254,.881,STONE,side+' grey pedestal')
    masonry(b,box(side_min,.77,side_max,4.57),.535,.884,side+' backing pier',lod,.082,.245)
    # The stepped street wall returns to the recessed column. It closes
    # the narrow strip exposed between the wall face and the pier in oblique view.
    edge=side_min if x<0 else side_max
    toward=1. if x<0 else -1.
    cheek=Polygon([(edge,-.002),(edge+.024*toward,-.002),
                   (edge+.074*toward,.876),(edge,.876)])
    b.plan_prism(cheek,0.,.773,STONE,'131 | '+side+' grey lower return')
    b.plan_prism(cheek,.773,4.349,BRICK[3],'131 | '+side+' vertical brick return')
    # The wall narrows back to the brown wood at the rectangular overlight.
    masonry(b,box(x-.168,3.53,x+.168,4.675),.323,.539,side+' upper brick respond',lod)
    fit=json.loads((Path(__file__).resolve().parents[1]/'measurements/portal-shaft-stereo.json').read_text())
    x=fit['axis_xy_m'][0] if x<0 else fit['western_x_m']
    axis_y=fit['axis_xy_m'][1]
    shaft_radius=fit['radius_at_z_230_m']
    taper=fit['radius_gradient_per_m']

    panel(b,x-.205,x+.205,.16,.772,.255,.59,STONE,side+' square stone foot')
    masonry(b,box(x-.176,.774,x+.176,1.408),.319,.566,side+' brick plinth',lod,.076,.239)
    seg=24 if lod else 48
    b.lathe((x,axis_y),[(1.368,.187),(1.395,.197),(1.426,.198),(1.440,.175),
                         (1.467,.198),(1.498,.197),(1.511,.173),(1.547,.160)],
            MOULD,seg,'131 | '+side+' lower rings')
    count=19
    for i in range(count):
        a,z=1.542+i*(1.575/count),1.542+(i+1)*(1.575/count)
        r0=shaft_radius+(a-2.30)*taper;r1=shaft_radius+(z-2.30)*taper
        fluted_course(b,x,axis_y,a,z-.0034,r0,r1,lod,f'{side} fluted brick course {i+1}',BRICK[(i+int(x>0))%5])
        fluted_course(b,x,axis_y,z-.0034,z,r1-.002,r1-.002,lod,f'{side} shaft joint {i+1}',MORTAR)
    b.lathe((x,axis_y),[(3.117,.140),(3.132,.164),(3.146,.179),(3.167,.182),
                         (3.178,.169),(3.185,.158),(3.213,.172),(3.238,.177),
                         (3.315,.197),(3.369,.206),(3.401,.217)],
            MOULD,seg,'131 | '+side+' neck and capital bell')
    panel(b,x-.088,x+.088,1.543,3.130,axis_y+.057,.541,MOULD,side+' bonded shaft return')
    # The two rounded volutes flank the central leaf below a stepped square cap.
    for k,sign in enumerate((-1,1)):
        ox=x+sign*.116
        theta=np.linspace(0.,2.18*math.pi,14 if lod else 30)
        radius=.059*np.exp(-.265*theta)
        curve=[(ox+sign*r*math.cos(t),.202,3.346+r*math.sin(t)) for t,r in zip(theta,radius)]
        b.tube(curve,.011,MOULD,6 if lod else 9,'131 | '+side+f' volute {k+1}')
        leaf(b,x+sign*.062,3.192,.072,.140,.204,side+f' side leaf {k+1}')
    leaf(b,x,3.190,.104,.164,.186,side+' central capital leaf')
    for i,(z,h,wide,dep) in enumerate(((3.391,.032,.405,.493),(3.423,.029,.421,.50),
                                       (3.452,.034,.434,.514),(3.486,.071,.453,.532))):
        panel(b,x-wide/2,x+wide/2,z,z+h,axis_y-dep/2,axis_y+dep/2,MOULD,side+f' cap course {i+1}')

def overlight(b):
    holes=[(-.877,-.158,3.593,4.419),(.129,.828,3.593,4.419)]
    opening=unary_union([box(l,bottom,r,top) for l,r,bottom,top in holes])
    frame=box(-1.086,3.326,1.086,4.567).difference(opening)
    prism(b,frame,.749,.874,TIMBER,'two-light timber transom')
    for i,(l,r,z0,z1) in enumerate(holes):
        well=box(l,z0,r,z1)
        clear=box(l+.025,z0+.029,r-.025,z1-.029)
        prism(b,well.difference(clear),.766,.866,BEAD,f'overlight {i+1} bead')
        prism(b,clear,.802,.835,GLASS,f'overlight {i+1} glass')

def door_panel(b):
    """Two painted grille fields, their short fret returns, transom bars and lower vent strip."""
    x0,x1,z0,z1=-.986,.957,.384,3.334
    panel(b,x0,x1,z0,z1,.985,1.018,DARK,'shaded field behind grille')
    def bar(l,r,lo,hi,name,d=.813):
        panel(b,l,r,lo,hi,d,d+.038,GREEN,name)
    for i,x in enumerate((x0+.018,-.519,.930)):
        bar(x-.018,x+.018,z0,z1,f'grille outer upright {i+1}')
    for j,z in enumerate((z0+.024,1.493,1.552,1.998,3.059,3.126,z1-.017)):
        bar(x0+.036,x1-.022,z-.016,z+.016,f'grille rail {j+1}')
    for x in (-.050,.012):
        bar(x-.011,x+.011,3.13,z1-.029,'short transom upright')
    for lo,hi in ((x0+.035,-.052),(.026,x1-.026)):
        bar(lo,hi,3.21,3.232,'transom horizontal')
    lines=json.loads((Path(__file__).resolve().parents[1]/'measurements/grille-scan-lines.json').read_text())
    for i,strip in enumerate(lines['bars']):
        x,w=strip['x_m'],strip['width_m']
        for name,lo,hi in [('lower',z0+.040,1.487),('upper',2.012,3.047)]:
            bar(x-w/2,x+w/2,lo,hi,f'{name} measured upright {i+1}')
    for i,bridge in enumerate(lines['returns']):
        a,c=(lines['bars'][bridge[k]] for k in ('left','right'))
        l,r=a['x_m']+a['width_m']/2,c['x_m']-c['width_m']/2
        z=bridge['z_m']
        bar(l,r,z-.012,z+.012,f'lower fret bridge {i+1}')
        offset=2.011-z0 if bridge['kind']=='bottom' else 3.046-1.487
        bar(l,r,z+offset-.012,z+offset+.012,f'upper fret bridge {i+1}')
    for i,z in enumerate(np.linspace(1.589,1.959,7)):
        bar(-.072,x1-.026,z,z+.025,f'continuous slat {i+1}')
    panel(b,x0+.043,-.076,1.57,1.99,.800,.835,GREEN,'solid middle panel behind left field')
    # The two dated street views show replaceable framed displays. Their images
    # are omitted because they are separate works with unidentified authors.
    panel(b,-.239,.526,2.008,2.741,.782,.804,FRAME,'upper poster frame')
    panel(b,-.218,.505,2.033,2.719,.779,.782,PAPER,'upper blank display inset')
    panel(b,-.958,-.696,1.554,1.994,.782,.804,FRAME,'lower notice frame')
    panel(b,-.944,-.710,1.571,1.976,.779,.782,PAPER,'lower blank notice inset')
    data=json.loads((Path(__file__).resolve().parents[1]/'measurements/portal-enamel-traces.json').read_text())
    from shapely.geometry import shape
    # Source outlines share this board's rectification at y=.79.
    panel(b,67/245-1.26,145/245-1.26,4.79-410/245,4.79-354/245,.790,.817,ENAMEL,'green street-number plate')
    for i,row in enumerate(data['outlines']):
        prism(b,shape(row['outline']),.787,.790,WHITE,f"enamel {row['field']} {i+1}")

def add_portal(b,lod=False):
    b.palette.update(PALETTE)
    brick_arch(b,lod)
    for x,side in ((-1.296,'east'),(1.263,'west')):
        engaged_pier(b,x,lod,side)
    for side,(left,right) in enumerate(((-1.086,-.986),(.957,1.086))):
        panel(b,left,right,.348,3.333,.753,.91,TIMBER,f'full-height wood jamb {side+1}')
    overlight(b)
    start=len(b.parts)
    door_panel(b)
    fit=json.loads((Path(__file__).resolve().parents[1]/'measurements/grille-stereo-depth.json').read_text())
    cam=np.array(CALIBRATION['camera_matrices']['2017_front'])
    eye=-np.linalg.solve(cam[:,:3],cam[:,3])
    scale=(fit['facade_depth_m']-eye[1])/(.790-eye[1])
    for part in b.parts[start:]:
        part['vertices']=(eye+(np.asarray(part['vertices'])-eye)*scale).tolist()
    # Two readily visible stone risers. The narrow third level carries the grille.
    for i,(y,z0,z1) in enumerate(((-.045,0.,.154),(.250,.154,.305),(.534,.305,.383))):
        panel(b,-1.071,1.039,z0,z1,y,1.014,STEP,f'threshold {i+1}')
