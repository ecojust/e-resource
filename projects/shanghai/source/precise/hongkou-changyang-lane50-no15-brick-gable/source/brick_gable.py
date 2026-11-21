"""No. 15 on Lane 50, photographed on 3 February 2015, before the museum extension."""
from math import sin,cos,pi,radians
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely import constrained_delaunay_triangles
from shapely.geometry.polygon import orient

MORTAR='red-brown mortar';BRICKS=('fired red brick','sienna brick','dull russet brick','burnt ochre brick')
RUBBED='gauged brick';SHADOW='deep brick reveal';STONE='weathered step stone';RISER='shaded vertical stone';SILL='light cornice stone'
DARK='dark timber inner door';GLASS='muted glass';DIM='shaded casement recess';WOOD='pale window joinery';GREEN='green enamel';WHITE='cream number enamel'
PALETTE={name:{'color':c,'roughness':r}for name,c,r in [(MORTAR,[.140,.043,.027],.96),(BRICKS[0],[.331,.086,.059],.90),(BRICKS[1],[.263,.062,.043],.92),(BRICKS[2],[.291,.068,.047],.92),(BRICKS[3],[.311,.088,.059],.90),(RUBBED,[.224,.045,.028],.91),(SHADOW,[.151,.045,.027],.90),(STONE,[.234,.225,.213],.92),(RISER,[.117,.109,.101],.95),(SILL,[.356,.331,.290],.90),(DARK,[.032,.029,.026],.83),(GLASS,[.160,.187,.203],.39),(DIM,[.041,.036,.033],.86),(WOOD,[.650,.612,.544],.75),(GREEN,[.021,.128,.081],.71),(WHITE,[.768,.739,.60],.56)]}

def extrude(b,poly,yfront,yback,mat,group):
    if poly.is_empty:return
    if hasattr(poly,'geoms'):
        for geom in poly.geoms:extrude(b,geom,yfront,yback,mat,group)
    elif poly.geom_type=='Polygon'and poly.area>1e-7:
        b.prism(poly,-yback,-yfront,lambda x,z,y:(x,-y,z),mat,group)

def piece(b,xc,y,zc,dx,dy,dz,mat,group):
    b.box((xc,y,zc),(dx,dy,dz),mat,label=group)

def arch(rx,rise,spring,low,n):
    points=[(-rx,low),(rx,low),(rx,spring)]
    points.extend((rx*cos(pi*i/n),spring+rise*sin(pi*i/n))for i in range(1,n+1))
    return Polygon(points)

def arch_bricks(b,rx,rise,spring,band,lod,label):
    count=19 if lod else 31
    for i in range(count):
        lo=(i+.035)*pi/count;hi=(i+.965)*pi/count
        angles=(lo,(lo+hi)/2,hi)
        outer=[((rx+band)*cos(a),spring+(rise+band)*sin(a))for a in angles]
        inner=[(rx*cos(a),spring+rise*sin(a))for a in reversed(angles)]
        extrude(b,Polygon(outer+inner),-.116,.077,RUBBED,label)
    for sign in (-1,1):
        piece(b,sign*(rx+band/2),-.041,spring-.052,band+.084,.222,.104,RUBBED,label+' spring blocks')

def model(b,lod=False):
    n=24 if lod else 42
    lower=arch(.92,.34,2.67,.44,n);upper=arch(.79,.42,4.91,3.39,n)
    body=Polygon([(-1.57,.36),(1.57,.36),(1.57,6.12),(0,7.03),(-1.57,6.12)])
    face=body.difference(unary_union([lower,upper]))
    extrude(b,face,0,.35,MORTAR,'Load-bearing front with two openings')
    # Horizontal stretcher courses are clipped against both arches and the pitched front.
    for row in range(65):
        z=.36+row*.107
        if z>=7.03:break
        for col in range(-7,8):
            x=col*.291+(.1455 if row%2 else 0)
            tile=box(x+.006,z+.004,x+.284,z+.102)
            geom=tile.intersection(face)
            if not geom.is_empty:
                mat=BRICKS[(col*5+row*3+col*row)%4]
                if lod:
                    # The mortar core carries all the returns at a distance; retain the facing of every brick.
                    for tri in constrained_delaunay_triangles(geom).geoms:
                        ring=list(orient(tri,sign=1).exterior.coords)[:3]
                        b.add([(x,-.010,z) for x,z in ring],[(0,1,2)],mat,'Bonded gable brickwork')
                else:
                    extrude(b,geom,-.010,-.0001,mat,'Bonded gable brickwork')
    # The triangular border consists of square projecting steps below each raking coping.
    for side in (-1,1):
        for i in range(8):
            x0=i*.189;x1=(i+1)*.189;z=6.68-i*.102
            piece(b,side*(x0+x1)/2,-.066,z,x1-x0,.151,.109,RUBBED,'Stepped brick pediment band')
        coords=[(0,7.04),(side*1.60,6.11),(side*1.60,6.044),(0,6.973)]
        extrude(b,Polygon(coords),-.077,.34,SILL,'Sloping gable coping')
    for rx,rise,spring,band,label in [(.92,.34,2.67,.145,'Door arch voussoirs'),(.79,.42,4.91,.15,'Window arch voussoirs')]:
        arch_bricks(b,rx,rise,spring,band,lod,label)
    for side in (-1,1):
        piece(b,side*1.044,.046,1.54,.22,.235,2.23,SHADOW,'Door jamb returns')
        for z in (.78,2.46):piece(b,side*1.046,-.065,z,.28,.20,.077,RUBBED,'Lower jamb bands')
        piece(b,side*.888,.05,4.16,.194,.215,1.47,SHADOW,'Window jambs')
    pane=arch(.773,.404,4.908,3.421,n)
    # The upper light and left leaf remain in plane. The right leaf is open in the 2015 image.
    fixed = pane.difference(box(.018,3.419,.79,4.845))
    extrude(b,fixed,.140,.164,GLASS,'Fixed upper light and left glazing')
    extrude(b,box(.018,3.42,.775,4.85),.272,.312,DIM,'Shadow behind the open right leaf')
    angle=radians(33)
    def open_leaf(poly,front,back,material,label):
        def locate(x,z,neg_y):
            y=-neg_y
            return (.738+x*cos(angle)-y*sin(angle),.107+x*sin(angle)+y*cos(angle),z)
        b.prism(poly,-back,-front,locate,material,label)
    sash=box(-.709,3.447,0,4.835)
    frame=sash.difference(sash.buffer(-.043))
    open_leaf(frame,-.019,.022,WOOD,'Outward-opening right casement')
    open_leaf(sash.buffer(-.041),.001,.016,GLASS,'Glass in open casement')
    frame=pane.difference(pane.buffer(-.048))
    extrude(b,frame,.074,.145,WOOD,'Arched window surround')
    piece(b,0,.093,4.109,.040,.084,1.362,WOOD,'Lower window meeting rail')
    piece(b,0,.093,4.866,1.51,.084,.052,WOOD,'Window transom')
    piece(b,0,.093,5.097,.032,.083,.418,WOOD,'Upper light divider')
    piece(b,0,-.025,3.366,1.91,.27,.097,SILL,'Upper window sill')
    # Four drainage mouldings cover the intermediate horizontal floor band.
    for z,sz,front in [(3.123,.11,-.062),(3.216,.06,-.111),(3.274,.048,-.149)]:
        piece(b,0,front+.08,z,3.18,.165,sz,RUBBED if z<3.25 else SILL,'Projecting floor cornice')
    # Visible rear door is set back inside the freely open, brick-lined entrance bay.
    tunnel=arch(1.082,.470,2.67,.422,n).difference(lower)
    extrude(b,tunnel,.332,.860,SHADOW,'Brick return of the porch barrel and jambs')
    extrude(b,arch(.95,.36,2.67,.422,n),.845,.895,DIM,'Porch backing and shaded transom')
    piece(b,-.08,.762,1.50,1.64,.070,2.07,DARK,'Recessed inner entrance door')
    for x in (-.45,.25):
        for z in (1.02,1.84):
            frame=box(x-.258,z-.294,x+.258,z+.294);ring=frame.difference(frame.buffer(-.026))
            extrude(b,ring,.707,.734,DARK,'Dark door field moulding')
    for idx in range(3):
        top=(idx+1)*.142
        front=-1.09+.32*idx
        piece(b,0,front+.16,top/2,2.26,.32,top,STONE,'Three street steps')
        piece(b,0,front-.003,top-.087,2.26,.012,.109,RISER,'Vertical stone risers')
        piece(b,0,front+.008,top-.009,2.27,.040,.018,STONE,'Exposed narrow tread edges')
    piece(b,0,.326,.213,2.26,.915,.426,STONE,'Recessed landing')
    for side in (-1,1):
        piece(b,side*1.28,-.41,.249,.29,1.32,.498,STONE,'Entrance side plinths')
        piece(b,side*1.28,-.41,.516,.34,1.36,.071,SILL,'Plinth stone coping')
    # A projecting segmented ring and a recessed disk form the upper roundel.
    zz=5.998;res=12 if lod else 24;disk=Point(0,zz).buffer(.315,quad_segs=res)
    extrude(b,disk,-.092,-.010,SHADOW,'Medallion recessed centre')
    rim=Point(0,zz).buffer(.385,quad_segs=res).difference(disk)
    extrude(b,rim,-.162,-.052,RUBBED,'Raised outer medallion ring')
    for j in range(12):
        ang=[2*pi*(j+.032)/12,2*pi*(j+.50)/12,2*pi*(j+.968)/12]
        pol=Polygon([(r*cos(a),zz+r*sin(a))for r,ls in ((.318,ang),(.165,list(reversed(ang))))for a in ls])
        extrude(b,pol,-.148,-.082,BRICKS[j%4],'Inner radial brickwork')
    # The photograph distinguishes raised outer keys from the finer inner radial joints.
    for j in range(8):
        angles=[2*pi*(j+t)/8 for t in (.13,.43,.73)]
        poly=Polygon([(r*cos(a),zz+r*sin(a)) for r,seq in ((.343,angles),(.247,list(reversed(angles)))) for a in seq])
        extrude(b,poly,-.219,-.113,BRICKS[(j+3)%4],'Projecting outer keys of roundel')
    # The contrast and the two numerals are visible in the high-resolution 2015 image.
    piece(b,1.064,-.131,2.04,.296,.026,.147,GREEN,'Green number 15 plaque')
    strokes=[[(.978,2.080),(.994,2.092),(.994,2.001)],[(.973,2.001),(1.013,2.001)],[(1.123,2.087),(1.059,2.087),(1.055,2.054),(1.100,2.054),(1.119,2.044),(1.119,2.014),(1.105,2.002),(1.053,2.002)]]
    for trace in strokes:extrude(b,LineString(trace).buffer(.0064,cap_style=2,join_style=2),-.150,-.145,WHITE,'Painted 15 numerals')
