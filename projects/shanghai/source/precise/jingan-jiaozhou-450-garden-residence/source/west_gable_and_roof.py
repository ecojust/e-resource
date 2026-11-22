"""West brick gable, its photographed shutters, chimney shoulders and tiled roof."""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
import garden_arcade as arcade

DATA=json.loads((Path(__file__).resolve().parents[1]/'measurements/west-fabric-sections.json').read_text())
OPENINGS=DATA['west_openings']
ROOF=DATA['roof']
FRAME='West gable | weathered dark shutter frames'
LEAF='West gable | angled timber louvres'
SHADOW='West gable | dark recessed opening'
BRICK_HEAD='West gable | brick sill and flush lintel'
STONE='West gable | weathered cap'
ROOF_TONES=['Main roof | grey tile '+str(n) for n in range(1,5)]
EDGE='Main roof | eaves board and exposed soffit'
PALETTE={k:{'color':arcade.linear(rgb),'roughness':r} for k,rgb,r in [(FRAME,(63,53,48),.85),(LEAF,(76,66,61),.85),(SHADOW,(34,32,32),.96),(BRICK_HEAD,(132,90,70),.94),(STONE,(125,113,100),.93),(EDGE,(76,58,48),.89),*[(k,c,.91) for k,c in zip(ROOF_TONES,[(99,99,107),(112,111,118),(107,106,114),(103,103,110)])]]}

def block(b,x0,x1,y0,y1,z0,z1,material,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)

def west(b,polygon,x0,x1,material,label):
    b.prism(polygon,x0,x1,lambda y,z,x:(x,y,z),material,label)

def roof_z(y):return 10.437+(y-4.55)*ROOF['sloping_roof_tan']

def screens(b):
    for o in OPENINGS:
        l,z,r,t=o['yz'];n=o['louvre_rows'];leaves=o['leaves'];name=o['label'];w=.047
        block(b,.095,.156,l,r,z,z+w,FRAME,name+' | sill-frame')
        block(b,.095,.156,l,r,t-w,t,FRAME,name+' | head-frame')
        for y in (l+w/2,r-w/2):
            block(b,.095,.156,y-w/2,y+w/2,z+w,t-w,FRAME,name+' | frame sides')
        block(b,.235,.254,l,r,z,t,SHADOW,name+' | deep shadow')
        if leaves==2:block(b,.084,.148,(r+l-w)/2,(r+l+w)/2,z+w,t-w,FRAME,name+' | central meeting stile')
        for j in range(leaves):
            a=l+w+(r-l-2*w)*j/leaves+(w/2 if j else 0)
            c=l+w+(r-l-2*w)*(j+1)/leaves-(w/2 if j+1<leaves else 0)
            pitch=(t-z-2*w)/n
            for i in range(n):
                h=z+w+(i+.48)*pitch
                b.box((.145,(a+c)/2,h),(.039,c-a,pitch*.94),LEAF,
                      basis=[(.82,0.,-.572),(0.,1.,0.),(.572,0.,.82)],label=name+' | inclined slats')
        block(b,-.105,.19,l-.08,r+.08,z-.085,z,BRICK_HEAD,name+' | projecting brick sill')
        # Flat header bricks radiate slightly at the outer joints.
        for i in range(max(9,int((r-l)/.10))):
            nn=max(9,int((r-l)/.10));a=l+(r-l)*i/nn;c=l+(r-l)*(i+1)/nn
            skew=((i+.5)/nn-.5)*.074
            west(b,Polygon([(a+.003,t),(c-.003,t),(c+skew-.003,t+.177),(a+skew+.003,t+.177)]),-.016,-.001,BRICK_HEAD,name+' | header bricks')

def small_arch(b,lod):
    # Only the upper half is recorded above the garden boundary wall. The
    # hidden opening below follows a simple vertical extrusion.
    c=2.02;radius=1.30;spring=2.82;rise=1.035;nn=29
    def curve(theta,band=0):
        return (c+(radius+band)*np.cos(theta),spring+(rise+band)*np.sin(theta))
    ts=np.linspace(0,np.pi,nn+1)
    sector=Polygon([(c-radius,-.05),(c+radius,-.05),*[curve(t)for t in ts]])
    band=Polygon([*[curve(t,.27)for t in ts],*[curve(t)for t in ts[::-1]]])
    west(b,box(0.,0.,3.72,4.735).difference(unary_union([sector,band])),.002,.42,arcade.FACE,'West return | brick arch spandrel')
    west(b,band,.033,.42,arcade.JOINT,'West return | mortar behind radial bricks')
    for i,(a,t) in enumerate(zip(ts[:-1],ts[1:])):
        zz=np.linspace(a+.002,t-.002,2 if lod else 3)
        section=Polygon([*[curve(v,.27+(.05 if i==nn//2 else 0))for v in zz],*[curve(v)for v in zz[::-1]]])
        west(b,section,-.008-(.012 if i==nn//2 else 0),.045,arcade.RINGS[i%len(arcade.RINGS)],'West return | fanned arch bricks')

def gable(b):
    c=DATA['roof']['independent_street_gable']['local_xyz_m']
    upper=[(3.72,10.87),(4.06,10.81),(5.10,12.13),(c[1],c[2]),(18.31,12.59),(19.18,12.74),(19.18,0),(3.72,0)]
    body=Polygon(upper)
    cuts=[box(l,z,r,t)for l,z,r,t in (o['yz']for o in OPENINGS)]
    west(b,body.difference(unary_union(cuts)),0.,.44,arcade.FACE,'West gable | brick wall with five openings')
    for i,(a,c) in enumerate(zip(upper[:5],upper[1:6])):
        band=Polygon([a,c,(c[0],c[1]+.10),(a[0],a[1]+.10)])
        west(b,band,-.05,.46,STONE,'West gable | sloping coping')
    screens(b)
    block(b,.40,16.94,18.89,19.17,0,9.95,arcade.FACE,'North wall | upper roof support')
    block(b,16.66,16.94,3.72,19.17,0,9.53,arcade.FACE,'East wall | clipped outer shell')
    block(b,10.7,16.67,3.72,4.19,0,4.7,arcade.FACE,'Garden rear wall | eastern brick continuation')
    block(b,.43,16.67,3.72,4.04,4.7,9.5,arcade.FACE,'Garden | shaded upper wall above terrace')
    # The eastern chimney is photographed against the sky. Return the thin
    # gable under the roof, without copying the west openings onto this end.
    ry=ROOF['ridge_y'];rz=ROOF['ridge_z']
    west(b,Polygon([(3.72,9.51),(ry,rz-.07),(19.17,10.1),(19.17,9.51)]),16.61,16.93,arcade.FACE,'East gable | north and south roof ends')
    small_arch(b,False)

def chimney(b,xbase,front,back,zbase,top,label,west_face):
    x0,x1=xbase-.23,xbase+.44
    block(b,x0,x1,front,back,zbase,top-.24,arcade.FACE,label+' | rectangular stack')
    for d,h,mat,s in [(.06,.105,BRICK_HEAD,'lower ledge'),(.11,.165,arcade.FACE,'upper brick cap'),(.035,.065,STONE,'capstone')]:
        t=top if s=='capstone' else top-.07 if s=='upper brick cap' else top-.30
        block(b,x0-d,x1+d,front-d,back+d,t-h,t,mat,label+' | '+s)
    for yy in np.linspace(front+.16,back-.16,4):
        block(b,x0-.055,x0+.006,yy-.085,yy+.085,top-2.46,top-.23,arcade.FACE,label+' | recessed-panel dividers')
    if west_face:
        # Shoulder rises from the exposed stack on the street wall.
        section=Polygon([(x0-.38,2.85),(x0-.38,4.28),(x0-.16,4.66),(x0,4.72),(x0,2.85)])
        b.prism(section,-back,-front,lambda x,z,d:(x,-d,z),arcade.FACE,label+' | splayed foot')

def tile_row(b,x0,x1,y0,y1,height,index,lod,label):
    # One continuous, watertight row. The rolled tile profile is sampled at
    # the photographed rhythm. Its lip overlaps the equally spaced next row.
    if x1<=x0:return
    steps=2 if lod else 4; period=.270
    marks=np.arange(np.floor(x0/period*steps)+1,np.ceil(x1/period*steps))*period/steps
    xx=np.r_[x0,marks[(marks>x0+1.e-5)&(marks<x1-1.e-5)],x1]
    v=[];f=[]
    for x in xx:
        relief=.058*(1+np.cos(2*np.pi*x/period))*.5
        v.extend([(x,y0,height(y0)-.084),(x,y1,height(y1)-.084),(x,y1,height(y1)-.032+relief),(x,y0,height(y0)+.032+relief)])
    for i in range(len(xx)-1):
        for j in range(4):
            q=(j+1)%4;k=i*4;f.append((k+j,k+q,k+4+q,k+4+j))
    k=(len(xx)-1)*4;f.extend([(3,2,1,0),(k,k+1,k+2,k+3)])
    b.add(v,f,ROOF_TONES[index%4],label)

def roof(b,lod):
    ry=ROOF['ridge_y'];z=ROOF['ridge_z'];yfront=3.22;yback=19.32
    # Fit exposure of each photographed course in plan. Front courses near
    # the eave are a little shorter in the calibrated oblique photograph.
    ys=[yfront]
    while ys[-1]<ry-.01:ys.append(min(ry,ys[-1]+.385+.008*(ys[-1]-4.8)))
    for i,(a,c) in enumerate(zip(ys,ys[1:])):
        splits=sorted({a,c,*[v for v in [4.55,9.17] if a<v<c]})
        for aa,cc in zip(splits,splits[1:]):
            sections=[(.14,6.792),(15.081,16.83)] if 4.55<=(aa+cc)/2<=9.17 else [(.14,16.83)]
            for x0,x1 in sections:
                tile_row(b,x0,x1,aa,cc,roof_z,i,lod,'South roof | overlapping pantile courses')
    fall=lambda y:z-(y-ry)*(z-10.07)/(yback-ry)
    ys=np.linspace(ry,yback,18)
    for i,(a,c) in enumerate(zip(ys,ys[1:])):tile_row(b,.14,16.83,a,c,fall,i,lod,'North roof | returning tile field')
    block(b,.13,16.88,ry-.11,ry+.11,z-.007,z+.143,ROOF_TONES[1],'Main roof | ridge cap')
    block(b,.11,16.88,yfront-.07,yfront+.12,roof_z(yfront)-.19,roof_z(yfront)+.012,EDGE,'Garden eave | shadow board')
    block(b,.11,16.87,yfront+.05,3.74,roof_z(yfront)-.18,roof_z(yfront)-.105,EDGE,'Garden eave | returned soffit')
    # The ridge of the west brick gable is offset from the inner wood roof
    # in the oblique street solution. Close its under-roof return at the end.
    c=ROOF['independent_street_gable']['local_xyz_m']
    section=Polygon([(3.72,roof_z(3.72)-.12),(ry,z-.16),(19.16,10.01),(19.16,12.73),(18.31,12.58),(c[1],c[2]-.015),(5.1,12.12),(4.06,10.8),(3.72,10.86)])
    for poly in ([section] if section.is_valid else [section.buffer(0)]):
        west(b,poly,.435,.54,arcade.FACE,'West gable | inner parapet return')

def add_fabric(b,lod=False):
    b.palette.update(PALETTE);start=len(b.parts)
    gable(b)
    chimney(b,0.,6.12,9.05,2.86,19.04,'West chimney',True)
    chimney(b,16.60,3.42,5.90,10.01,16.04,'East chimney',False)
    roof(b,lod)
    for p in b.parts[start:]:
        if p['material']==arcade.FACE:arcade.material_uv(p)
