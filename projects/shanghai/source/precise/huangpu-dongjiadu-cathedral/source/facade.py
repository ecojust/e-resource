"""South front before the structural conservation works, in local metres."""
from math import cos, pi, sin
from pathlib import Path

from shapely.affinity import translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes

WIDTH = 30.62
SECTION_DEPTH = 3.2
FONT = Path(__file__).parent / 'fonts/DongjiaduInscriptionSubset.otf'
PALETTE = {
    'lime render': {'color': [.82,.79,.685], 'roughness': .91},
    'warm stone': {'color': [.72,.67,.535], 'roughness': .83},
    'cream carving': {'color': [.90,.85,.73], 'roughness': .78},
    'cool plinth': {'color': [.35,.36,.345], 'roughness': .9},
    'wood leaf': {'color': [.145,.054,.027], 'roughness': .67},
    'carved wood': {'color': [.22,.088,.041], 'roughness': .64},
    'upper glass': {'color': [.115,.137,.132], 'roughness': .31},
    'louvre shadow': {'color': [.12,.125,.118], 'roughness': .90},
    'stone slat': {'color': [.60,.57,.48], 'roughness': .83},
    'inscription ink': {'color': [.034,.029,.022], 'roughness': .75},
    'red ochre': {'color': [.419,.063,.039], 'roughness': .84},
    'slate roof': {'color': [.205,.201,.187], 'roughness': .85},
    'cap metal': {'color': [.292,.197,.165], 'roughness': .62, 'metallic': .17},
    'clock face': {'color': [.097,.11,.106], 'roughness': .58},
    'clock gilt': {'color': [.61,.391,.121], 'roughness': .44, 'metallic': .27},
    'section plaster': {'color': [.59,.57,.516], 'roughness': .96},
}

def curve(start, c1, c2, end, n):
    out=[]
    for i in range(1,n+1):
        t=i/n
        out.append(tuple((1-t)**3*start[k]+3*t*(1-t)**2*c1[k]+3*t*t*(1-t)*c2[k]+t**3*end[k] for k in range(2)))
    return out

def strip(f,path,thickness,back,front,mat,label):
    poly=Polygon([*path,*[(x,z-thickness) for x,z in reversed(path)]])
    f.prism(poly,back,front,mat,label)

def crown(f,x,z,w,lod):
    b=f.builder
    b.lathe((x,-.19),[(z,.225*w),(z+.11*w,.285*w),(z+.21*w,.18*w),(z+.41*w,.118*w),
        (z+.50*w,.21*w),(z+.65*w,.145*w),(z+.85*w,.032*w)],'cream carving',8 if lod else 14,'Gable/stone finials')

def frieze(f,x,w,z,d,name):
    # Projecting multi-member cornices, with lower fillet and projecting drip.
    for dz,height,extra,proj,mat in [
        (-.42,.085,0,.04,'warm stone'),(-.30,.12,.11,.12,'cream carving'),
        (-.16,.16,.19,.21,'lime render'),(.005,.15,.34,.36,'cream carving'),
        (.14,.10,.49,.48,'warm stone'),(.235,.075,.54,.50,'cream carving')]:
        f.box(x,z+dz,w+extra,height,.36+proj,d+proj/2,mat,name)

def tapered_cap(f,x,lod):
    b=f.builder;z=17.86;y=.75
    tiers=[(z,1.60,1.03),(z+.15,1.65,1.07),(z+.26,1.46,.96),(z+.45,1.22,.79),
           (z+.73,.97,.64),(z+1.10,.71,.48),(z+1.52,.59,.40),(z+1.65,.65,.44),
           (z+1.77,.34,.24),(z+1.90,.19,.15)]
    verts=[(x+sx*a,y+sy*c,h) for h,a,c in tiers for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]]
    faces=[(3,2,1,0),tuple(range(len(verts)-4,len(verts)))]
    for k in range(len(tiers)-1):
        for j in range(4):faces.append((4*k+j,4*k+(j+1)%4,4*k+4+(j+1)%4,4*k+4+j))
    b.add(verts,faces,'cap metal','Towers/concave hipped roof')
    b.lathe((x,y),[(19.76,.13),(19.86,.16),(19.98,.07),(20.23,.047),(20.37,.012)],
        'cap metal',8 if lod else 12,'Towers/finial')
    for dx in [-1.33,1.33]:
        b.lathe((x+dx,.48),[(17.96,.23),(18.09,.27),(18.22,.15),(18.39,.095),(18.49,.04)],
                'warm stone',8 if lod else 12,'Towers/acrotëria')

def pilaster(f,x,width,top,lower,lod):
    f.box(x,lower+.18,width+.19,.34,.45,.14,'cool plinth','piers/plinth')
    f.box(x,(lower+.35+top)/2,width,top-lower-.35,.34,.17,'lime render','piers/shaft')
    for z,w,h,p in [(lower+.42,width+.09,.075,.25),(top-.42,width+.11,.12,.22),
                       (top-.23,width+.18,.20,.26),(top-.052,width+.27,.115,.30)]:
        f.box(x,z,w,h,.43,p,'cream carving','piers/base and capital')
    for side in [-1,1]:
        dx=x+side*width*.39;dz=top-.21
        circular=Point(dx,dz).buffer(width*.125,quad_segs=4 if lod else 8)
        f.prism(circular,.49,.53,'warm stone','piers/Ionic capital volutes')
        if not lod:f.prism(circular.buffer(-.032),.531,.55,'cream carving','piers/volute centres')

def tablet(f,x,top,text,spacing,size,d,lod):
    for n,ch in enumerate(text):
        for _,p in lettering_shapes(ch,size,size*.97,font=FONT):
            if lod:p=p.simplify(.014,preserve_topology=True)
            f.prism(translate(p,xoff=x,yoff=top-n*spacing),d,d+.024,'inscription ink','Inscription/'+ch)

def statue(f,x,lod):
    b=f.builder;h=2.05;y=.17
    # Coupled head, robed torso, folded arms and curved drapery. Attributes unresolved.
    b.lathe((x,y),[(h,.28),(h+.09,.31),(h+.66,.233),(h+1.08,.245),(h+1.27,.187),
                    (h+1.33,.098)],'cream carving',9 if lod else 15,'Lower niches/robed figures')
    b.lathe((x,y-.01),[(h+1.30,.08),(h+1.37,.13),(h+1.56,.15),(h+1.66,.075)],
            'cream carving',9 if lod else 14,'Lower niches/head')
    for s in [-1,1]:
        b.tube([(x+s*.215,y,h+1.19),(x+s*.269,y-.08,h+.99),(x+s*.085,y-.22,h+1.025)],
               .069,'cream carving',6 if lod else 9,'Lower niches/arms')
        if not lod:
            for n in [1,2]:
                u=.072*n*s;b.tube([(x+u*.4,y-.17,h+1),(x+u,y-.19,h+.58),(x+u*1.5,y-.18,h+.08)],
                                    .020,'warm stone',6,'Lower niches/robe folds')

def wood_door(f,x,w,h,lod):
    ap=box(x-w/2,0,x+w/2,h);f.prism(ap.buffer(.014,join_style=2),-.42,-.37,'wood leaf','closed panelled double door')
    ncol=4 if w>2 else 2;nrow=6 if w>2 else 4
    for i in range(ncol):
        for j in range(nrow):
            x0=x-w/2+.10+i*(w-.20)/ncol;x1=x-w/2+.10+(i+1)*(w-.20)/ncol
            z0=.22+j*(h-.43)/nrow;z1=.22+(j+1)*(h-.43)/nrow
            q=box(x0+.045,z0+.04,x1-.045,z1-.04)
            f.prism(q.difference(q.buffer(-.044,join_style=2)),-.371,-.332,'carved wood','doors/raised panel borders')
            if not lod:f.prism(q.buffer(-.081,join_style=2),-.372,-.350,'carved wood','doors/fielded panels')
    for s in [-1,1]:f.box(x+s*.09,h*.455,.043,.22,.052,-.316,'clock gilt','doors/pulls')
    return ap

def front(b,lod):
    half=WIDTH/2;f=Facade(b,(-half,0),(half,0),'South');seg=9 if lod else 21
    lower_top=11.66;top_left=[(-half,lower_top),(-half,17.70),(-11.72,17.70),(-11.72,14.02)]
    top_left+=curve(top_left[-1],(-11.56,14.67),(-10.18,14.01),(-9.54,14.93),seg)
    top_left.extend([(-9.22,14.93),(-9.22,15.21),(-8.66,15.21),(-8.66,14.96)])
    top_left+=curve(top_left[-1],(-6.61,15.09),(-5.18,16.90),(-5.11,18.79),seg)
    top_left.extend([(-5.11,19.05),(-5.52,19.05),(-5.52,19.36),(-3.84,19.36),(-3.84,19.61),(-3.47,19.61),(-3.47,19.83)])
    top_left+=curve(top_left[-1],(-2.85,19.91),(-2.34,20.73),(-2.14,21.33),seg)
    top_left.extend([(-1.84,21.33),(-1.84,21.54),(-1.61,21.55),(-1.62,21.91)])
    top_left+=curve(top_left[-1],(-1.54,22.60),(-.86,22.14),(-.60,22.88),seg)
    top_left+=curve(top_left[-1],(-.45,23.12),(-.21,22.91),(0,23.22),seg)
    edge=top_left+[(-x,z) for x,z in reversed(top_left[:-1])]
    outline=Polygon([(-half,0),(half,0),*reversed(edge)])
    holes=[wood_door(f,0,2.91,5.22,lod)]
    for s in [-1,1]:
        x=s*8.93;holes.append(wood_door(f,x,1.54,3.25,lod));w=box(x-.69,5.19,x+.69,8.13);holes.append(w)
        f.window(w,2,4,'inscription ink',False,'upper glass',label='side upper casement')
        f.box(x,5.1,1.89,.17,.44,.14,'warm stone','windows/apron sill')
        for dx in [-.916,.916]:
            f.box(x+dx,6.64,.14,3.03,.22,.072,'warm stone','windows/plain surrounds')
        for z,ww,hh in [(3.43,1.91,.21),(3.62,2.36,.16),(4.04,2.29,.25),(4.30,2.68,.14)]:
            f.box(x,z,ww,hh,.53,.18,'cream carving','side doors/layered lintels')
        niche=opening(s*13.55,1.94,1.02,2.30,.54,seg);holes.append(niche)
        f.prism(niche.buffer(.012),-.52,-.49,'warm stone','blind niches/recess');statue(f,s*13.55,lod)
        f.prism(niche.buffer(.11,join_style=2).difference(niche),.018,.08,'cream carving','blind niches/arched border')
        f.box(s*13.55,1.82,1.40,.19,.61,.15,'cream carving','blind niches/projecting bracket')
        tower=s*13.52;vent=opening(tower,12.54,1.64,3.94,.85,seg);holes.append(vent)
        f.prism(vent.buffer(.01),-.31,-.28,'louvre shadow','bell openings/recess')
        f.prism(vent.buffer(.15,join_style=2).difference(vent),.013,.11,'cream carving','bell openings/hood')
        for j in range(14):
            z=12.67+j*.257;q=vent.intersection(box(tower-1,z,tower+1,z+.12))
            f.prism(q,-.21,-.102,'stone slat','bell openings/horizontal louvres')
        for u in [s*14.85,s*12.18]:pilaster(f,u,.58,11.16,.02,lod)
        frieze(f,tower,3.47,17.58,.06,'bell towers/projecting cornice');tapered_cap(f,tower,lod)
        for u in [s*5.84,s*3.07]:pilaster(f,u,.67,11.18,.02,lod)
        crown(f,s*8.97,15.22,.82,lod);crown(f,s*3.58,19.83,.96,lod)
    # Fanlight bottom follows the raised curved hood of the central door.
    arch_base=[(-1.54,6.46),(-1.24,6.46),*curve((-1.24,6.46),(-.68,7.20),(.68,7.20),(1.24,6.46),seg),(1.54,6.46)]
    transom=Polygon([*arch_base,(1.54,7.83),*curve((1.54,7.83),(.68,8.53),(-.68,8.53),(-1.54,7.83),seg)])
    holes.append(transom);f.window(transom,6,2,'inscription ink',False,'upper glass',label='central curved transom')
    f.prism(transom.buffer(.145,join_style=2).difference(transom),.016,.17,'warm stone','transom/curved surround')
    f.wall(0,23.22,holes,.75,'lime render',outline)
    for s in [-1,1]:
        for x in [s*2.01,s*1.80]:
            f.box(x,2.76,.21,5.49,.48,.15,'cream carving','central portal/jamb')
            for z in [.21,1.77,2.03,2.27,5.39]:f.box(x,z,.35,.10,.51,.20,'warm stone','central portal/jamb mouldings')
        p=[(s*1.02,5.95),(s*1.24,5.78),(s*1.51,5.87),(s*1.70,6.02),(s*1.96,6.02),(s*2.20,5.91),(s*2.39,5.89)]
        if s<0:p.reverse()
        strip(f,p,.12,.11,.44,'warm stone','portal/winged hood')
        x=s*4.37;f.box(x,5.72,.91,7.49,.169,.081,'warm stone','couplets/rebated surrounds')
        f.box(x,5.72,.753,7.28,.065,.177,'cream carving','couplets/tablet')
        inscription='宣仁宣義聿昭拯濟大權衡' if s<0 else '無始無終先作形聲真主宰'
        tablet(f,x,8.90,inscription,.636,.49,.214,lod)
    centre=[(-1.28,5.83),*curve((-1.28,5.83),(-.62,6.78),(.62,6.78),(1.28,5.83),seg*2)]
    for dz,depth in [(0,.57),(-.18,.47),(-.33,.39)]:
        strip(f,[(x,z+dz)for x,z in centre],.15,.09,depth,'cream carving','central door/arched pediment')
    for x,w,d in [(0,12.3,.19),(-9.0,5.90,.03),(9.0,5.90,.03),(-13.58,3.53,.10),(13.58,3.53,.10)]:
        frieze(f,x,w,11.72,d,'principal broken entablature')
    frieze(f,0,10.73,19.24,.17,'central tall gable cornice')
    for s in [-1,1]:
        for xx in [s*4.47,s*3.85]:f.box(xx,15.50,.23,6.44,.35,.12,'cream carving','high gable/paired pilaster')
        path=[(s*5.01,18.84),*curve((s*5.01,18.84),(s*5.16,16.51),(s*6.08,15.21),(s*6.72,14.19),seg)]
        spiral=[(s*(6.11+.64*(1-i/(seg*2+3))*cos(-.11-i*2*pi/(seg*2))),13.42+.76*(1-i/(seg*2+3))*sin(-.11-i*2*pi/(seg*2))) for i in range(seg*2+1)]
        sc=[*path,*curve(path[-1],(s*7.23,13.68),(s*7.12,12.85),spiral[0],seg),*spiral[1:]]
        poly=LineString(sc).buffer(.094,quad_segs=4);f.prism(poly,.012,.165,'warm stone','shoulders/scrolled volute')
        for u in [s*5.62,s*6.14]:f.box(u,6.07,.34,9.63,.34,.10,'lime render','lower body/recessed high pilasters')
    crest=LineString(edge[4:-4]).buffer(.066,join_style=2,cap_style=2)
    f.prism(crest,.012,.16,'cream carving','stepped crest coping')
    f.box(0,15.24,4.98,3.82,.124,.073,'red ochre','clock/recessed vermilion field')
    for radius,d0,d1,mat in [(1.33,.151,.239,'warm stone'),(1.26,.239,.291,'inscription ink'),(1.13,.291,.315,'clock face'),(.55,.315,.344,'cream carving'),(.39,.344,.358,'clock gilt')]:
        f.prism(Point(0,15.24).buffer(radius,quad_segs=8 if lod else 18),d0,d1,mat,'clock/concentric dial')
    for i in range(12):
        a=2*pi*i/12;q=LineString([(.66*sin(a),15.24+.66*cos(a)),(1.08*sin(a),15.24+1.08*cos(a))]).buffer(.026)
        f.prism(q,.317,.336,'inscription ink','clock/dial divisions')
    plaque=opening(0,19.85,1.41,2.87,.30,seg)
    f.prism(plaque.buffer(.135,join_style=2),.087,.165,'red ochre','top tablet/red outline');f.prism(plaque,.166,.198,'cream carving','top tablet/face');tablet(f,0,22.15,'天主堂',.85,.62,.202,lod)
    # The open iron cross shows paired rails with closely spaced ties in the close-up.
    for shift in [-.093,.093]:
        b.box((shift,-.13,24.58),(.045,.14,2.86),'inscription ink',label='Crown/cross iron rails')
        b.box((0,-.13,25.30+shift),(2.19,.14,.045),'inscription ink',label='Crown/cross iron rails')
    for i in range(14):
        z=23.22+i*.204
        b.tube([(-.083,-.13,z),(.083,-.13,z+.088)],.026,'inscription ink',6,'Crown/iron lattice')
    for i in range(11):
        x=-1.055+i*.205
        b.tube([(x,-.13,25.212),(x+.096,-.13,25.388)],.023,'inscription ink',6,'Crown/iron lattice')
    for u in [-4.85,-4.43,4.43,4.85]:
        bracket=Polygon([(u-.09,18.78),(u+.09,18.78),(u+.13,19.04),(u-.13,19.04)])
        f.prism(bracket,.09,.40,'cream carving','high cornice/flanking brackets')
    for x,z in [(-1.10,25.30),(1.10,25.30),(0,26.02)]:
        f.prism(Point(x,z).buffer(.14,quad_segs=6),.048,.22,'inscription ink','Crown/cross tips')
    # The model ends in a shallow slice of the nave. Historic body stays coarse on the city map.
    for x in [-half+.16,half-.16]:b.box((x,SECTION_DEPTH/2,5.68),(.32,SECTION_DEPTH,11.36),'section plaster',label='Section/plain side returns')
    b.box((0,SECTION_DEPTH-.15,5.72),(WIDTH,.30,11.44),'section plaster',label='Section/plain rear closure')
    for x0,x1,z0,z1 in [(-half+.10,-5.2,11.48,13.48),(-5.2,0,13.48,16.05),(0,5.2,16.05,13.48),(5.2,half-.10,13.48,11.48)]:
        def roof(x,y,z):return (x,y,z0+(x-x0)*(z1-z0)/(x1-x0)+z)
        b.prism(box(x0,.77,x1,SECTION_DEPTH),-.16,0,roof,'slate roof','Section/roof behind front')
    for s in [-1,1]:
        poly=Polygon([(s*half,11.35),(s*half,11.48),(s*5.20,13.48),(0,16.05),(0,11.35)])
        f.prism(poly,-SECTION_DEPTH,-SECTION_DEPTH+.19,'section plaster','shallow attic return')
