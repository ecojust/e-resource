"""West lane entrance and south garden elevation of 17, Lane 329, Xinhua Road.

Metres. The photographs establish the openings and the different roof levels.
The oblique garden wall, rear return and roof depth are aligned to the city outline.
"""
import math

from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

STUCCO = 'warm roughcast'
RENDER = 'pale porch render'
BRICK = 'fired arch brick'
MORTAR = 'lime mortar'
WOOD = 'oxblood joinery'
GLASS = 'smoked window glass'
IRON = 'black iron'
TILE = 'weathered barrel tile'
CAP = 'raised tile roll'
SHADE = 'dark shutter'
STEP = 'threshold stone'
PLATE = 'green enamel'
NUMERAL = 'ivory enamel'
PALETTE = {k: dict(color=c,roughness=r,metallic=m) for k,c,r,m in [
    (STUCCO,[.71,.65,.54],.90,0), (RENDER,[.79,.75,.66],.85,0),
    (BRICK,[.435,.230,.132],.84,0), (MORTAR,[.65,.56,.44],.94,0),
    (WOOD,[.207,.082,.075],.68,0), (GLASS,[.160,.212,.212],.32,.22),
    (IRON,[.117,.121,.105],.55,.48), (TILE,[.44,.222,.119],.87,0),
    (CAP,[.52,.291,.172],.85,0), (SHADE,[.252,.202,.143],.74,0),
    (STEP,[.492,.475,.422],.92,0), (PLATE,[.056,.232,.174],.41,.18),
    (NUMERAL,[.86,.85,.70],.49,.12)]}


def pointed(center, width, spring, rise):
    # Two shallow sweeps meet in a visible peak over the folding door.
    curve = [(center+width*.5*t, spring+rise*(1-abs(t)**.76))
             for t in [i/12 for i in range(12,-13,-1)]]
    return Polygon([(center-width/2,.12),(center+width/2,.12),*curve])


def masonry(face, aperture, kind, lod):
    left,low,right,high = aperture.bounds
    mid = (left+right)/2
    band = aperture.buffer(.185,join_style=2).difference(aperture)
    band = band.intersection(box(left-.3,low+.02,right+.3,high+.3))
    face.prism(band,.012,.115,BRICK,kind+' brick reveal')
    spring = 2.78 if kind=='garage' else 2.52
    for i in range(1,int(spring/.18)):
        z=.13+.18*i
        for u in (left,right):
            seam = band.intersection(box(u-.24,z,u+.24,z+.014))
            face.prism(seam,.116,.123,MORTAR,kind+' jamb bed joints')
    n = 12 if lod else 24
    for i in range(1,n):
        t=i/n
        if kind=='garage':
            x=left+t*(right-left)
            z=spring+(high-spring)*(1-abs(2*t-1)**.76)
            dx=.065*(2*t-1)
        else:
            angle=math.pi*(1-t)
            x=mid+(right-left)*.5*math.cos(angle)
            z=spring+(high-spring)*math.sin(angle)
            dx=.18*math.cos(angle)
        seam=LineString([(x,z-.01),(x+dx,z+.24)]).buffer(.009,cap_style=2).intersection(band)
        face.prism(seam,.116,.123,MORTAR,kind+' radial joints')


def panel_door(face, outline, leaves, label, dark=False):
    left,low,right,high=outline.bounds
    face.prism(outline.buffer(.004),-.162,-.124,WOOD,label+' leaf backing')
    for i in range(leaves):
        start=left+(right-left)*i/leaves
        stop=left+(right-left)*(i+1)/leaves
        stile=outline.intersection(box(start+.019,low+.03,start+.076,high))
        face.prism(stile,-.120,-.076,SHADE if dark else WOOD,label+' stiles')
        for a,b in ((low+.20,1.05),(1.20,high-.21)):
            raised=outline.intersection(box(start+.125,a,stop-.115,b))
            face.prism(raised,-.119,-.092,WOOD,label+' raised panels')


def window(face,u,z,w,h,label,columns=2,rows=2,shutters=False,sill=True):
    aperture=box(u-w/2,z,u+w/2,z+h)
    face.window(aperture,columns,rows,frame=SHADE,glass=GLASS,trim=False,label=label)
    if sill:
        face.box(u,z-.035,w+.22,.11,.26,.04,STEP,label+' sill')
    if shutters:
        for sign in (-1,1):
            cx=u+sign*(w*.5+.18)
            face.box(cx,z+h/2,.32,h,.1,.035,SHADE,label+' shutter frame')
            for i in range(9):
                face.box(cx,z+.12+(h-.23)*i/8,.27,.045,.07,.11,WOOD,label+' shutter slats')


def hip(b,x0,y0,x1,y1,eave,rise,label,lod):
    """Four clay slopes and the semicircular profiles of their ridge and rolls."""
    width,depth=x1-x0,y1-y0
    h=eave+rise
    inset=min(width,depth)*.35
    if width>depth:
        p=(x0+inset,(y0+y1)/2,h);q=(x1-inset,(y0+y1)/2,h)
        high=[(p,q),(q,q),(q,p),(p,p)]
    else:
        p=((x0+x1)/2,y0+inset,h);q=((x0+x1)/2,y1-inset,h)
        high=[(p,p),(p,q),(q,q),(q,p)]
    corners=[(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave)]
    for i,(ra,rb) in enumerate(high):
        va,vb=corners[i],corners[(i+1)%4]
        poly=[va,vb,rb] if ra==rb else [va,vb,rb,ra]
        b.add(poly,[tuple(range(len(poly)))],TILE,label+'/hip slopes')
        b.add([va,vb,(*vb[:2],eave-.13),(*va[:2],eave-.13)],[(0,3,2,1)],TILE,label+'/thick eaves')
        n=max(2,round(math.dist(va,vb)/(.57 if lod else .25)))
        for j in range(1,n):
            t=j/n
            lower=tuple(a*(1-t)+b0*t for a,b0 in zip(va,vb))
            upper=tuple(a*(1-t)+b0*t for a,b0 in zip(ra,rb))
            b.tube([lower,upper],.043,CAP,5 if lod else 8,label+'/barrel tile rolls')
        b.tube([va,ra],.09,CAP,6 if lod else 10,label+'/hip caps')
    b.tube([p,q],.105,CAP,7 if lod else 12,label+'/ridge cap')


def single_pitch(b,x0,x1,y0,y1,low,high,lod,label):
    def slope(x,y,d):return x,y,low+(y-y0)*(high-low)/(y1-y0)+d
    b.prism(box(x0,y0,x1,y1),-.12,.012,slope,TILE,label+'/tile bed')
    n=round((x1-x0)/(.38 if lod else .205))
    for i in range(n+1):
        x=x0+(x1-x0)*i/n
        b.tube([slope(x,y0,.025),slope(x,y1,.025)],.053,CAP,6 if lod else 9,label+'/clay rolls')
    b.box(((x0+x1)*.5,y0,low-.1),(x1-x0+.10,.18,.13),RENDER,label=label+'/eaves fascia')
    b.box(((x0+x1)*.5,y0-.06,low-.19),(x1-x0+.16,.15,.06),RENDER,label=label+'/lower cornice')


def porch_details(b,lane,arch,lod):
    # The entrance reveal is deep and laid in brick from the front edge to the door.
    left,right=2.02,3.76
    for x in (left+.015,right-.015):
        b.box((x,-.38,1.28),(.035,.87,2.40),BRICK,label='portal/brick reveal depth')
        for i in range(1,15):
            b.box((x,-.38,.14+i*.157),(.040,.87,.012),MORTAR,label='portal/reveal brick courses')
    ring=arch.buffer(.17,join_style=2).difference(arch).intersection(box(-1.08,2.51,1.08,3.70))
    porch=Facade(b,(1.51,-.88),(4.27,-.88),'deep arched entry')
    porch.prism(ring,-.84,.010,BRICK,'curved brick barrel')
    # The pair of white corbels taper sharply into the masonry over the springing.
    for x in (1.61,4.16):
        side=Facade(b,(x,-.07),(x,-1.02),'portal canopy corbel')
        profile=Polygon([(-.43,3.62),(.47,3.62),(.44,3.43),(.31,3.34),
                         (.13,3.31),(-.05,3.08),(-.19,2.76),(-.29,2.55),(-.43,2.55)])
        side.prism(profile,-.095,.095,RENDER,'shaped support')
    # Green enamel plate and number are legible in the independently dated west-lane view.
    cx,cz=1.21,2.18
    porch.box(cx,cz,.30,.222,.042,.065,PLATE,'green street number plate')
    for points in [[(-.12,.04),(-.073,.076),(-.073,-.061)],
                   [(-.114,-.064),(-.033,-.064)],[(.008,.075),(.112,.075),(.045,-.063)]]:
        b.tube([porch.point(cx+u,cz+v,.094) for u,v in points],.012,NUMERAL,7,'west lane/number 17')
    # Pinched curves between the vertical rods are visible against the glass door.
    for x in (2.51,2.89,3.27):
        for i in range(4):
            z=.41+i*.61
            for sign in (-1,1):
                pts=[lane.point(x+sign*.104*math.sin(t*math.pi*2),z+t*.57,-.060)
                     for t in (j/(8 if lod else 14) for j in range(9 if lod else 15))]
                b.tube(pts,.019,IRON,5 if lod else 7,'main door/curved iron grille')
    for x,width in [(-4.23,1.50),(4.90,1.46)]:
        def awning(u,y,d):return u,y,2.94+.42*(y+.40)+d
        b.prism(box(x-width/2,-.47,x+width/2,.01),-.04,0,awning,WOOD,'smaller openings/oxblood awnings')
        b.box((x,-.47,2.89),(width,.045,.14),WOOD,label='smaller openings/awning valances')


def west(b,lod):
    lane=Facade(b,(-5.80,0),(5.80,0),'west lane ground floor')
    garage=pointed(-.73,3.63,2.78,.40)
    side=box(-4.84,.13,-3.56,2.84)
    entry=opening(2.89,.12,1.63,3.22,.82,18 if lod else 38)
    light=box(4.44,1.37,5.32,2.89)
    lane.wall(.05,3.66,[garage,side,entry,light],.29,STUCCO)
    panel_door(lane,garage,4,'folding coach door')
    panel_door(lane,side,2,'side door',True)
    masonry(lane,garage,'garage',lod)
    lane.window(entry,2,3,frame=IRON,glass=GLASS,trim=False,label='main door')
    for off in (-.40,-.14,.14,.40):
        bar=entry.intersection(box(2.89+off-.021,.16,2.89+off+.021,3.45))
        lane.prism(bar,-.108,-.060,IRON,'entrance security grille')
    window(lane,4.88,1.37,.88,1.52,'small west light',2,2)
    porch=Facade(b,(1.51,-.88),(4.27,-.88),'projecting entrance porch')
    arch=opening(0,.08,1.74,3.31,.87,18 if lod else 38)
    porch.wall(.08,3.81,[arch],.34,RENDER)
    masonry(porch,arch,'portal',lod)
    for x in (1.64,4.14):
        b.box((x,-.39,1.85),(.25,.94,3.54),RENDER,label='porch/side returns')
    b.box((2.89,-.62,.08),(2.53,1.01,.12),STEP,label='porch/step')
    single_pitch(b,1.36,4.40,-1.12,.93,3.90,4.52,lod,'porch/lean-to hood')
    porch_details(b,lane,arch,lod)
    # The garage and left door occupy a tiled lower projection beneath the upper wall.
    for x0,x1,name in [(-5.88,-3.23,'side entrance'),(-3.29,1.45,'garage roof'),(4.34,5.87,'small light hood')]:
        y0,y1=-.26,1.52
        def slope(x,y,z):return x,y,3.60+.37*(y-y0)+z
        b.prism(box(x0,y0,x1,y1),-.12,.015,slope,TILE,name+'/tiles')
        count=round((x1-x0)/(.49 if lod else .205))
        for i in range(count+1):
            x=x0+(x1-x0)*i/count
            b.tube([slope(x,y0,.025),slope(x,y1,.025)],.043,CAP,6 if lod else 9,name+'/rolls')
    upper=Facade(b,(-5.79,1.37),(3.55,1.37),'west upper storey')
    lights=[(-2.81,1.35),(0,1.85),(2.67,1.30)]
    holes=[box(x-w/2,4.83,x+w/2,6.45)for x,w in lights]
    upper.wall(3.57,6.95,holes,.24,STUCCO)
    for x,w in lights:window(upper,x,4.83,w,1.62,'upper casements',2,2)
    b.box((-1.11,1.29,6.91),(9.65,.33,.16),RENDER,label='west upper/eaves cornice')


def garden(b,lod):
    # With the camera in the garden, the left side is toward the lane.
    outer=Facade(b,(5.56,.04),(5.56,13.51),'south garden arcade')
    centers=(-4.73,-1.66,1.59,4.70)
    shapes=[opening(x,.10,2.55,3.17,.72,18 if lod else 36) for x in centers]
    outer.wall(.08,3.66,shapes,.29,STUCCO)
    for x in centers:
        for sign in (-1,1):
            outer.box(x+sign*1.40,2.52,.33,.14,.42,.039,RENDER,'arcade impost blocks')
    behind=Facade(b,(4.14,.32),(4.14,13.38),'south recessed lower wall')
    rearholes=[box(x-.88,.14,x+.88,2.84)for x in centers]
    behind.wall(.06,3.62,rearholes,.24,STUCCO)
    for x,ap in zip(centers,rearholes):
        behind.window(ap,2,3,frame=SHADE,glass=GLASS,trim=False,label='garden casements')
    b.box((4.88,6.78,3.63),(1.85,13.53,.18),STEP,label='garden terrace/slab')
    for i in range(36 if not lod else 19):
        y=.21+13.08*i/(35 if not lod else 18)
        b.tube([(5.72,y,3.72),(5.72,y,4.50)],.019,IRON,6,'garden terrace/uprights')
    for z in (3.83,4.44,4.52):
        b.tube([(5.72,.18,z),(5.72,13.26,z)],.025,IRON,7,'garden terrace/rails')
    # Square tower at the garden's eastern end, with an upper shutter each side.
    x0,x1,y0,y1=-.43,4.29,7.86,13.51
    top=9.37
    faces=[Facade(b,(x0,y0),(x1,y0),'tower/west'),Facade(b,(x1,y0+.23),(x1,y1-.23),'tower/garden'),
           Facade(b,(x1,y1),(x0,y1),'tower/east'),Facade(b,(x0,y1-.23),(x0,y0+.23),'tower/north')]
    # The two side walls stop at the inner skin of the front and back walls.
    # This exposes one plaster surface at each corner and preserves the outer dimensions.
    for i,f in enumerate(faces):
        top_windows=[box(u-.454,7.70,u+.454,8.94) for u in (-1.035,0,1.035)]
        lower=box(-1.36,3.75,1.36,6.27)
        holes=[*top_windows,lower] if i==1 else (top_windows if i==0 else [])
        f.wall(3.64,top,holes,.23,STUCCO)
        if i in (0,1):
            for u in (-1.035,0,1.035):
                window(f,u,7.70,.908,1.24,'loft casement pair',2,3,sill=False)
            f.box(0,7.665,3.95,.11,.26,.04,STEP,'continuous sill under the three lights')
            for u in (-1.79,1.79):
                f.box(u,8.32,.39,1.15,.090,.03,SHADE,'loft shutter side panel')
                for j in range(10):f.box(u,7.81+j*.103,.34,.049,.05,.087,WOOD,'loft shutter blades')
        if i==1:window(f,0,3.75,2.72,2.52,'terrace doors',3,2)
        f.box(0,top-.04,f.length+.12,.14,.29,.035,RENDER,'cornice')
    hip(b,x0-.22,y0-.23,x1+.23,y1+.22,9.41,.78,'garden tower/hip',lod)
    mid=Facade(b,(3.55,1.61),(3.55,y0),'garden upper return')
    hole=box(-.80,4.45,.80,6.34)
    mid.wall(3.64,6.94,[hole],.23,STUCCO)
    window(mid,0,4.45,1.6,1.89,'second storey window')
    hip(b,-5.96,1.16,3.72,8.04,7.01,1.08,'west wing/hip',lod)
    hip(b,-6.22,7.91,-.41,13.77,6.48,.81,'east wing/hip',lod)


def add_house(builder,lod):
    west(builder,lod)
    garden(builder,lod)
    north=Facade(builder,(-6.08,13.56),(-5.80,.06),'north return')
    north.wall(.04,6.47,[],.25,STUCCO)
    east=Facade(builder,(5.50,13.55),(-6.08,13.55),'east return')
    east.wall(.04,6.48,[],.23,STUCCO)
    builder.box((-.09,6.78,.047),(11.12,13.44,.089),STEP,label='building/ground slab')
