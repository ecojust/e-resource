"""Original model of the main house. Metres, east-right when looking north from the garden."""
import math

import numpy as np
from shapely.geometry import Polygon, box
from photo_architecture import Facade, opening

WALL = 'warm ochre render'
LIME = 'pale edge stone'
TILE = 'burnt clay roofing'
RIDGE = 'raised tile barrel'
FRAME = 'dark wood frames'
GLASS = 'blue grey glazing'
IRON = 'balcony iron'
PALETTE = {
    WALL: {'color': [.63,.538,.385], 'roughness': .90},
    LIME: {'color': [.74,.652,.492], 'roughness': .86},
    TILE: {'color': [.375,.135,.081], 'roughness': .81},
    RIDGE: {'color': [.435,.167,.098], 'roughness': .83},
    FRAME: {'color': [.12,.082,.051], 'roughness': .65},
    GLASS: {'color': [.12,.195,.195], 'roughness': .29, 'metallic': .16},
    IRON: {'color': [.067,.069,.057], 'roughness': .56, 'metallic': .42},
    'entrance flags': {'color': [.43,.409,.336], 'roughness': .85},
    'shaded door wood': {'color': [.135,.075,.044], 'roughness': .67},
}


def pointed(x, bottom, width, height, rise, detail):
    """Two circular arcs meet at an apex, distinct from the adjacent round-headed lights."""
    r = width / 2
    offset = max(.001,(rise*rise-r*r)/(2*r))
    radius = r + offset
    theta = math.atan2(rise,offset)
    pts = [(x-r,bottom),(x+r,bottom)]
    for i in range(detail+1):
        a = theta*i/detail
        pts.append((x-offset+radius*math.cos(a),bottom+height-rise+radius*math.sin(a)))
    for i in range(detail-1,-1,-1):
        a = theta*i/detail
        pts.append((x+offset-radius*math.cos(a),bottom+height-rise+radius*math.sin(a)))
    return Polygon(pts)


def window(f, p, lod, stone=False):
    f.window(p,2,2 if lod else 3,frame=FRAME,glass=GLASS,trim=False)
    if stone:
        f.prism(p.buffer(.066,join_style='mitre').difference(p),-.022,.057,LIME,'arch moulding')


def front(b, lod):
    steps = 8 if lod else 20
    west = Facade(b,(-10.1,-5.83),(-4.35,-5.83),'West garden wing')
    apertures = []
    for u in (-1.98,-.05,1.89):
        apertures.extend([opening(u,.46,1.13,2.40,.59,steps),opening(u,4.15,1.19,1.61)])
    west.wall(.12,6.50,apertures,material=WALL)
    for q in apertures: window(west,q,lod)
    west.beam(6.47,.11,.31,LIME)
    west.beam(3.62,.07,.119,LIME)
    west.builder.box((-7.22,-5.20,6.54),(5.9,1.50,.15),LIME,label='West garden wing/terrace cornice')

    f = Facade(b,(-4.35,-7.10),(3.62,-7.10),'South garden loggia')
    main = [pointed(u,.135,1.55,2.92,1.34,steps) for u in (-2.47,0,2.47)]
    upper = [opening(u,3.91 if i in (0,3) else 3.56,1.40,1.91 if i in (0,3) else 2.26,.65,steps)
             for i,u in enumerate((-2.72,-.91,.91,2.72))]
    f.wall(.10,6.18,main+upper,thickness=.47,material=WALL)
    for w in upper: window(f,w,lod,True)
    f.beam(6.19,.15,.33,LIME)
    for x in (-4.35,3.62):
        segment = ((x,-7.10),(x,-5.12))
        if x<0: segment=segment[::-1]
        Facade(b,*segment,'South garden loggia/side cheek').wall(.1,6.18,material=WALL)
    back = Facade(b,(-4.35,-5.12),(3.62,-5.12),'Inside shaded loggia')
    openings = [opening(x,.14 if x==0 else .56,1.37,2.54 if x==0 else 1.95,.65,steps) for x in (-2.46,0,2.46)]
    back.wall(.10,3.49,openings,thickness=.19,material=WALL)
    for j,q in enumerate(openings):
        back.window(q,2,2,frame=FRAME,trim=False,glass='shaded door wood' if j==1 else GLASS)
    b.box((-.365,-6.12,3.45),(7.83,1.98,.19),WALL,label='South garden loggia/overhead slab')
    b.box((-.365,-6.12,.10),(7.9,2.03,.20),'entrance flags',label='South garden loggia/paving')
    f.box(0,3.59,3.78,.17,.57,.22,LIME,'projecting balcony floor')
    for u in np.linspace(-1.78,1.78,9 if lod else 19):
        f.line((u,3.68,.455),(u,4.28,.455),.024,IRON,5,'balcony pickets')
    for z in (3.80,4.28): f.line((-1.81,z,.455),(1.81,z,.455),.032,IRON,7,'balcony rail')
    for x in (-1.80,1.80):
        f.line((x,4.28,-.01),(x,4.28,.455),.033,IRON,7,'balcony returns')
        f.box(x*.85,3.42,.16,.36,.42,.12,LIME,'balcony corbels')
    for j in range(3):
        b.box((-.365,-7.17-.25*j,(.20-.047*j)/2),(3.65+.16*j,.32,.20-.047*j),'entrance flags',label='South garden loggia/steps')
    mid = Facade(b,(3.62,-5.53),(5.91,-5.53),'Garden return')
    lower=opening(0,.52,1.66,2.15,.48,steps); upper=[opening(x,4.15,.73,1.59) for x in (-.47,.47)]
    mid.wall(.1,6.59,[lower,*upper],material=WALL)
    for q in [lower,*upper]: window(mid,q,lod)


def turret(b,lod):
    """Faceted curved bay, with the arched ground-floor and rectangular upper lights in real openings."""
    cx,cy,r=7.78,-4.65,2.63
    angles=np.linspace(math.radians(-150),math.radians(5),9)
    arc=[(cx+r*math.cos(a),cy+r*math.sin(a)) for a in angles]
    start=(5.91,-5.53)
    Facade(b,start,arc[0],'East garden bay/west junction').wall(.1,6.65,material=WALL,thickness=.16)
    for j,(a,c) in enumerate(zip(arc,arc[1:])):
        f=Facade(b,a,c,'East rounded bay/section '+str(j+1))
        holes=[]
        if j in (1,4,7):
            holes=[pointed(0,.58,.77,2.02,.53,8 if lod else 14),opening(0,4.12,.78,1.62)]
        f.wall(.10,6.68,holes,thickness=.15,material=WALL)
        for q in holes:window(f,q,lod,True)
        f.beam(3.61,.075,.125,LIME)
        f.beam(6.64,.16,.28,LIME)
    edge=(*arc[-1],)
    Facade(b,edge,(10.22,-2.50),'East rounded bay/return').wall(.1,6.61,material=WALL)
    plan=Polygon([start,*arc,(10.22,-2.50),(5.91,-2.50)])
    b.plan_prism(plan,.0,.14,LIME,'East rounded bay/foundation')
    b.plan_prism(plan,6.65,6.94,WALL,'East rounded bay/raised drum')
    b.plan_prism(plan.buffer(.16),6.93,7.055,TILE,'East rounded bay/tiled cap')
    center=(7.95,-4.55,7.26)
    for p,q in zip(arc,arc[1:]):
        b.add([(*p,7.06),(*q,7.06),center],[(0,1,2)],TILE,'East rounded bay/shallow roof')


def roof(b, x0,x1,y0,y1,eaves,rise,axis,lod,name,gable=False,hip_distance=None):
    """A tiled roof with photographed broad slopes; tile rolls descend to each eave."""
    if axis=='y': u0,u1,v0,v1=y0,y1,x0,x1
    else:u0,u1,v0,v1=x0,x1,y0,y1
    def pt(u,v,z):return (u,v,z) if axis=='x' else (v,u,z)
    vm=(v0+v1)/2
    h=0 if gable else min((v1-v0)*.30,(u1-u0)*.21)
    if hip_distance is not None:
        h=min(hip_distance,(u1-u0)*.48)
    a=pt(u0,v0,eaves);c=pt(u1,v0,eaves);d=pt(u1,v1,eaves);e=pt(u0,v1,eaves)
    left,right=pt(u0+h,vm,eaves+rise),pt(u1-h,vm,eaves+rise)
    planes = [[a,c,right,left],[e,left,right,d]]
    if not gable:
        planes += [[a,left,e],[c,d,right]]
    for verts in planes:
        v=verts if axis=='x' else list(reversed(verts))
        b.add(v,[tuple(range(len(v)))],TILE,name+'/roof planes')
    for i in (0,1):
        slope=v0 if i==0 else v1
        for u in np.arange(u0+.12,u1-.05,.69 if lod else .245):
            ratio=min(1,(u-u0)/h,(u1-u)/h) if h else 1.
            b.tube([pt(u,slope,eaves+.018),pt(u,slope+(vm-slope)*ratio,eaves+rise*ratio+.018)],
                   .039 if lod else .052,RIDGE,5 if lod else 7,name+'/barrel tile rolls')
    b.tube([left,right],.102,RIDGE,8,name+'/ridge')
    if h:
        # End hips have their own runs of convex terracotta tiles. The south hip
        # is visible from the garden between the attic gable and the arcade.
        for v in np.arange(v0+.11,v1-.05,.64 if lod else .236):
            ratio=1-abs(v-vm)/((v1-v0)/2)
            for origin,direction in ((u0,1),(u1,-1)):
                b.tube([pt(origin,v,eaves+.024),pt(origin+direction*h*ratio,v,eaves+rise*ratio+.024)],
                       .038 if lod else .047,RIDGE,5 if lod else 7,name+'/end hip tile rolls')
        for a,c in ((a,left),(e,left),(d,right),(pt(u1,v0,eaves),right)):
            b.tube([a,c],.083,RIDGE,7,name+'/hip caps')


def rear(b,lod):
    f=Facade(b,(10.22,5.65),(-10.10,5.65),'Northern entrance elevation')
    n=8 if lod else 16
    left=[pointed(x,.72, .62,1.35,.42,n) for x in (-6.13,-5.26,-4.39)]
    upper=[pointed(x,3.93,.75,2.23,.59,n) for x in (-6.35,-5.28,-4.21,-.39,.66,1.71)]
    others=[opening(x,1.10,1.05,1.55,.32,n)for x in (4.58,6.12,7.65)]
    upper+= [opening(x,4.30,1.09,1.72,.30,n)for x in (5.05,6.68)]
    door=opening(.3,.11,1.80,2.83,.82,n)
    f.wall(.08,6.83,[*left,*upper,*others,door],material=WALL)
    for q in left+upper+others:window(f,q,lod)
    f.window(door,2,3,frame=FRAME,glass='shaded door wood',trim=False)
    f.prism(door.buffer(.18).difference(door),-.04,.12,LIME,'recessed entrance arch')
    f.beam(6.84,.16,.32,LIME)
    # North porte-cochère: open gable and clear side bays, no floor spanning the drive.
    ox=-.24; width=4.25; end=9.35
    portal=Facade(b,(ox+width/2,end),(ox-width/2,end),'North porte-cochere/outward gable')
    arch=opening(0,-.12,2.74,2.94,1.35,n)
    outline=Polygon([(-width/2,0),(width/2,0),(width/2,3.14),(1.68,3.17),(1.40,3.45),(.94,3.60),(.57,3.96),(0,4.09),(-.57,3.96),(-.94,3.60),(-1.40,3.45),(-1.68,3.17),(-width/2,3.14)])
    portal.wall(0,4.1,[arch],thickness=.35,material=WALL,outline=outline)
    portal.prism(arch.buffer(.09).difference(arch).intersection(outline),.00,.07,LIME,'stone arch ring')
    for sign in (-1,1):
        x=ox+sign*width/2
        for y in (5.93,end-.19):
            b.box((x,y,1.36),(.40,.43,2.72),WALL,label='North porte-cochere/driveway piers')
        b.box((x,(end+5.67)/2,2.93),(.42,end-5.63,.38),WALL,label='North porte-cochere/side lintels')
    roof(b,ox-width/2-.11,ox+width/2+.11,5.45,end+.03,3.06,.83,'y',lod,'North porte-cochere',True)


def dormer(b,x,y,z,w,depth,h,facesouth,lod):
    sign=1 if facesouth else -1
    near=y;back=y+sign*depth
    f=Facade(b,(x-sign*w/2,near),(x+sign*w/2,near),'Attic garden dormer' if facesouth else 'Attic north dormer')
    holes=[opening(u,z+.12,.63,h*.76)for u in np.linspace(-w*.30,w*.30,3 if facesouth else 2)]
    outline=Polygon([(-w/2,z),(w/2,z),(w/2,z+h),(0,z+h+w*.19),(-w/2,z+h)])
    f.wall(z,z+h,holes,material=WALL,thickness=.21,outline=outline)
    for q in holes:window(f,q,lod)
    # The far end remains visible across the ridge from the opposite drive.
    # Close the whole pentagonal dormer, including the triangle under its roof.
    back_face=Facade(b,(x+sign*w/2,back),(x-sign*w/2,back),f.label+'/back')
    back_face.wall(z-.40,z+h,material=WALL,thickness=.16,outline=Polygon([
        (-w/2,z-.40),(w/2,z-.40),(w/2,z+h),(0,z+h+w*.19),(-w/2,z+h)]))
    for edge in (-w/2,w/2):
        b.box((x+edge,(near+back)/2,z+(h-.40)/2),(.1,depth,h+.40),WALL,label=f.label+'/side cheeks')
    roof(b,x-w/2-.12,x+w/2+.12,min(near,back)-.1,max(near,back)+.1,z+h,w*.19,'y',lod,f.label,True)


def add_geometry(b,lod):
    front(b,lod);turret(b,lod);rear(b,lod)
    core=box(-10.10,-5.53,10.22,5.65)
    b.plan_prism(core,0,.13,'entrance flags','Main house/foundation')
    b.plan_prism(core,6.57,6.72,LIME,'Main house/upper ceiling')
    for x,side in ((-10.10,'west'),(10.22,'east')):
        a,c=((x,5.65),(x,-5.83)) if x<0 else ((x,-2.50),(x,5.65))
        f=Facade(b,a,c,side.title()+' return')
        xs=(-2.55,.0,2.55) if x<0 else (-1.9,1.4)
        holes=[opening(u,y,.95,h,.30 if y<3 else 0,10)for u in xs for y,h in ((.74,1.74),(4.05,1.62))]
        f.wall(.08,6.83,holes,material=WALL,thickness=.20)
        for q in holes:window(f,q,lod)
        f.beam(6.81,.14,.33,LIME)
    roof(b,-10.36,10.50,-5.84,5.90,6.85,2.32,'x',lod,'Main house')
    # Tiled projection above the four garden arches and central windowed attic gable.
    roof(b,-4.52,3.80,-7.29,-1.32,6.34,1.68,'y',lod,'South projecting pavilion',hip_distance=2.85)
    dormer(b,-.43,-5.87,7.13,3.82,2.42,1.13,True,lod)
    dormer(b,1.38,4.12,7.79,3.12,2.70,1.04,False,lod)
    dormer(b,4.65,-3.51,7.48,2.04,1.55,.69,True,lod)
    for x,y in [(6.88,1.42),(-5.85,2.92)]:
        b.box((x,y,8.62),(.56,.85,2.40),WALL,label='Roof/chimney shaft')
        b.box((x,y,9.82),(.68,.98,.16),LIME,label='Roof/chimney crowns')
        for dy in (-.18,.18):b.lathe((x,y+dy),[(9.84,.15),(10.12,.12)],TILE,9,'Roof/chimney pots')
