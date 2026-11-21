"""Upper timber-framed frontage as seen in photographs of the former consulate in 2000 and 2004."""
from math import cos, hypot, pi, sin

COLOURS = {
    'cream roughcast': (216,208,186), 'coved soffit': (202,196,175),
    'old dark framing': (75,54,45), 'warm timber edge': (98,68,53),
    'window wood': (100,65,51), 'window bead': (126,90,67),
    'smoky glazing': (67,78,78), 'green grey glazing': (73,83,78),
    'painted stone sill': (131,104,82), 'red verge tiles': (151,93,68),
    'light red verge tiles': (168,106,75), 'grey verge sheet': (110,108,99)
}

def linear(value):
    c=value/255
    return c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4

PALETTE={k:{'color':[linear(v) for v in col],'roughness': .38 if 'glazing' in k else .91}
         for k,col in COLOURS.items()}
HALF=2.06
X_WINDOWS=(-1.03,1.03)
W=.92
SILL=.275
HEAD=1.77
CORNICE=2.29
TOP=4.22

def prism(b,outline,front,back,mat,label):
    count=len(outline)
    verts=[(x,y,z) for y in (front,back) for x,z in outline]
    faces=[tuple(range(count)),tuple(reversed(range(count,2*count)))]
    faces.extend((i,i+count,(i+1)%count+count,(i+1)%count) for i in range(count))
    b.add(verts,faces,mat,label)

def section(b,start,end,width,front,back,mat,label):
    x,z=start
    dx,dz=end[0]-x,end[1]-z
    length=hypot(dx,dz)
    ox,oz=-dz*width/(2*length),dx*width/(2*length)
    prism(b,[(x-ox,z-oz),(x+dx-ox,z+dz-oz),(x+dx+ox,z+dz+oz),(x+ox,z+oz)],front,back,mat,label)

def profile(b,start,end,cross,mat,label):
    vertices=[(x,y,z) for x in (start,end) for y,z in cross]
    n=len(cross)
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    b.add(vertices,faces,mat,label)

def box(b,label,mat,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)*.5,(y0+y1)*.5,(z0+z1)*.5),(x1-x0,y1-y0,z1-z0),mat,label=label)

def window(b,cx,idx,lod):
    x0,x1=cx-W/2,cx+W/2
    for ix in (0,1):
        a=(x0,x1-.064)[ix]
        box(b,f'Window {idx} outer jamb {ix}', 'window wood',a,a+.064,-.065,.116,SILL,HEAD)
    for iz,z in enumerate((SILL,HEAD-.066)):
        box(b,f'Window {idx} outer rail {iz}','window wood',x0,x1,-.066,.118,z,z+.066)
    xa,xb=x0+.064,x1-.064
    za,zb=SILL+.066,HEAD-.066
    for col in range(4):
        for row in range(6):
            a=xa+(xb-xa)*col/4
            e=xa+(xb-xa)*(col+1)/4
            z=za+(zb-za)*row/6
            h=za+(zb-za)*(row+1)/6
            label=f'Window {idx} light {col+1}-{row+1}'
            box(b,label,'smoky glazing' if (col+row+idx)%4 else 'green grey glazing',a,e,.120,.136,z,h)
            if not lod:
                for j,u in enumerate((a+.007,e-.013)):
                    box(b,label+' bead '+str(j),'window bead',u,u+.006,.071,.089,z+.008,h-.008)
    for j in (1,2,3):
        x=xa+(xb-xa)*j/4
        width=.046 if j==2 else .023
        box(b,f'Window {idx} upright {j}','window wood',x-width/2,x+width/2,.007,.120,za,zb)
    for j in range(1,6):
        z=za+(zb-za)*j/6
        box(b,f'Window {idx} transom {j}','window wood',xa,xb,.020,.116,z-.012,z+.012)
    for j,side in enumerate((x0-.052,x1)):
        box(b,f'Window {idx} outer timber surround {j}','old dark framing',side,side+.052,-.081,.0,SILL-.034,HEAD+.023)
    profile(b,x0-.094,x1+.094,[(-.103,SILL-.048),(-.158,SILL-.032),(-.148,SILL-.010),(-.103,SILL+.008),(.038,SILL+.008),(.038,SILL-.048)], 'painted stone sill',f'Window {idx} projecting sill')

def add_building(b,lod=False):
    gaps=[(-HALF,X_WINDOWS[0]-W/2),(X_WINDOWS[0]+W/2,X_WINDOWS[1]-W/2),(X_WINDOWS[1]+W/2,HALF)]
    for j,(a,e) in enumerate(gaps):
        box(b,'Rendered wall panel '+str(j),'cream roughcast',a,e,-.004,.22,0,1.83)
    for j,cx in enumerate(X_WINDOWS):
        box(b,'Spandrel below opening '+str(j),'cream roughcast',cx-W/2,cx+W/2,-.004,.22,0,SILL)
        box(b,'Header over window '+str(j),'cream roughcast',cx-W/2,cx+W/2,-.004,.22,HEAD,1.83)
    for j,x in enumerate((-2.01,0,2.01)):
        box(b,'Timber post '+str(j),'old dark framing',x-.046,x+.046,-.065,.026,0,1.84)
    box(b,'Continuous lower tie','old dark framing',-HALF,HALF,-.078,.03,.222,.283)
    box(b,'Window head tie','old dark framing',-HALF,HALF,-.084,.02,1.768,1.85)
    for j,cx in enumerate(X_WINDOWS):window(b,cx,j+1,lod)
    def cove(start,end,thickness,mat,label):
        n=4 if lod else 13
        for j in range(n):
            a=j/n*pi/2;v=(j+1)/n*pi/2
            curve=lambda angle:(-.008-.218*(1-cos(angle))-thickness,1.839+.418*sin(angle))
            y,z=curve(a);ye,ze=curve(v)
            profile(b,start,end,[(y,z),(ye,ze),(.12,ze),(.12,z)],mat,label)
    cove(-HALF,HALF,0,'coved soffit','Curved plastered frieze')
    for j in range(9):
        x=-2.00+.50*j
        cove(x-.027,x+.027,.037,'old dark framing',f'Curved exposed rib {j+1}')
    box(b,'Tie under upper gable','old dark framing',-2.12,2.12,-.275,.16,2.254,2.365)
    prism(b,[(-HALF,2.32),(HALF,2.32),(0,TOP)],-.177,.18,'cream roughcast','Triangular white infill')
    def peak(x):return TOP-abs(x)/HALF*(TOP-2.32)
    for j,x in enumerate((-1.06,-.596,0,.596,1.06)):
        section(b,(x,2.32),(x,peak(x)-.049),.065,-.213,-.171,'old dark framing',f'Gable vertical {j}')
    for side in (-1,1):
        for j,(lower,upper) in enumerate(((0,.596),(.596,1.06))):
            section(b,(side*lower,2.344),(side*upper,peak(upper)-.047),.070,-.223,-.173,'old dark framing',f'Splayed gable timber {side} {j}')
        foot=(side*(HALF+.145),2.19)
        top=(0,TOP+.108)
        section(b,foot,top,.122,-.351,-.087,'old dark framing',f'Raking bargeboard {side}')
        section(b,foot,top,.045,-.370,-.341,'warm timber edge',f'Bargeboard outer bead {side}')
        section(b,(foot[0],foot[1]+.079),(0,top[1]+.077),.055,-.337,.263,'grey verge sheet',f'Raking roof edge {side}')
        count=16 if lod else 32
        for j in range(count):
            lo=j/count;hi=min(1,(j+1.10)/count)
            at=lambda t:(foot[0]*(1-t),foot[1]*(1-t)+top[1]*t+.122)
            section(b,at(lo),at(hi),.039,-.302,.24,'light red verge tiles' if j%5==1 else 'red verge tiles',f'Verge tile {side} {j+1}')
