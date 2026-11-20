"""Photo-informed outer and recessed northern walls at 59 Hong Kong Road, in metres."""
from math import cos, pi, sin
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening

STONE = 'warm artificial stone'
PALE = 'raised stone mouldings'
SHADE = 'weathered stone recess'
GLASS = 'smoked window glass'
SASH = 'bronze glazing bars'
BASE = 'dark plinth'
WOOD = 'entrance doors'
PLATE = 'green address enamel'
LETTER = 'cream numerals'
CUT = 'section stone'
PALETTE = {
    STONE: {'color':[.55,.48,.39], 'roughness':.86},
    PALE: {'color':[.68,.61,.51], 'roughness':.78},
    SHADE: {'color':[.40,.335,.27], 'roughness':.89},
    GLASS: {'color':[.145,.193,.21], 'metallic':.17,'roughness':.29},
    SASH: {'color':[.105,.099,.084], 'metallic':.22,'roughness':.52},
    BASE: {'color':[.31,.283,.247], 'roughness':.87},
    WOOD: {'color':[.19,.139,.105], 'roughness':.64},
    PLATE: {'color':[.018,.30,.219], 'roughness':.5},
    LETTER: {'color':[.9,.88,.74], 'roughness':.63},
    CUT: {'color':[.43,.40,.36], 'roughness':.92},
}
HALF = 10.77
COLUMN_X = [-7.35,-4.41,-1.47,1.47,4.41,7.35]
BAY_X = [-5.88,-2.94,0,2.94,5.88]
COL_Y = .64
REAR_Y = 2.67


def plate(f,x,z,width,height,back,front,material,label):
    f.box(x,z,width,height,front-back,(back+front)/2,material,label)


def ribbon(f,coords,radius,back,front,material,label,lod):
    profile=LineString(coords).buffer(radius,quad_segs=2 if lod else 4)
    f.prism(profile,back,front,material,label)


def moulded_frame(f,x,z,w,h,back,projection,label):
    outer=box(x-w*.5,z,x+w*.5,z+h)
    border=outer.buffer(.105,join_style=2).difference(outer)
    f.prism(border,back,projection,PALE,label+' inner reveal')
    frame=outer.buffer(.187,join_style=2).difference(outer.buffer(.117,join_style=2))
    f.prism(frame,back,projection+.04,STONE,label+' outer fillet')


def window(f,x,z,w,h,lod,label,barred=False):
    cut=opening(x,z,w,h)
    f.prism(cut.buffer(.012,join_style=2),-.35,-.32,GLASS,label+' glass')
    inset=cut.buffer(-.075,join_style=2)
    bars=[box(x-.032,z,x+.032,z+h),box(x-w/2,z+h*.63-.034,x+w/2,z+h*.63+.034)]
    if barred:
        for n in range(-2,3):
            xx=x+n*w/5.6
            bars.append(box(xx-.017,z+.06,xx+.017,z+h-.06))
    frame=cut.difference(inset.difference(unary_union(bars)))
    f.prism(frame,-.313,-.23,SASH,label+' bars')
    plate(f,x,z-.048,w+.16,.10,-.03,.105,PALE,label+' sill')
    return cut


def courses(f,field,lo,hi,bottom,top,lod,label):
    rows=max(1,round((top-bottom)/(.84 if lod else .64)))
    width=1.72
    for row in range(rows):
        z=bottom+(top-bottom)*row/rows;upper=bottom+(top-bottom)*(row+1)/rows
        for j in range(-1,int((hi-lo)/width)+1):
            start=lo+(j+.5*(row%2))*width
            x0=max(lo,start+.012);x1=min(hi,start+width-.012)
            if x1<=x0:continue
            part=field.intersection(box(x0,z+.012,x1,upper-.012))
            if part.area>.012:f.prism(part,.003,.031,STONE,label)


def shaft(b,x,lod,terminal):
    radius=.437
    z0=1.11;z1=7.53
    if terminal:
        # The end member has a flat fluted front, unlike the four detached round shafts.
        b.box((x,COL_Y,(z0+z1)/2),(.84,.83,z1-z0),SHADE,label='engaged terminal shaft')
        for i in range(6 if not lod else 5):
            cnt=6 if not lod else 5
            dx=(i-(cnt-1)/2)*.78/cnt
            b.box((x+dx,COL_Y-.426,(z0+z1)/2),(.073,.105,z1-z0),STONE,label='terminal vertical flutes')
    else:
        grooves=22 if not lod else 16
        angles=[2*pi*i/(grooves*4) for i in range(grooves*4)]
        vertices=[]
        for z,scale in [(z0,1.06),(2.67,1.04),(5.10,.985),(z1,.91)]:
            for i,t in enumerate(angles):
                radial=radius*scale*(1-.102*(1-cos(2*pi*i/4))*.5)
                vertices.append((x+radial*cos(t),COL_Y+radial*sin(t),z))
        n=len(angles)
        faces=[(k*n+i,k*n+(i+1)%n,(k+1)*n+(i+1)%n,(k+1)*n+i) for k in range(3) for i in range(n)]
        b.add(vertices,faces,STONE,'freestanding shafts with recessed flutes')
    b.box((x,COL_Y,.29),(1.19,1.19,.58),STONE,label='square column plinth')
    b.lathe((x,COL_Y),[(.57,.593),(.638,.593),(.675,.525),(.728,.554),(.785,.526),(.838,.458),
                         (.897,.491),(.963,.487),(1.01,.462),(1.12,.460)],PALE,18 if lod else 34,'round column base mouldings')
    b.lathe((x,COL_Y),[(7.48,.402),(7.53,.452),(7.59,.452),(7.64,.405),(7.75,.411),(8.01,.485),(8.27,.567),(8.40,.59)],
            PALE,16 if lod else 32,'Corinthian capital core')


def crown_leaves(b,x,lod):
    # A folded central rib and shallow side lobes form each external acanthus leaf.
    for ring,z,radius,height,shift in [(0,7.59,.415,.49,0),(1,7.82,.46,.49,pi/8)]:
        for j in range(8):
            angle=2*pi*j/8+shift
            def point(r,t,h):
                return (x+r*cos(angle)-t*sin(angle),COL_Y+r*sin(angle)+t*cos(angle),z+h)
            outline=[(0,0),(.07,.10),(.102,.17),(.074,.177),(.12,.26),(.092,.27),
                     (.13,.348),(.079,.36),(.08,.405),(0,height)]
            if lod:outline=[(0,0),(.09,.13),(.102,.23),(.11,.33),(0,height)]
            xy=outline+[(-s,h)for s,h in reversed(outline[1:-1])]
            vertices=[point(radius+.055+.16*(h/height)**1.6,s,h)for s,h in xy]
            ridge=point(radius+.18,0,height*.585)
            b.add(vertices+[ridge],[(i,(i+1)%len(vertices),len(vertices))for i in range(len(vertices))],
                  PALE,'two crowns of carved acanthus')
    for corner in range(4):
        ang=pi/4+corner*pi/2
        for side in [-1,1]:
            pts=[]
            for i in range(8 if lod else 15):
                count=7 if lod else 14;u=i/count;theta=1.92*pi*u
                dist=.42+.205*u+.077*(1-u)*sin(theta)
                tangent=side*(.16*(1-u)+.10*(1-.70*u)*cos(theta))
                pts.append((x+dist*cos(ang)-tangent*sin(ang),COL_Y+dist*sin(ang)+tangent*cos(ang),
                            7.98+.33*u+.055*(1-u)*sin(theta)))
            b.tube(pts,.033 if lod else .039,PALE,5 if lod else 7,'corner capital volutes')
    for z,w,h in [(8.34,1.32,.094),(8.42,1.42,.072),(8.49,1.47,.073)]:
        b.box((x,COL_Y,z),(w,w,h),PALE,label='stepped square abacus')


def wreath(f,x,z,radius,lod,label):
    nr=10 if lod else 18
    for j in range(nr):
        a=2*pi*j/nr
        cx=x+radius*cos(a);cz=z+radius*.78*sin(a)
        outline=Polygon([(cx-.048*cos(a),cz-.048*sin(a)),(cx+.061*cos(a)-.050*sin(a),cz+.061*sin(a)+.050*cos(a)),
                         (cx+.042*cos(a)+.075*sin(a),cz+.042*sin(a)-.075*cos(a))])
        f.prism(outline,.12,.193,PALE,label)


def end_garland(f,x,lod):
    z=4.81;w=1.78;h=1.12
    plate(f,x,z,w,h,.032,.10,SHADE,'garland recessed field')
    frame=box(x-w/2,z-h/2,x+w/2,z+h/2)
    f.prism(frame.buffer(.086,join_style=2).difference(frame),.025,.164,PALE,'garland panel border')
    points=[(x-.68+i*1.36/20,z-.22+.39*((i-10)/10)**2)for i in range(21)]
    ribbon(f,points,.065,.101,.182,PALE,'hanging stone garland',lod)
    for i in range(2,19,2 if lod else 1):
        u,v=points[i]
        for s in [-1,1]:
            leaf=Polygon([(u-.054,v),(u+s*.081,v+.071),(u+s*.105,v-.065),(u+.020,v-.085)])
            if leaf.is_valid:f.prism(leaf,.15,.211,STONE,'garland leaf clusters')
    for sign in [-1,1]:
        u=x+sign*.66
        ribbon(f,[(u,z+.205),(u+sign*.059,z+.04),(u+sign*.079,z-.22),(u+sign*.13,z-.34)],
               .047,.114,.218,PALE,'garland ribbon ends',lod)
        ribbon(f,[(u,z+.18),(u-sign*.07,z+.28),(u-sign*.11,z+.21),(u,z+.17)],
               .028,.13,.224,PALE,'tied garland ribbon',lod)


def shield(f,lod):
    z=12.01
    profile=Polygon([(-.63,z+.75),(-.49,z+.91),(-.23,z+.89),(0,z+.99),(.23,z+.89),(.49,z+.91),
                     (.63,z+.75),(.45,z+.43),(.42,z+.08),(.31,z-.17),(0,z-.40),(-.31,z-.17),
                     (-.42,z+.08),(-.45,z+.43)])
    f.prism(profile,-.03,.19,STONE,'central heraldic shield')
    f.prism(profile.difference(profile.buffer(-.092,join_style=2)),.185,.286,PALE,'shield carved bevel')
    for sign in [-1,1]:
        seq=[(.25,-.33),(.55,-.24),(.69,.02),(.65,.29),(.57,.46),(.67,.76),(.62,.92),(.53,.99),(.45,.97)]
        ribbon(f,[(sign*x,z+h)for x,h in seq],.058,.095,.235,PALE,'shield folded stone rim',lod)


def address(f):
    plate(f,0,3.54,.44,.206,.16,.192,PLATE,'59 Hong Kong Road enamel')
    for points in [[(-.04,3.611),(-.118,3.611),(-.118,3.55),(-.051,3.55),(-.04,3.526),(-.04,3.502),(-.062,3.484),(-.122,3.484)],
                   [(.044,3.487),(.084,3.504),(.108,3.55),(.108,3.591),(.094,3.61),(.056,3.61),(.04,3.592),(.04,3.563),(.058,3.55),(.108,3.55)]]:
        ribbon(f,points,.010,.191,.201,LETTER,'raised address numerals',True)


def add_frontage(b,lod):
    f=Facade(b,(-HALF,0),(HALF,0),'North front')
    inside=Facade(b,(-HALF,REAR_Y),(HALF,REAR_Y),'Portico wall')
    # Three stair nosings stop at the actual columned opening.
    for j in range(3):
        lo=-.55+.30*j;hi=REAR_Y
        b.box((0,(lo+hi)/2,(j+.5)*.135),(14.75,hi-lo,.135),PALE,label='portico entrance steps')
    b.box((0,1.69,.447),(14.9,3.28,.084),STONE,label='portico stone landing')
    d=opening(0,.49,2.03,3.98)
    inside.prism(d.buffer(.008,join_style=2),-.78,-.75,WOOD,'deep central entrance')
    plate(inside,0,1.87,.05,2.7,-.755,-.70,SASH,'double door centre stile')
    for sign in [-1,1]:
        pane=box(sign*.47-.35,.72,sign*.47+.35,2.88)
        inside.prism(pane,-.749,-.726,GLASS,'double door glass')
    plate(inside,0,3.41,2.36,.14,-.06,.18,PALE,'door transom rail')
    screen=box(-.996,3.59,.996,4.44)
    inside.prism(screen,-.748,-.728,GLASS,'glazed transom')
    # Thin metal rhombus grille is visible above the green address plaque.
    for sign in [-1,1]:
        for j in range(14 if lod else 22):
            n=14 if lod else 22
            start=-1.9+j*(3.8/(n-1))
            g=LineString([(start,3.54),(start+sign*.94,4.49)]).intersection(screen)
            if not g.is_empty:
                coords=list(g.coords)
                if len(coords)>1:ribbon(inside,coords,.010,-.720,-.70,SASH,'transom diamond grille',True)
    moulded_frame(inside,0,.49,2.03,3.98,0,.11,'central entrance')
    address(inside)
    back_holes=[d]
    for x in BAY_X:
        back_holes.append(window(inside,x,5.38,1.19,1.74,lod,'portico upper window'))
    for x in [-5.88,5.88]:back_holes.append(window(inside,x,.99,.91,2.14,lod,'outer portico window',True))
    background=box(-7.69,.46,7.69,8.55).difference(unary_union(back_holes))
    inside.prism(background,-.45,0,SHADE,'portico back wall and actual reveals')
    courses(inside,background,-7.69,7.69,.49,8.50,lod,'rear ashlar')
    for z,h,dpt in [(4.55,.12,.16),(4.76,.13,.22),(4.89,.08,.18),(7.85,.16,.15)]:
        plate(inside,0,z,15.39,h,-.03,dpt,PALE,'recessed wall stringcourses')
    # End walls bound the porch and continue as short side returns.
    for sign in [-1,1]:
        x=sign*9.14
        holes=[window(f,x,.78,1.20,2.85,lod,'terminal ground window',True),window(f,x,5.52,1.39,2.06,lod,'terminal upper window')]
        sidewall=box(7.77 if sign==1 else -HALF,.01,HALF if sign==1 else -7.77,8.57).difference(unary_union(holes))
        f.prism(sidewall,-.49,0,SHADE,'terminal solid bays')
        lo,low,hi,high=sidewall.bounds
        courses(f,sidewall,lo,hi,low,high,lod,'terminal stone spandrels')
        plate(f,x,4.10,2.88,.14,-.005,.22,PALE,'terminal sill band')
        end_garland(f,x,lod)
        b.box((sign*7.83,1.51,4.52),(.17,2.47,8.02),STONE,label='sheltered inner end return')
    for i,x in enumerate(COLUMN_X):
        shaft(b,x,lod,i in [0,5]);crown_leaves(b,x,lod)
    b.box((0,1.76,8.57),(15.07,3.43,.17),SHADE,label='stone portico soffit')
    for x in BAY_X:
        outer=box(x-1.26,.49,x+1.26,2.53)
        b.plan_prism(outer.difference(outer.buffer(-.095,join_style=2)),8.42,8.49,STONE,'coffered portico soffit bands')
    upper_holes=[]
    for x in [-9.14,*BAY_X,9.14]:
        up=window(f,x,9.64,1.19,1.18,lod,'third-storey rectangular window')
        upper_holes.append(up)
        moulded_frame(f,x,9.64,1.19,1.18,-.03,.073,'attic window trim')
    upper=box(-HALF,8.51,HALF,11.54).difference(unary_union(upper_holes))
    f.prism(upper,-.43,0,STONE,'third storey')
    for z,h,back,depth in [(8.56,.14,-.1,.22),(8.72,.15,-.1,.27),(8.91,.19,-.1,.25),(9.13,.16,-.1,.37),
                           (9.33,.11,-.1,.48),(9.43,.14,-.1,.59),(11.22,.105,-.03,.16),(11.52,.13,-.04,.29)]:
        plate(f,0,z,2*HALF,h,back,depth,PALE,'continuous moulded entablature and cornice')
    n=49 if lod else 82
    for j in range(n):
        x=(j+.50)*2*HALF/n-HALF
        plate(f,x,9.24,.132,.123,.235,.43,PALE,'cornice dentils')
    for x in BAY_X:wreath(f,x,8.91,.15,lod,'stone frieze wreaths')
    plate(f,0,11.75,2*HALF,.38,-.17,.025,STONE,'attic coping wall')
    plate(f,0,11.94,2*HALF,.088,-.21,.089,PALE,'attic coping')
    plate(f,0,11.90,6.09,.70,-.18,0,STONE,'raised central parapet')
    plate(f,0,12.29,6.14,.103,-.21,.105,PALE,'central parapet coping')
    shield(f,lod)
    # Close the measured street-front study at Y=4.20, leaving the deep block to the city source.
    b.box((0,2.36,11.48),(2*HALF,3.67,.14),CUT,label='front roof section')
    for sign in [-1,1]:
        b.box((sign*(HALF-.115),2.26,5.73),(.23,3.91,11.46),CUT,label='short party-wall return')
    b.box((0,4.15,5.73),(2*HALF,.10,11.46),CUT,label='back section of street frontage')
