"""Parametric exterior of Shanghai's Majestic Theatre, based on the 2017 entrance and street views."""
from math import cos, sin, radians, ceil
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box, Point
from shapely.ops import unary_union
from photo_architecture import Facade
from sign_lettering import lettering_shapes

PALETTE = {
    'cream aggregate': {'color':[.69,.61,.44],'roughness':.83},
    'warm limestone trim': {'color':[.79,.71,.54],'roughness':.72},
    'incised sand ornament': {'color':[.53,.45,.31],'roughness':.75},
    'marquee charcoal': {'color':[.053,.043,.048],'roughness':.46,'metallic':.22},
    'marquee opal glass': {'color':[.84,.80,.61],'roughness':.32},
    'garnet enamel letters': {'color':[.48,.012,.025],'roughness':.34,'metallic':.25},
    'copper lattice': {'color':[.19,.115,.060],'roughness':.52,'metallic':.5},
    'amber leaded glass': {'color':[.32,.25,.16],'roughness':.25,'metallic':.20},
    'blue grey glass': {'color':[.092,.13,.15],'roughness':.25,'metallic':.21},
    'entry mahogany': {'color':[.21,.096,.050],'roughness':.55},
    'dark granite plinth': {'color':[.060,.056,.049],'roughness':.52},
    'mineral roof': {'color':[.43,.44,.41],'roughness':.85},
    'roof seam zinc': {'color':[.40,.42,.39],'roughness':.65,'metallic':.22},
}
# The camera sees the corner between Jiangning Road and Fengxian Road from the south.
# Curtain-wall endpoints fit the measured map shell. Drum radius is estimated from roof and door scale.
NORTH_END = (21.06,36.35)
# Follow the actual digitized joint with W1203409767. Recess 0.32 m on the theatre side.
PARTY_JOINT = (31.76,21.55)
EAST_END = (43.49,6.76)
FENG_START = (-11.32,-30.29)
JIANG_END = (-30.86,-26.38)
WEST_END = (-42.95,-6.32)
CENTER = np.array([-21.40,-27.70])
RADIUS = 5.65
ARC = 76
# Camera-right vector and outward bisector respectively, in ENU.
RIGHT = np.array([cos(radians(8)),-sin(radians(8))])
OUT = np.array([RIGHT[1],-RIGHT[0]])
FONT = Path(__file__).with_name('fonts')/'MajesticSignSubset.otf'


def axis(angle):
    a = radians(angle)
    return RIGHT*cos(a)-OUT*sin(a), OUT*cos(a)+RIGHT*sin(a)


def xy(angle,r=RADIUS):
    return tuple(CENTER+axis(angle)[1]*r)


def arc(a,b,r,lod=False):
    count = max(1,ceil(abs(b-a)/(5 if lod else 2.5)))
    return [xy(angle,r) for angle in np.linspace(a,b,count+1)]


def ring(builder,a,b,inner,outer,bottom,top,material,label,lod):
    poly = Polygon(arc(a,b,outer,lod)+arc(b,a,inner,lod))
    builder.plan_prism(poly,bottom,top,material,label)


def tangent(builder,angle,r,span,label):
    center=np.array(xy(angle,r))
    t=axis(angle)[0]*span/2
    return Facade(builder,center-t,center+t,label)


def glyphs(builder,text,r,center_angle,arc_width,z,height,depth,mat,prefix,lod):
    """Individually orient the editable glyphs around the curve; spacing follows the sign arc."""
    width = r*radians(arc_width)
    for index,(char,shape) in enumerate(lettering_shapes(text,width,height,font=FONT)):
        x0,_,x1,_ = shape.bounds
        mid = (x0+x1)/2
        panel=tangent(builder,center_angle+mid/width*arc_width,r,max(.15,x1-x0),prefix)
        outline=affinity.translate(shape,xoff=-mid,yoff=z)
        if prefix=='Chinese sign':
            # These are individually spaced, nearly square characters. Arc width sets their
            # position on the drum, independently from a character's physical width.
            outline=affinity.scale(outline,xfact=min(1.,1.06/(x1-x0)),yfact=1.,origin=(0,z))
        outline=outline.simplify(.014 if lod else .003,preserve_topology=True)
        panel.prism(outline,0,depth,mat,f'{index+1} {char}')


def glass_grid(facade,width,low,high,recess,glass,frame,rows,cols,label):
    half=width/2
    facade.prism(box(-half-.014,low-.014,half+.014,high+.014),recess-.09,recess,glass,label+' glazing')
    border=.064
    surface=box(-half,low,half,high)
    panes=[]
    for i in range(cols):
        for j in range(rows):
            x0=-half+i*width/cols; z0=low+j*(high-low)/rows
            panes.append(box(x0+border/2,z0+border/2,x0+width/cols-border/2,z0+(high-low)/rows-border/2))
    facade.prism(surface.difference(unary_union(panes)),recess+.015,recess+.080,frame,label+' framing')


def lobby(builder,lod):
    plaster='cream aggregate'; limestone='warm limestone trim'; dark='marquee charcoal'
    # Solid piers alternate with five tall, real glazed openings. Both end openings return onto the sides.
    opening_centers=[-60,-30,0,30,60]
    half=5.7
    stop=-ARC
    for i,a in enumerate(opening_centers):
        ring(builder,stop,a-half,RADIUS-.54,RADIUS,4.42,14.12,plaster,f'Lobby/pier {i+1}',lod)
        chord=2*RADIUS*sin(radians(half))
        g=tangent(builder,a,RADIUS*cos(radians(half)),chord,f'Lobby/window {i+1}')
        glass_grid(g,chord,4.40,14.15,-.20,'amber leaded glass','copper lattice',8 if lod else 16,2 if lod else 4,'stained glass')
        for z in (6.05,8.53,11.01,13.49):
            d=chord*.36
            # Four-point outline repeated in each bay, inferred from the 2017 illuminated view.
            points=[g.point(0,z-.43,-.105),g.point(d,z,-.105),g.point(0,z+.43,-.105),
                    g.point(-d,z,-.105),g.point(0,z-.43,-.105)]
            builder.tube(points,.025 if lod else .033,'copper lattice',4 if lod else 8,g.label+'/lead diamonds')
        stop=a+half
    ring(builder,stop,ARC,RADIUS-.54,RADIUS,4.42,14.12,plaster,'Lobby/pier 6',lod)
    # Three recessed entrances sit between four rounded piers, beneath a deep curved marquee.
    ring(builder,-ARC,ARC,RADIUS-1.48,RADIUS+.09,0,.11,'dark granite plinth','Lobby/entry threshold',lod)
    stops=[-46,0,46]
    last=-ARC
    for i,a in enumerate(stops):
        halfdoor=9.2
        ring(builder,last,a-halfdoor,RADIUS-1.31,RADIUS-.57,.11,3.40,plaster,f'Entry/recess wall {i+1}',lod)
        width=2*(RADIUS-.60)*sin(radians(halfdoor))
        d=tangent(builder,a,(RADIUS-.60)*cos(radians(halfdoor)),width,f'Entry/portal {i+1}')
        glass_grid(d,width,.11,3.40,-.18,'blue grey glass','entry mahogany',3,2,'doors')
        d.box(0,2.71,width,.12,.10,-.085,'entry mahogany','transom')
        if not lod:
            for x in (-.12,.12):d.box(x,1.11,.044,.42,.065,-.014,'aged brass','pulls')
        last=a+halfdoor
    ring(builder,last,ARC,RADIUS-1.31,RADIUS-.57,.11,3.40,plaster,'Entry/recess wall 4',lod)
    for i,a in enumerate([-65,-23,23,65]):
        builder.lathe(xy(a,RADIUS-.12),[(.08,.31),(.30,.31),(.31,.28),(3.98,.28)],plaster,16 if lod else 32,f'Entry/round pier {i+1}')
        builder.lathe(xy(a,RADIUS-.12),[(.09,.325),(.32,.325)],'dark granite plinth',16 if lod else 32,f'Entry/pier plinth {i+1}')
    for z0,z1,inner,outer,mat,label in [
            (3.38,3.83,RADIUS-1.40,RADIUS+.20,plaster,'entry soffit'),
            (3.83,4.65,RADIUS-.70,RADIUS+1.14,dark,'marquee fascia'),
            (3.82,3.92,RADIUS-.68,RADIUS+1.19,dark,'marquee lower lip'),
            (4.57,4.68,RADIUS-.65,RADIUS+1.18,dark,'marquee upper lip'),
            (3.97,4.50,RADIUS+1.145,RADIUS+1.170,'marquee opal glass','marquee lightbox'),
            (14.09,14.25,RADIUS-.56,RADIUS+.10,limestone,'window lintel'),
            (14.25,15.21,RADIUS-.56,RADIUS+.05,limestone,'floral frieze'),
            (15.20,15.30,RADIUS-.57,RADIUS+.13,limestone,'crown lip')]:
        angle=71 if label=='marquee lightbox' else ARC
        ring(builder,-angle,angle,inner,outer,z0,z1,mat,'Lobby/'+label,lod)
    # Close the rear of the rotunda where it rises through the low roof.
    ring(builder,ARC,360-ARC,RADIUS-.54,RADIUS,11.28,15.30,plaster,'Crown/rear drum wall',lod)
    # The circular crown rises visibly above both street walls.
    center=Point(CENTER)
    builder.plan_prism(center.buffer(RADIUS-.12,quad_segs=16 if lod else 42),15.28,16.79,plaster,'Crown/cylindrical attic')
    builder.plan_prism(center.buffer(RADIUS-.05,quad_segs=16 if lod else 42),16.77,16.90,limestone,'Crown/coping')
    builder.plan_prism(center.buffer(RADIUS-.25,quad_segs=16 if lod else 42),16.90,16.95,'mineral roof','Crown/roof cover')
    if not lod:
        for a in np.linspace(-71,71,22):
            f=tangent(builder,a,RADIUS+.08,.58,'Lobby/frieze')
            for x in (-.14,.14):
                pts=[f.point(x-.13,14.66,.010),f.point(x,14.81,.010),f.point(x+.13,14.66,.010),f.point(x,14.52,.010),f.point(x-.13,14.66,.010)]
                builder.tube(pts,.023,'incised sand ornament',5,'Lobby/frieze stylised petals')
    glyphs(builder,'MAJESTIC',RADIUS-.38,0,145,17.94,1.56,.12,'garnet enamel letters','Crown letters',lod)
    glyphs(builder,'美琪大戏院',RADIUS+.15,0,137,5.27,1.16,.085,'garnet enamel letters','Chinese sign',lod)
    glyphs(builder,'M A J E S T I C  T H E A T R E',RADIUS+1.20,0,105,4.235,.28,.035,dark,'Marquee letters',lod)
    for i,a in enumerate(np.linspace(-65,65,8)):
        g=tangent(builder,a,RADIUS-.45,.15,'Crown')
        g.box(0,17.11,.065,.48,.085,0,'copper lattice',f'sign stanchion {i+1}')


def long_wall(builder,a,b,label,side,lod):
    fac=Facade(builder,a,b,label); half=fac.length/2
    heights={'west':11.50,'south':11.65,'blind':11.65}
    h=heights[side]; holes=[]; panels=[]
    if side=='west':
        for i in range(7):
            panels.append((-half+4.2+i*1.73,5.72,1.14,2.31,'gallery',1,4))
        panels.extend([(-half+6.5,.58,4.82,2.82,'poster',2,1),
                       (-half+12.0,.58,4.82,2.82,'poster',2,1)])
    if side=='south':
        for i in range(3):
            panels.append((-half+2.35+i*2.11,.52,1.94,3.10,'poster',1,1))
        # Two groups of upper and lower service-side windows visible to the right of the corner.
        for i in range(9):
            panels.append((-half+16.3+i*2.45,5.65,1.04,1.75,'upper',2,2))
        for i in range(8):
            panels.append((-half+16.3+i*2.44,.89,.89,1.61,'lower',2,2))
        panels.append((-half+38.5,.10,3.12,3.27,'service doors',3,2))
    for i,(u,z,w,v,kind,c,r) in enumerate(panels):
        p=box(u-w/2,z,u+w/2,z+v);holes.append(p)
        d=Facade(builder,fac.point(u-w/2,0)[:2],fac.point(u+w/2,0)[:2],label+f'/{kind} {i+1}')
        glass_grid(d,w,z,z+v,-.22,'blue grey glass','marquee charcoal',max(1,r-1) if lod else r,c,'opening')
    fac.wall(0,h,holes,.39,'cream aggregate')
    if side!='blind':
        fac.prism(box(-half,0,half,.38).difference(unary_union(holes)),-.08,.035,'dark granite plinth','base')
        for z,p in [(h-.17,.12),(h-.44,.065)]:
            fac.box(0,z,fac.length,.13,.22,p-.11,'warm limestone trim','upper bands')
        if side=='west':
            fac.box(-half+9.39,5.57,12.4,.15,.29,.04,'warm limestone trim','gallery sill')
            fac.box(-half+9.39,8.11,12.4,.16,.25,.04,'warm limestone trim','gallery lintel')


def add_theatre(builder,lod):
    lobby(builder,lod)
    left=xy(-ARC); right=xy(ARC)
    long_wall(builder,WEST_END,JIANG_END,'Jiangning Road','west',lod)
    long_wall(builder,FENG_START,EAST_END,'Fengxian Road','south',lod)
    for a,b,label in [(EAST_END,PARTY_JOINT,'East party wall'),(PARTY_JOINT,NORTH_END,'East end'),(NORTH_END,WEST_END,'Rear envelope')]:
        long_wall(builder,a,b,label,'blind',lod)
    # Shoulder walls join the street envelope to the projecting drum, stepping above the parapets.
    for a,b,label in [(JIANG_END,left,'West shoulder'),(right,FENG_START,'East shoulder')]:
        f=Facade(builder,a,b,label)
        f.wall(0,13.71,thickness=.52,material='cream aggregate')
        f.box(0,.22,f.length,.44,.54,-.22,'dark granite plinth','base')
        f.box(0,4.24,f.length+.04,.81,.86,.16,'marquee charcoal','canopy return')
        f.box(0,13.62,f.length+.04,.16,.62,-.20,'warm limestone trim','parapet')
        for frac in (-.31,.32):
            f.box(f.length*frac,9.06,.35,9.02,.34,.075,'warm limestone trim','vertical fins')
    poly=Polygon([WEST_END,JIANG_END,*arc(-ARC,ARC,RADIUS,lod),FENG_START,EAST_END,PARTY_JOINT,NORTH_END])
    builder.plan_prism(poly.buffer(-.10),0,.075,'dark granite plinth','Base/enclosed floor slab')
    drum=Point(CENTER).buffer(RADIUS-.23,quad_segs=20 if lod else 40)
    deck=poly.buffer(-.09).difference(drum)
    builder.plan_prism(deck,11.28,11.40,'mineral roof','Roof/lower street deck')
    # Low closed returns below the shoulder caps preserve the prominent flanking steps.
    for a,b,label in [(JIANG_END,left,'West shoulder'),(right,FENG_START,'East shoulder')]:
        f=Facade(builder,a,b,label)
        pts=[f.point(-f.length/2,0,-.49)[:2],f.point(f.length/2,0,-.49)[:2],
             f.point(f.length/2,0,-2.2)[:2],f.point(-f.length/2,0,-2.2)[:2]]
        builder.plan_prism(Polygon(pts),11.36,13.69,'cream aggregate',label+'/raised parapet return')
    # Three-quarter satellite view shows an elongated light roof and deeper stage end. Heights and slopes are inferred.
    t=np.array(EAST_END)-FENG_START;t/=np.linalg.norm(t)
    n=np.array([-t[1],t[0]])
    def roofxy(x,y):return tuple(t*x+n*y)
    def patch(x0,x1,y0,y1):
        return Polygon([roofxy(x0,y0),roofxy(x1,y0),roofxy(x1,y1),roofxy(x0,y1)])
    auditorium=patch(-32.60,23.20,-10.31,16.2)
    builder.plan_prism(auditorium,11.36,14.42,'cream aggregate','Roof/auditorium volume')
    # Low pitched auditorium roof along the long axis. Four continuous slopes carry real section heights.
    profile=[(-10.56,14.45),(-5,15.13),(2.94,15.53),(10.65,15.13),(16.43,14.45)]
    for i,((y0,z0),(y1,z1)) in enumerate(zip(profile,profile[1:])):
        low=[(*roofxy(x,y),z-.12) for x,y,z in [(-32.75,y0,z0),(23.36,y0,z0),(23.36,y1,z1),(-32.75,y1,z1)]]
        verts=low+[(x,y,z+.12) for x,y,z in low]
        builder.add(verts,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],'mineral roof','Roof/auditorium pitched plane')
        if not lod:
            for x in np.arange(-31.8,23.2,3.6):
                builder.tube([(*roofxy(x,y0),z0+.017),(*roofxy(x,y1),z1+.017)],.028,'roof seam zinc',5,'Roof/standing seams')
    # The pitched cover must meet the wall along both sloping end verges.
    # Close each gable to the underlying auditorium, including the thin eaves.
    for x0,x1,name in [(-32.75,-32.55,'west'),(23.16,23.36,'east')]:
        profile_outline=Polygon([(profile[0][0],14.39),*profile,(profile[-1][0],14.39)])
        def map_gable(y,z,x):
            e,north=roofxy(x,y)
            return e,north,z
        builder.prism(profile_outline,x0,x1,map_gable,'cream aggregate','Roof/'+name+' gable')
    stage=patch(23.20,37.1,-13.4,15.8)
    builder.plan_prism(stage,11.38,16.46,'cream aggregate','Roof/stage volume')
    builder.plan_prism(stage.buffer(.12,join_style=2),16.46,16.61,'warm limestone trim','Roof/stage coping')
    builder.plan_prism(stage.buffer(-.15,join_style=2),16.61,16.68,'mineral roof','Roof/stage cover')
