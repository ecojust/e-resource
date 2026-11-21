"""Reconstruct the broad gable shown on plate 29 of Shanghai of To-day (1930)."""
from math import pi,cos,sin,sqrt
from pathlib import Path
from random import Random
from PIL import Image,ImageDraw
from shapely.geometry import Polygon,box
from shapely.ops import unary_union

WALL='Light rendered masonry'
BAND='Raised masonry band'
CAP='Dark gable coping'
KEY='Projecting keystone'
FRAME='Dark window framing'
GLASS='Neutral glazing'
TILE='Grayscale roof covering'
SILL='Stone sill'
PALETTE={m:dict(color=c,roughness=r)for m,c,r in [
    (WALL,[.76,.75,.71],.92),(BAND,[.855,.842,.80],.93),(CAP,[.275,.267,.255],.83),
    (KEY,[.91,.90,.86],.89),(FRAME,[.155,.150,.142],.65),(GLASS,[.26,.27,.26],.34),
    (TILE,[.94,.94,.94],.93),(SILL,[.51,.495,.46],.91)]}
SCALE=.020
WINDOWS=((135,193),(244,299),(348,404))
CENTRE=259
def xval(u):return (u-CENTRE)*SCALE
def zval(v):return (505-v)*SCALE
def xyz(u,v,front):return xval(u),-front,zval(v)
def prism(b,shape,back,front,mat,label):
    b.prism(shape,back,front,lambda x,z,d:(x,-d,z),mat,label)
def shape(points):return Polygon([(xval(x),zval(z))for x,z in points])
def rect(b,l,t,r,base,back,front,mat,label):
    prism(b,box(xval(l),zval(base),xval(r),zval(t)),back,front,mat,label)
def arc(cx,spring,rx,ry,steps):
    return [(cx+rx*cos(pi*i/steps),spring-ry*sin(pi*i/steps))for i in range(steps+1)]
def ribbon(cx,spring,outer_x,outer_y,inner_x,inner_y,steps):
    return shape(arc(cx,spring,outer_x,outer_y,steps)+arc(cx,spring,inner_x,inner_y,steps)[::-1])
def texture(out):
    rng=Random(415);im=Image.new('RGB',(384,250),(107,104,99));draw=ImageDraw.Draw(im)
    for row,y in enumerate(range(-4,250,12)):
        for x in range(-20 if row%2 else -6,384,30):
            tone=rng.randrange(-7,8);draw.rectangle((x+1,y+1,x+29,y+11),fill=tuple(k+tone for k in (110,108,103)))
            draw.line((x+1,y+10,x+29,y+10),fill=tuple(k+tone for k in (96,94,89)))
            for _ in range(13):
                v=rng.randrange(-7,9);draw.point((x+rng.randrange(2,28),y+rng.randrange(2,10)),fill=tuple(k+v for k in (108,106,101)))
    im.save(out)
def window_shape(index,l,r,steps):
    top=349 if index!=1 else 317
    if index==1:
        return shape([(r,492)]+arc((l+r)/2,top,(r-l)/2,19,steps)+[(l,492)])
    return shape([(l,top),(r,top),(r,492),(l,492)])
def crest(b,lod):
    n=16 if lod else 42
    outer=arc(CENTRE,286,189,168,n)
    panel=shape([(448,294)]+outer+[(70,294)])
    prism(b,panel,-.44,.004,WALL,'Semicircular gable wall')
    prism(b,ribbon(CENTRE,286,195,175,189,167,n),-.54,.104,CAP,'Outer projecting curved coping')
    prism(b,ribbon(CENTRE,286,189.4,168.5,184.7,163,n),-.38,.078,BAND,'Inner concentric moulding')
    for i in range(14 if lod else 30):
        count=14 if lod else 30
        a0=pi*(i+.09)/count;a1=pi*(i+.76)/count
        # Small shadows are visible directly under the curved coping.
        pts=[(CENTRE+rx*cos(a),286-ry*sin(a))for rx,ry,a in [
            (185,164,a0),(185,164,a1),(184.2,161.7,a1),(184.2,161.7,a0)]]
        prism(b,shape(pts),-.018,.041,BAND,'Small projections below moulding')
    # Profile of the raised apex ornament. The print shows neither its true
    # colour nor the section around its unseen rear face.
    for i,(v0,v1,radius0,radius1,mat) in enumerate([
            (140,128,5.3,12.8,BAND),(128,119,12.8,8.4,CAP),(119,112,8.0,11.4,BAND),
            (112,104,8.6,7.3,CAP),(104,100,12.8,10.3,BAND),(100,93,8.4,6.4,CAP),
            (93,89,9.2,6.9,BAND),(89,60,5.9,2.3,CAP)]):
        around=8 if lod else 16
        def ring(radius,v):
            return [(xval(CENTRE)+radius*SCALE*cos(j*2*pi/around),-.013+radius*SCALE*sin(j*2*pi/around),zval(v)) for j in range(around)]
        a,c=ring(radius0,v0),ring(radius1,v1)
        tris=[]
        for j in range(around):k=(j+1)%around;tris.extend([(j,k,k+around),(j,k+around,j+around)])
        for j in range(1,around-1):tris.extend([(0,j+1,j),(around,around+j,around+j+1)])
        b.add(a+c,tris,mat,f'Central finial tier {i+1}')
def add_building(b,lod):
    n=14 if lod else 34
    apertures=[window_shape(i,l,r,n)for i,(l,r)in enumerate(WINDOWS)]
    face=shape([(59,286),(461,286),(461,503),(59,503)]).difference(unary_union(apertures))
    prism(b,face,-.42,0,WALL,'Upper front with three recessed windows')
    crest(b,lod)
    for l,r in [(48,121),(403,472)]:
        rect(b,l,282,r,291,-.50,.135,CAP,'Projecting lower end of gable coping')
    # Horizontal masonry returns flank the recessed sash on the three bays.
    for v in [320,356,390,424,458,490]:
        for l,r in [(63,133),(195,241),(301,346),(407,459)]:
            rect(b,l,v,r,v+2.5,-.003,.05,BAND,'Raised string courses alongside the windows')
    for i,((l,r),opening) in enumerate(zip(WINDOWS,apertures)):
        prism(b,opening,-.23,-.158,GLASS,f'Recessed glazing {i+1}')
        if i==1:
            prism(b,ribbon((l+r)/2,317,(r-l)/2,19,(r-l)/2-1.7,17.3,n),
                  -.149,-.079,FRAME,'Arched dark outer window frame')
        for u in (l+.5,r-.5):
            rect(b,u-.57,318 if i==1 else 351,u+.57,491,-.153,-.083,FRAME,f'Recessed outer jamb {i+1}')
        for f in (.035,.34,.67,.965):
            u=l+(r-l)*f;top=350.1 if i!=1 else 317-19*sqrt(max(0,1-(2*f-1)**2))+.10
            rect(b,u-.9,top,u+.9,491,-.159,-.093,FRAME,f'Upright of window {i+1}')
        levels=(349.7,397,449,490)if i!=1 else(351.5,406,450,490)
        for v in levels:rect(b,l+.7,v-.9,r-.7,v+.9,-.157,-.085,FRAME,f'Cross rail of window {i+1}')
        rect(b,l-3.0,492,r+3.0,496.2,-.17,.092,SILL,f'Sill below window {i+1}')
        if i==1:
            prism(b,ribbon((l+r)/2,317,34.0,26.0,27.8,19.0,n),-.09,.094,BAND,'Segmental head around central window')
            xs=[(233,291),(241,298),(258,291),(271,288),(283,290),(300,298),(311,291),(304,284),(293,281),(281,278),(272,277),(259,279),(248,284),(237,285)]
            prism(b,shape(xs),-.045,.162,BAND,'Raised segmental eyebrow and projecting ends')
            upper=[(233,289.5),(240,295),(255,288),(271,284.5),(288,286),(303,294),(310,289),
                   (304,287.8),(289,281.8),(271,279.4),(255,282.8),(240,289.8),(234,286.5)]
            prism(b,shape(upper),.160,.178,CAP,'Folded upper edge of eyebrow')
            k=shape([(264,277),(278,277),(275,289),(267,289)])
            prism(b,k,.08,.185,KEY,'Small central wedge above eyebrow')
        else:
            rect(b,l-6,339,r+6,346,-.025,.139,BAND,f'Projecting square hood {i+1}')
            rect(b,l-6.5,337.6,r+6.5,340.6,-.028,.151,CAP,f'Shadowed hood edge {i+1}')
            mid=(l+r)/2
            prism(b,shape([(mid-8.8,313),(mid+8.8,313),(mid+5.5,340),(mid-4.2,340)]),
                  -.01,.165,KEY,f'Keystone over side window {i+1}')
    for i,(u,v) in enumerate(((216,242),(271,232),(325,248),(265,180),(268,146))):
        rect(b,u-6.5,v,u+6.5,v+8.8,-.016,.065,BAND,'Isolated masonry accent '+str(i+1))
        rect(b,u-9.3,v-1.9,u+9.3,v+1.5,-.02,.089,CAP,'Cap on masonry accent '+str(i+1))
    # Only two short roof shoulders visible beyond the raised front are included.
    for l,r in [(10,89),(429,510)]:
        def roof_profile(t):
            return -.04+1.33*t,zval(284)+.66*t
        rows=4 if lod else 7
        for j in range(rows):
            y0,z0=roof_profile(j/rows);y1,z1=roof_profile((j+1)/rows)
            b.prism(Polygon([(y0,z0-.055),(y1,z1-.038),(y1,z1+.012),(y0,z0+.024)]),
                    xval(l),xval(r),lambda y,z,x:(x,y,z),TILE,'Short adjoining pitched roof shoulder')
        rect(b,l,283.5,r,289,-.02,.046,CAP,'Adjoining eaves edge')
    b.palette[TILE]['texture']=str(Path(__file__).with_name('roof-tone.png'))
    for p in b.parts:
        if p['material']==TILE:p['texcoords']=[[(x+5.4)/11,.98-y/1.66] for x,y,z in p['vertices']]
