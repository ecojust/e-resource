"""Jiang twin villas, east villa. One measured south garden bay adjoining the passage."""
from math import sin,cos,pi
from shapely.geometry import box,Polygon
from shapely.ops import unary_union

PALETTE={
 'warm stucco':dict(color=[.69,.637,.522],roughness=.91),
 'pale carved stone':dict(color=[.704,.691,.619],roughness=.87),
 'limestone edge':dict(color=[.608,.605,.554],roughness=.88),
 'shade plaster':dict(color=[.533,.509,.437],roughness=.94),
 'light window frames':dict(color=[.744,.715,.613],roughness=.71),
 'deep grey glazing':dict(color=[.116,.154,.162],metallic=.12,roughness=.28),
 'upper glass':dict(color=[.183,.214,.201],metallic=.11,roughness=.31),
 'dark reveal':dict(color=[.294,.288,.259],roughness=.86),
 'gallery paving':dict(color=[.479,.466,.409],roughness=.90)
}
PIER_X=.49
ROUND_X=3.935
END=4.215
DECK_DEPTH=2.23
LEVELS=[(0.,4.198,4.574),(4.574,7.707,8.083),(8.083,11.403,11.779)]

def block(b,x0,x1,y0,y1,low,high,mat,label):
    assert x1>x0 and y1>y0 and high>low
    b.box(((x0+x1)/2,(y0+y1)/2,(low+high)/2),(x1-x0,y1-y0,high-low),mat,label=label)

def face(b,outline,front,back,material,label):
    b.prism(outline,-back,-front,lambda x,z,t:(x,-t,z),material,label)

def square_profile(b,center,sections,mat,label):
    verts=[];faces=[(3,2,1,0)]
    for z,w,d in sections:
        x,y=center
        verts.extend([(x-w/2,y-d/2,z),(x+w/2,y-d/2,z),(x+w/2,y+d/2,z),(x-w/2,y+d/2,z)])
        if len(verts)>4:
            n=len(verts)-8
            faces.extend((n+j,n+(j+1)%4,n+(j+1)%4+4,n+j+4)for j in range(4))
    faces.append(tuple(range(len(verts)-4,len(verts))));b.add(verts,faces,mat,label)

def tuscan(b,bottom,top,i,lod):
    x,y=ROUND_X,.29
    n=12 if lod else 28;r=.189 if i else .211
    block(b,x-.257,x+.257,.032,.548,bottom,bottom+.103,'pale carved stone',f'{i} square column foot')
    rings=[(bottom+.103,r*1.18),(bottom+.137,r*1.25),(bottom+.174,r*1.21),
           (bottom+.213,r*1.08),(bottom+.239,r*1.115),(bottom+.275,r)]
    b.lathe((x,y),rings,'limestone edge',n,f'{i} round plinth bands')
    b.lathe((x,y),[(bottom+.275,r),(bottom+.73,r*1.016),(top-.280,r*.885)],
            'pale carved stone',n,f'{i} plain tapered column')
    b.lathe((x,y),[(top-.280,r*.885),(top-.252,r*1.01),(top-.228,r*.94),
            (top-.189,r*.96),(top-.150,r*1.10),(top-.112,r*1.26),(top-.083,r*1.29)],
            'limestone edge',n,f'{i} moulded capital')
    block(b,x-.263,x+.263,.022,.558,top-.083,top,'pale carved stone',f'{i} Tuscan abacus')

def baluster_rail(b,left,right,z,height,lod,tag,count):
    front=.105; rear=.365;cy=(front+rear)/2
    for lo,hi,d in [(0.,.088,.267),(.088,.121,.234)]:
        block(b,left,right,cy-d/2,cy+d/2,z+lo,z+hi,'limestone edge',tag+' bottom mould')
    step=(right-left)/count;rad=.071 if height>.95 else .061;n=7 if lod else 13
    for k in range(count):
        x=left+step*(k+.5)
        # The photograph shows broad-shouldered turned stone bottles with small square pads.
        block(b,x-.076,x+.076,cy-.076,cy+.076,z+.121,z+.162,'pale carved stone',tag+' lower pads')
        way=[(.162,.074),(.187,.072),(.224,.046),(.260,.045),(.312,.064),
             (.390,.082),(.483,.081),(.572,.058),(.66,.043),(.72,.049),(.755,.068),(.789,.068)]
        profile=[(z+.162+(f-.162)*(height-.16-.162)/(.789-.162),r*rad/.071)for f,r in way]
        b.lathe((x,cy),profile,'pale carved stone',n,tag+' turned stone bottles')
    for low,high,d in [(height-.160,height-.132,.241),(height-.132,height-.058,.273),(height-.058,height,.301)]:
        block(b,left,right,cy-d/2,cy+d/2,z+low,z+high,'pale carved stone',tag+' handrail')

def rear_windows(b,i,base,top,lod):
    # Two tall sash windows are seen between the pier and first column. The rear plane is recessed.
    pane_face=2.25;wa=Polygon([(0.,base),(END,base),(END,top),(0.,top)])
    sill=base+(.51 if i==0 else .32);head=top-(.79 if i==0 else .65)
    apertures=[(1.11,.74),(3.32,.82)]
    openings=[box(c-w/2,sill,c+w/2,head)for c,w in apertures]
    face(b,wa.difference(unary_union(openings)),DECK_DEPTH,2.49,'warm stucco',f'{i} cream rear wall')
    for j,((c,w),rect) in enumerate(zip(apertures,openings)):
        tag=f'{i} rear sash {j}'
        face(b,rect.buffer(.049,join_style=2).difference(rect),2.188,2.239,'pale carved stone',tag+' architrave')
        face(b,rect.difference(rect.buffer(-.056,join_style=2)),2.246,2.313,'light window frames',tag+' jambs')
        face(b,rect.buffer(-.052,join_style=2),2.337,2.354,'upper glass' if i==2 else 'deep grey glazing',tag+' panes')
        for z,t in [(head-.41,.043),(sill+.49*(head-.39-sill),.024)]:
            block(b,c-w/2+.04,c+w/2-.04,pane_face+.041,pane_face+.084,z-t/2,z+t/2,'light window frames',tag+' transoms')
        block(b,c-.018,c+.018,pane_face+.043,pane_face+.081,sill+.051,head-.048,'light window frames',tag+' sash mullion')
        if not lod:
            for offset in (-.22,.22):
                block(b,c+w*offset-.012,c+w*offset+.012,2.30,2.325,head-.382,head-.056,'light window frames',tag+' upper lights')
        block(b,c-w/2-.064,c+w/2+.064,2.153,2.293,sill-.066,sill,'limestone edge',tag+' projecting sill')

def pilaster(b,lod):
    # An isolated foot below, then a tall upper strip crossing the second and third galleries.
    cx,cy=PIER_X,.32
    square_profile(b,(cx,cy),[(0.,.90,.79),(.135,.90,.79),(.174,.83,.735),(.225,.79,.72),
                   (3.91,.79,.72),(3.96,.835,.755),(4.05,.88,.81),(4.198,.91,.84)],'pale carved stone','ground pier with squared capital')
    square_profile(b,(cx,cy),[(4.574,.94,.82),(4.67,.94,.82),(4.74,.827,.75),
                   (10.96,.827,.75),(11.02,.85,.76),(11.07,.93,.81),(11.15,.89,.79),
                   (11.24,.98,.84),(11.32,1.02,.89),(11.403,1.04,.91)],'pale carved stone','two-storey garden pier')
    # Shallow floral relief seen on the upper front. The visible sprays and pendants are simplified.
    for side in (-1,1):
        trail=[(cx+side*u,-.076,z) for u,z in [(0.10,10.98),(.27,10.86),(.25,10.73),(.12,10.64),(.065,10.52)]]
        b.tube(trail,.018,'limestone edge',sides=5 if lod else 9,label='pier carved sprays')
        for j,(u,z)in enumerate([(.062,10.62),(.058,10.45),(.043,10.28)]):
            x=cx+side*u
            leaf=Polygon([(x-.024,z+.038),(x+.027,z+.044),(x+.046,z+.007),(x+.002,z-.065),(x-.033,z-.007)])
            face(b,leaf,-.104,-.063,'limestone edge','pier relief drops')
    block(b,cx-.193,cx+.193,-.084,-.048,10.94,11.012,'limestone edge','pier front head band')

def add_loggia(b,lod=False):
    # Only the garden-facing west bay of the east house reaches this local coordinate frame.
    block(b,0,END,-.035,2.49,-.035,.043,'gallery paving','garden gallery threshold')
    pilaster(b,lod)
    for i,(base,top,deck) in enumerate(LEVELS):
        rear_windows(b,i,max(.043,base),top,lod)
        tuscan(b,max(.043,base),top,i,lod)
        baluster_rail(b,.88,ROUND_X-.20,base+.044,[1.209,.833,.895][i],lod,f'{i} garden rail',14)
        block(b,0,END,.125,2.49,top,deck,'shade plaster',f'{i} gallery soffit')
        courses=[(top,top+.085,-.035),(top+.085,top+.127,-.077),(top+.127,top+.243,-.045),
                 (top+.243,deck-.054,-.099),(deck-.054,deck,-.121)]
        for k,(z0,z1,y) in enumerate(courses):
            block(b,0,END,y,.125,z0,z1,'limestone edge' if k in(1,3) else'pale carved stone',f'{i} fascia bands')
    # The roof behind the garden parapet and the central pediment are outside this segment.
    baluster_rail(b,.90,END,11.779,.77,lod,'roof garden parapet',15)
    square_profile(b,(PIER_X,.265),[(11.779,.96,.87),(11.892,.96,.87),(11.959,.81,.76),(12.916,.81,.76),
        (13.002,.87,.81),(13.084,.98,.89),(13.143,.99,.90),(13.22,.93,.85)],'pale carved stone','west roof end post')
    for k in range(7):
        x=.26+.56*k
        block(b,x-.061,x+.061,-.173,.18,11.507,11.653,'limestone edge','cornice modillions')
    if not lod:
        for k in range(29):
            x=.095+.139*k
            block(b,x-.030,x+.030,-.101,.033,11.665,11.718,'pale carved stone','upper dentil band')
