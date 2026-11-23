"""The central gable and six open balcony fronts of the house photographed at No. 60."""
import argparse
import math
from pathlib import Path
import sys
import numpy as np
from PIL import Image
from shapely import set_precision
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

SLUG='xuhui-gaoan-60-gabled-balcony-front'
META={'id':SLUG,'name':'高安路60号住宅中央山花与双列阳台','viewer_page':'gaoan-60-gabled-balcony-front.html','heritage_group':'5D003 / XH-J-003-V','address':'上海市徐汇区高安路60号','period':'2015年12月26日和2016年3月12日实照所见状态','scope':'Central gabled frontispiece, narrow upper windows and two rows of open balconies between the first balcony slab and the gable crown.','dimensions':'层距归一为三个展示单位，纵深为照片估计。','photo_author':'高参88；中国の風景','photo_source':'https://4travel.jp/travelogue/11116030','photos_embedded':False,'geometry_license':'MIT, original reconstruction','texture_license':'MIT, generated mineral aggregate and facing brick','copyright':'Original reconstructed geometry and procedural textures under MIT. Reference photographs are not embedded.'}
RENDER='No 60 | warm roughcast';BRICK='No 60 | red facing brick';STONE='No 60 | pale dressed stone';CAP='No 60 | pale cap and moulding';SHADOW='No 60 | reveal plaster';TILE='No 60 | red clay tile';SASH='No 60 | green black window steel';GLASS='No 60 | gray green glass';GLASS2='No 60 | warm reflected glass';IRON='No 60 | light fish scale ironwork';INTERIOR='No 60 | shaded back wall';DARK='No 60 | clay tile underside';GLYPH='No 60 | mineral crest and diamond field'
COLORS={RENDER:(193,177,145),BRICK:(147,78,57),STONE:(185,175,152),CAP:(198,192,171),SHADOW:(157,145,124),TILE:(129,77,53),SASH:(50,55,52),GLASS:(105,124,128),GLASS2:(116,127,123),IRON:(211,205,185),INTERIOR:(126,116,99),DARK:(92,63,49),GLYPH:(177,170,147)}
PALETTE={m:{'color':[(i/255)**2.2 for i in c],'roughness':(.32 if m in (GLASS,GLASS2) else .78)} for m,c in COLORS.items()}
for m,file in ((RENDER,'coarse-render.png'),(BRICK,'brick-bond.png')):PALETTE[m].update(color=[1,1,1],texture=str(HERE/file))

def textures():
    rng=np.random.default_rng(736);n=256
    noise=rng.normal(0,6,(n,n));stones=rng.random((n,n))>.79
    noise+=stones*rng.normal(10,7,(n,n))-np.roll(stones,1,axis=0)*5
    Image.fromarray(np.clip(np.array(COLORS[RENDER])+noise[:,:,None],0,255).astype('uint8')).save(HERE/'coarse-render.png')
    y,x=np.indices((n,n));course=16;brick=48
    # Four bricks across each texture repeat, with a half-brick offset on alternate courses.
    brick=64
    joints=(y%course<1.5)|((x+(y//course%2)*32)%brick<2)
    arr=np.empty((n,n,3))
    for r in range(16):
        shade=rng.uniform(-8,8,4)
        mask=(y//course==r);arr[mask]=np.array(COLORS[BRICK])+shade[((x[mask]+(r%2)*32)//brick)%4,None]
    arr[joints]=[121,101,81]
    Image.fromarray(np.clip(arr+rng.normal(0,3,(n,n,1)),0,255).astype('uint8')).save(HERE/'brick-bond.png')

def flat(b,poly,front,back,mat,label):
    if poly.is_empty:return
    poly=set_precision(poly,1e-6)
    pieces=[poly] if poly.geom_type=='Polygon' else list(poly.geoms)
    for i,p in enumerate(pieces):
        if p.geom_type=='Polygon' and p.area>1.e-7:
            b.prism(p,-back,-front,lambda x,z,d:(x,-d,z),mat,label+(f' part {i+1}' if len(pieces)>1 else ''))
def plan(b,poly,z0,z1,mat,label):b.prism(poly,z0,z1,lambda x,y,d:(x,y,d),mat,label)
def block(b,x0,x1,y0,y1,z0,z1,mat,name):b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)
def rect(b,x0,x1,z0,z1,y0,y1,mat,name):block(b,x0,x1,y0,y1,z0,z1,mat,name)
def rounded_deck(x0,x1,front,back,r,lod):
    # Rounded ends turn through 90 degrees before entering the short side walls.
    pts=[(x0,back),(x0,front+r)]
    for x,t0 in ((x0+r,math.pi),(x1-r,1.5*math.pi)):
        for t in np.linspace(t0,t0+math.pi/2,5 if lod else 11):
            pts.append((x+r*math.cos(t),front+r+r*math.sin(t)))
    pts.extend([(x1,back),(x0,back)])
    return Polygon(np.round(pts,7))
def window(b,x0,x1,z0,z1,y,cols,transoms,label,lod=False):
    width=.042 if cols<5 else .052; c=.068
    bands=[z0,*[z0+(z1-z0)*h for h in transoms],z1]
    edges=np.linspace(x0,x1,cols+1);panes=[]
    for i,(l,r) in enumerate(zip(edges,edges[1:])):
        for j,(base,head) in enumerate(zip(bands,bands[1:])):
            xl=l+(c if i==0 else width/2);xr=r-(c if i==cols-1 else width/2)
            bot=base+(c if j==0 else width/2);top=head-(c if j==len(bands)-2 else width/2)
            pane=box(xl,bot,xr,top);panes.append(pane)
            flat(b,pane,y+.046,y+.068,GLASS2 if (i+2*j)%5==0 else GLASS,f'{label} pane {i+1}-{j+1}')
    flat(b,box(x0,z0,x1,z1).difference(unary_union(panes)),y,y+.068,SASH,label+' steel sash and bars')
def segment(b,a,c,width,depth,mat,name):
    a=np.asarray(a);c=np.asarray(c);u=c-a;L=float(np.linalg.norm(u));u/=L
    y=np.array([0.,1.,0.]);v=np.cross(u,y);v/=np.linalg.norm(v)
    b.box((a+c)/2,(L,depth,width),mat,basis=[u,y,v],label=name)
def local(u,v):return ((312+.22*u-386)/40,(529+39-.22*v)/40)
def drawn(pts):return Polygon([local(u,v)for u,v in pts])
def center(b,lod):
    outline=Polygon([(-1.55,-.52),(1.60,-.52),(1.60,12.25),(-.13,13.87),(-1.55,12.47)])
    opening=[(-.335,.50,-.39,.93),(-.34,.48,2.64,3.98),(-.34,.49,5.72,7.03),(-.38,.49,8.77,10.04)]
    holes=[box(a,c,q,d)for a,q,c,d in opening]
    field=drawn([(193,1158),(192,741),(202,687),(223,648),(257,621),(294,605),(331,601),(367,603),(408,622),(443,650),(462,684),(465,1158)])
    flat(b,outline.difference(unary_union([*holes,field])),.026,.40,RENDER,'Gable | central masonry and four structural openings')
    flat(b,field.intersection(outline).difference(unary_union(holes)),.033,.40,STONE,'Gable | recessed arch face around top window')
    line=LineString([local(u,v) for u,v in [(194,1146),(194,740),(205,687),(225,653),(255,627),(296,610),(332,606),(370,610),(407,625),(442,651),(460,687),(461,1146)]])
    flat(b,line.buffer(.019,cap_style='flat',join_style='round').difference(unary_union(holes)),-.031,.031,CAP,'Gable | narrow arched moulding')
    for i,(x0,x1,base,top) in enumerate(opening):
        sill=base-.10
        rect(b,x0-.080,x1+.080,sill,base,-.086,.19,CAP,f'Gable | window {i+1} projecting sill')
        if i<3:
            window(b,x0,x1,base,top,.12,2,(.22,.50,.79),f'Gable | lower window {i+1}',lod)
        else:
            # Both small metal casements swing out in the two dated photographs.
            width=(x1-x0)/2
            for j,(pivot,sign,ang) in enumerate(((x0,1,67),(x1,-1,57))):
                angle=math.radians(ang);U=np.array([sign*math.cos(angle),-math.sin(angle)])
                normal=np.array([-U[1],U[0]])
                if np.linalg.det([U,normal])<0:normal=-normal
                def leaf(poly,d0,d1,mat,name):
                    b.prism(poly,d0,d1,lambda t,z,d:(pivot+U[0]*t-normal[0]*d,.11+U[1]*t-normal[1]*d,z),mat,name)
                edges=np.linspace(base+.022,top-.02,5);glass=[box(.028,l+.014,width-.028,r-.014)for l,r in zip(edges,edges[1:])]
                leaf(box(0,base,width,top).difference(unary_union(glass)),0,.033,SASH,f'Gable | open casement {j+1} steel fours')
                for k,g in enumerate(glass):leaf(g,.005,.024,GLASS,f'Gable | open casement {j+1} light {k+1}')
            window(b,x0,x1,base,top,.39,2,(.70,), 'Gable | dark inner glazing behind open leaves',lod)
        if i:
            surround=box(x0+.05,sill-.38,x1-.05,sill-.02)
            flat(b,surround.difference(surround.buffer(-.068,join_style='mitre')),-.018,.025,BRICK,f'Gable | window {i+1} brick spandrel frame')
    diamond=drawn([(339,662),(376,694),(344,729),(308,697)])
    flat(b,diamond.difference(diamond.buffer(-.035,join_style='mitre')),-.063,.023,BRICK,'Gable | red diamond under arched eyebrow')
    # Literal outline and recessed cells of the pale cast device. No initials are supplied.
    crest=drawn([(263,376),(310,361),(339,350),(365,351),(390,368),(415,377),(413,454),(338,490),(259,454)])
    flat(b,crest,-.007,.029,STONE,'Gable | chamfered crest carrier')
    cells=[drawn([(276,386),(289,378),(289,437),(304,453),(275,443)]),
           drawn([(308,373),(322,369),(322,447),(313,442),(313,408),(304,400)]),
           drawn([(336,371),(361,367),(376,377),(391,375),(399,383),(399,429),(358,452),(337,437)])]
    face=crest.buffer(-.020,join_style='mitre')
    flat(b,face.difference(unary_union(cells)),-.084,-.008,GLYPH,'Gable | cast relief with narrow and broad recessed cells')
    upper=[local(u,v)for u,v in [(37,369),(323,158),(602,317)]]
    step=[(598,375),(524,375),(524,337),(470,337),(470,297),(413,297),(413,262),(369,262),(369,224),(314,224),(314,261),(269,261),(269,299),(216,299),(216,341),(162,341),(162,379),(113,379),(113,407),(76,407)]
    flat(b,Polygon([*upper,*[local(u,v)for u,v in step]]),.009,.027,BRICK,'Gable | saw stepped red facing below the two rakes')
    for side,(a,c) in enumerate((((-1.58,12.44),(.02,13.75)),((.02,13.75),(1.67,12.47)))):
        for name,d,height,off,mat in [('top coping',.38,.089,0.,CAP),('shadow fascia',.30,.110,-.10,STONE),('small bead',.23,.033,-.23,CAP)]:
            segment(b,(a[0],-.08,a[1]+off),(c[0],-.08,c[1]+off),height,d,mat,f'Gable | rake {side+1} {name}')
        for k in range(7):
            t=(k+.57)/7;x=a[0]*(1-t)+c[0]*t;z=a[1]*(1-t)+c[1]*t-.16
            # A projecting concave corbel, shaded on its side in both close photographs.
            profile=Polygon([(-.257,z+.04),(.030,z+.04),(.030,z-.21),(-.046,z-.21),(-.054,z-.14),(-.078,z-.095),(-.126,z-.055),(-.257,z-.035)])
            b.prism(profile,x-.053,x+.053,lambda y,h,d:(d,y,h),CAP,f'Gable | rake {side+1} modillion {k+1}')

def grille(b,x0,x1,z0,z1,lod,name):
    r=(x1-x0)/12.4;t=.023
    bars=[];N=8 if lod else 15
    # Four offset rows of open arched bars; each crown touches the two bars above it.
    for j in range(5):
        base=z0-.45*r+j*r*.95
        for i in range(-1,9):
            c=x0+(i*2+(.90 if j%2==0 else -.10))*r
            pts=[(c+r*math.cos(a),base+r*math.sin(a))for a in np.linspace(0,math.pi,N)]
            bars.append(LineString(pts).buffer(t/2,cap_style='square',join_style='round',quad_segs=2))
    aperture=box(x0,z0,x1,z1);rim=aperture.difference(aperture.buffer(-.015))
    net=set_precision(unary_union([rim,*bars]).intersection(aperture),1e-5)
    flat(b,net,.031,.077,IRON,name+' four offset scalloped rows')
def balcony(b,x0,x1,z,lod,name):
    r=.24;back=1.48
    base=rounded_deck(x0,x1,-.055,back,r,lod)
    plan(b,base,z-.150,z-.035,STONE,name+' soffit')
    plan(b,rounded_deck(x0-.026,x1+.026,-.086,back,r+.026,lod),z-.035,z+.015,CAP,name+' rounded slab nosing')
    y=0.;left=x0+r;right=x1-r
    z0=z+.015;top=z+.845;middle=(left+right)*.5
    hole=box(middle-.55,z+.167,middle+.55,z+.704)
    cuts=[hole]
    for start,stop in ((left+.15,middle-.72),(middle+.72,right-.14)):
        for c in np.linspace(start,stop,7):
            cuts.append(box(c-.045,z+.162,c+.045,z+.696))
    flat(b,box(left,z0,right,top).difference(unary_union(cuts)),y,y+.155,STONE,name+' pierced parapet and fourteen narrow slots')
    grille(b,*[hole.bounds[i] for i in (0,2,1,3)],lod,name)
    # The broad capping and lower band follow each end's photographed radius.
    for j,(a,bb,front,inner)in enumerate(((top,top+.065,-.039,.182),(z+.049,z+.086,-.020,.160))):
        outer=rounded_deck(x0-.015,x1+.015,front,.57,r+.015,lod)
        innerpoly=rounded_deck(x0+.156,x1-.156,inner,.64,max(.06,r-.156),lod)
        plan(b,outer.difference(innerpoly),a,bb,CAP,name+(' coping' if j==0 else ' foot band'))
    outside=rounded_deck(x0,x1,0,.55,r,lod)
    inside=rounded_deck(x0+.155,x1-.155,.155,.57,r-.155,lod)
    shells=outside.difference(inside)
    for j,cap in enumerate((box(x0-.1,-.1,left,.62),box(right,-.1,x1+.1,.62))):
        plan(b,shells.intersection(cap),z0,top,STONE,name+f' return {j+1}')

def gallery(b,lod):
    for k,(x0,x1) in enumerate(((-6.70,-1.34),(1.30,6.94))):
        side=('left','right')[k];bottom=(.015,.15)[k]
        # Per-side slab elevations retain the independently read front edges.
        for n in range(3):balcony(b,x0,x1,bottom+3*n,lod,f'Balcony | {side} level {n+2}')
        roof=(9.26,9.46)[k];inner=1.48
        for x,edge in ((x0,'outer left'),(x1-.135,'outer right')):
            block(b,x,x+.135,.23,inner+.16,-.12,roof-.15,RENDER,f'Gallery | {side} {edge} return wall')
        # Visible geometry stops at the inner wall of the public façade view.
        for n in range(3):
            z=bottom+n*3
            wall=box(x0+.135,z+.015,x1-.135,z+2.87)
            openings=[]
            if k==0 and n<2:
                openings.append(box(x0+.45,z+.76,x0+1.39,z+1.95))
            if k==0 or n==0:
                openings.append(box(x1-2.14,z+.75,x1-.60,z+1.94))
            flat(b,wall.difference(unary_union(openings)),inner,inner+.15,INTERIOR,f'Gallery | {side} level {n+2} recessed wall')
            for j,h in enumerate(openings):
                l,low,r,top=h.bounds;window(b,l,r,low,top,inner+.055,3,(.70,),f'Gallery | {side} level {n+2} shaded light {j+1}',lod)
        plan(b,box(x0-.14,-.17,x1+.14,inner+.16),roof-.23,roof-.11,STONE,f'Gallery | {side} roof soffit')
        plan(b,box(x0-.15,-.22,x1+.14,inner+.16),roof-.11,roof-.035,CAP,f'Gallery | {side} projecting fascia')
        tilecount=33
        pitch=(x1-x0+.30)/tilecount
        for j in range(tilecount):
            c=x0-.15+(j+.5)*pitch;r=pitch*.515
            angles=np.linspace(0,math.pi,7 if lod else 12)
            profile=Polygon([(c+r*math.cos(t),roof+.04+r*.67*math.sin(t))for t in angles]+[(c+(r-.018)*math.cos(t),roof+.04+(r-.018)*.67*math.sin(t))for t in angles[::-1]])
            # The visible ceramic hood pitches down towards its open barrel ends.
            b.prism(profile,-.26,.32,lambda x,z,d:(x,-d,z-.18*d),TILE,f'Gallery | {side} barrel tile {j+1}')
        block(b,x0-.15,x1+.15,.18,.40,roof+.015,roof+.092,DARK,f'Gallery | {side} shadow behind hollow eave tiles')
        z0=roof+.25;z1=(12.35,12.53)[k]
        upper=box(x0,z0,x1,z1)
        hole=box(-6.58,10.52,-2.28,11.93) if k==0 else box(1.52,10.75,6.07,12.16)
        flat(b,upper.difference(hole),.29,.58,STONE,f'Gallery | {side} fifth storey window surround')
        l,low,r,top=hole.bounds
        window(b,l,r,low,top,.389,6 if k==0 else 8,(.71,),f'Gallery | {side} fifth storey strip',lod)
        rect(b,l-.10,r+.10,low-.08,low,.195,.58,CAP,f'Gallery | {side} projecting strip sill')
        block(b,x0-.14,x1+.14,-.015,.92,z1-.02,z1+.09,CAP,f'Gallery | {side} top eave')
        for s,c in enumerate((x0+.12,x1-.13)):
            block(b,c-.067,c+.067,.05,.37,z0+.22,z1-.07,STONE,f'Gallery | {side} end pier {s+1}')
            block(b,c-.105,c+.105,.005,.40,z1-.12,z1-.045,CAP,f'Gallery | {side} pier head {s+1}')
def build(lod=False):
    b=CrownBuilder(PALETTE);center(b,lod);gallery(b,lod);return b
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--output',type=Path,required=True);a.add_argument('--lod',action='store_true');args=a.parse_args()
    textures();print(build(args.lod).save(args.output,META)['sha256'])
