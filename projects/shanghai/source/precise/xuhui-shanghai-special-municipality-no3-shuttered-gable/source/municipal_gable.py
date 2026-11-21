"""A cropped brick attic face with four shutter leaves at the former Shanghai municipal offices."""
from pathlib import Path
from random import Random
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union

BRICK='Garden-face orange brick'
COLOUR='Faded red paint on shutters'
SIDE='Recessed red-brown brick'
RETURN_BRICK='Brick masonry on the gable returns'
SHADOW='Dark joint behind shutters'
BED='Buff cement sill'
LIP='Pale stone drip edge'
WOOD='Weathered red-brown gable board'
SOFFIT='Dark timber soffit'
TILE='Muted orange tile'
METAL='Pale vertical gable strip'
PALETTE={name:dict(color=c,roughness=r) for name,c,r in [
    (BRICK,[.94,.91,.89],.95),(SIDE,[.42,.19,.11],.95),(COLOUR,[.375,.151,.144],.84),
    (RETURN_BRICK,[.91,.82,.78],.95),(SHADOW,[.131,.066,.047],.92),(BED,[.654,.505,.322],.92),(LIP,[.76,.665,.476],.85),
    (WOOD,[.328,.158,.125],.90),(SOFFIT,[.242,.157,.114],.90),('Exposed pale verge paint',[.62,.47,.355],.97),(TILE,[.49,.213,.128],.91),(METAL,[.82,.72,.58],.75)]}
HALF=2.56
APEX=4.78
KNEE=2.91
RETURN=.88
LEFT=-1.30
RIGHT=1.30
SILL=1.18
HEAD=2.75
LEAVES=4
PITCH=(RIGHT-LEFT)/LEAVES
SLATS=27
SLAT_STEP=(HEAD-SILL-.156)/SLATS

def texture(path):
    rng=Random(395)
    width,height=960,800
    canvas=Image.new('RGB',(width,height),(199,166,132))
    paint=ImageDraw.Draw(canvas)
    for row,y in enumerate(range(0,height,10)):
        for x in range(-18 if row%2 else 0,width,36):
            level=rng.randrange(-16,16)
            p=[max(0,min(255,v+level))for v in (212,128,74)]
            paint.rounded_rectangle((x+1,y+1,x+34,y+8),radius=1,fill=tuple(p))
            if rng.random()<.7:
                paint.line((x+2,y+2,x+33,y+2),fill=tuple(min(255,v+7)for v in p))
            for _ in range(16):
                u=x+rng.randrange(2,33);v=y+rng.randrange(2,8);delta=rng.randrange(-12,12)
                paint.point((u,v),fill=tuple(max(0,min(255,c+delta))for c in p))
    canvas.save(path)

def face(b,shape,rear,front,mat,name):
    b.prism(shape,rear,front,lambda x,z,d:(x,-d,z),mat,name)

def cube(b,x,y,z,w,d,h,mat,name):
    b.box((x,y,z),(w,d,h),mat,label=name)

def frontbeam(b,a,c,width,back,front,mat,name):
    face(b,LineString([a,c]).buffer(width/2,cap_style='flat'),back,front,mat,name)

def section(b,shape,x0,x1,label,mat):
    # Profile uses horizontal depth and height, extruded along X.
    b.prism(shape,x0,x1,lambda y,z,x:(x,y,z),mat,label)

def add_building(b,lod):
    envelope=Polygon([(-HALF,0),(HALF,0),(HALF,KNEE),(0,APEX),(-HALF,KNEE)])
    opening=box(LEFT-.052,SILL-.038,RIGHT+.052,HEAD+.055)
    recessed=box(-2.24,.104,2.24,.734)
    face(b,envelope.difference(opening).difference(recessed),-.275,0,BRICK,'Running-bond front gable and recessed shutter opening')
    face(b,recessed,-.275,-.044,BRICK,'Inset brick panel below the window sill')
    face(b,box(-2.25,.736,2.25,.77),.001,.022,BRICK,'Raised brick header above inset panel')
    face(b,opening,-.226,-.209,SHADOW,'Shadow behind four louvered leaves')
    for sign in (-1,1):
        x=sign*(HALF-.075)
        cube(b,x,(RETURN+.025)/2,KNEE/2,.15,RETURN-.025,KNEE,RETURN_BRICK,'Brick end return')
    face(b,box(-HALF,.906,HALF,.968),.001,.041,SIDE,'Projecting header course under the sill')
    face(b,box(-HALF,.976,HALF,1.052),.001,.033,BRICK,'Brick course immediately below the sill')
    cube(b,0,-.045,SILL-.039,2.89,.214,.094,BED,'Projecting continuous window sill')
    for s in (-1,1):
        x=s*(RIGHT+.089)
        face(b,box(x-.075,SILL-.008,x+.075,HEAD+.103),-.008,.045,BED,'Buff window jamb')
        face(b,box(x-.061,HEAD+.083,x+.061,HEAD+.174),.010,.066,LIP,'Jamb capital shoulder')
    for name,z,h,wd,depth,mat in [('Window head plain band',HEAD+.083,.127,2.91,.106,BED),
        ('Window head projecting bed',HEAD+.169,.054,2.98,.153,LIP),
        ('Window head crown',HEAD+.214,.052,3.03,.178,BED)]:
        cube(b,0,-depth*.39,z,wd,depth,h,mat,name)
    for leaf in range(LEAVES):
        lo=LEFT+leaf*PITCH+.008;hi=lo+PITCH-.016
        solid=box(lo,SILL,hi,HEAD)
        inner=box(lo+.049,SILL+.083,hi-.049,HEAD-.073)
        face(b,solid.difference(inner),-.142,-.042,COLOUR,f'Shutter {leaf+1} frame')
        for j in range(SLATS):
            z=SILL+.083+j*SLAT_STEP
            # Every shutter blade projects toward the bottom, leaving a real dark reveal.
            profile=[(.057,z),(.108,z+.038),(.113,z+.039),(.112,z+.055),(.054,z+.015)]
            if lod:profile=[profile[i]for i in (0,1,3,4)]
            section(b,Polygon(profile),lo+.044,hi-.044,f'Shutter {leaf+1} blade {j+1}',COLOUR)
    for sign in (-1,1):
        def z(x):return APEX-(APEX-KNEE)*x/HALF
        x=HALF+.135
        board=Polygon([(0,z(0)+.09),(x,z(x)+.09),(x,z(x)-.117),
                       (.94*x,z(.94*x)-.129),(.90*x,z(.90*x)-.091),(.84*x,z(.84*x)-.029),
                       (.79*x,z(.79*x)-.012),(0,z(0)-.092)])
        from shapely.affinity import scale
        if sign<0:board=scale(board,xfact=-1,yfact=1,origin=(0,0))
        face(b,board,-.01,.167,WOOD,'Shaped gable verge board')
        pts=[(0,z(0)),(sign*x,z(x))]
        band=LineString(pts).buffer(.047,cap_style='flat')
        face(b,band,-RETURN,.158,TILE,'Pitched tile verge')
        face(b,LineString([(0,APEX-.021),(sign*x,z(x)-.022)]).buffer(.017,cap_style='flat'),-RETURN,.020,SOFFIT,'Pitched eave soffit')
        frontbeam(b,(0,APEX+.083),(sign*x,z(x)+.083),.035,-.018,.175,BED,'Weathered verge coping')
        # Light abrasions interrupt the reddish paint in the municipal-office photograph.
        sequence=Random(395+(1 if sign>0 else 5))
        for chip in range(26):
            t=sequence.uniform(.13,.97)*x
            height=z(t)+sequence.uniform(-.044,.035)
            length=sequence.uniform(.018,.062)
            if lod and chip%3:continue
            patch=Polygon([(sign*(t-length),height+.012),(sign*(t-.004),height+.007),
                           (sign*(t+.006),height+.021),(sign*(t+length),height+.003),
                           (sign*(t+.033),height-.004),(sign*t,height-.009)])
            if patch.is_valid:face(b,patch,.1671,.1677,'Exposed pale verge paint','Scattered wear on the verge board')
    # A narrow pale vertical element is visible below the ridge. Its function is uncertain.
    face(b,box(-.025,3.38,.025,APEX+.074),.163,.215,METAL,'Pale centre strip below ridge')
    face(b,Polygon([(-.025,3.38),(.025,3.38),(.018,3.29)]),.152,.208,WOOD,'Short tapered lower end')
    b.palette[BRICK]['texture']=str(Path(__file__).with_name('running-bond.png'))
    b.palette[RETURN_BRICK]['texture']=b.palette[BRICK]['texture']
    for part in b.parts:
        if part['material']==RETURN_BRICK:
            part['texcoords']=[[(abs(x)-HALF+y)/(2*HALF),1.-z/(APEX+.20)] for x,y,z in part['vertices']]
        if part['material']==BRICK:
            part['texcoords']=[[(x+HALF)/(2*HALF),1.-z/(APEX+.20)]for x,y,z in part['vertices']]
