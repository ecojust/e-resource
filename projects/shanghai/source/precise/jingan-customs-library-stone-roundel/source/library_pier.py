"""Stone roundel and fluted, bound rods on the entrance pier of the Shanghai Customs Library."""
from math import cos, sin, pi
import json
from pathlib import Path


def paint(rgb):
    return dict(color=[v/3294.6 if v<=10 else ((v/255+.055)/1.055)**2.4 for v in rgb],metallic=0,roughness=.86)


PALETTE={name:paint(rgb) for name,rgb in {
    'sandstone':(174,157,131),'light ashlar':(177,163,141),'cool ashlar':(161,150,134),
    'joint':(130,120,104),'recess':(139,130,109),'sculpted stone':(168,156,131),
    'round rim':(176,162,139),'flutes':(155,142,123),'stone ties':(175,158,135),
}.items()}
R=.258
CENTRE=.965


def block(b,x0,x1,y0,y1,z0,z1,mat,name):
    b.box(((x0+x1)*.5,(y0+y1)*.5,(z0+z1)*.5),(x1-x0,y1-y0,z1-z0),mat,label=name)


def curved_band(b,x,rad,profile,label,lod):
    segments=8 if lod else 17
    vs=[];fs=[]
    for i in range(segments+1):
        a=-pi/2+pi*i/segments
        for t,(r,z) in enumerate(profile):
            vs.append((x+r*sin(a),.018-r*cos(a),z))
    n=len(profile)
    for i in range(segments):
        for j in range(n-1):
            ix=i*n+j;fs.append((ix,ix+n,ix+n+1,ix+1))
    b.add(vs,fs,'stone ties',label)


def fascio(b,x,lod):
    bottom=.555;top=1.390;rad=.078
    # Flutes face the street and turn around the corners of the stone projection.
    for j in range(9):
        angle=(-.45+j*.1125)*pi
        px=x+rad*sin(angle);py=.018-rad*cos(angle)
        b.tube([(px,py,bottom),(px,py,top)],.0125,'flutes',6 if lod else 10,'stone rod '+str((x,j+1)))
    curved_band(b,x,rad,[(.083,bottom),(.091,bottom+.007),(.091,bottom+.039),(.086,bottom+.048)],'lower collar '+str(x),lod)
    curved_band(b,x,rad,[(.084,top-.030),(.094,top-.021),(.094,top+.005),(.080,top+.018)],'upper collar '+str(x),lod)
    # Three broad diagonal bindings are visible across the front of each bundle.
    for j in range(3):
        z0=.686+j*.171;vs=[];fs=[];nn=11 if lod else 26
        for k in range(nn+1):
            angle=-pi/2+pi*k/nn
            for r,dz in ((.084,-.018),(.094,-.013),(.094,.012),(.085,.018)):
                vs.append((x+r*sin(angle),.018-r*cos(angle),z0+.079*sin(angle)+dz))
        for k in range(nn):
            for v in range(3):
                a=4*k+v;fs.append((a,a+4,a+5,a+1))
        b.add(vs,fs,'stone ties','diagonal binding '+str((x,j+1)))


def medallion(b,lod):
    field=json.loads(Path(__file__).with_name('roundel-samples.json').read_bytes());a=field['heights'];size=field['size']
    def sample(x,y):
        u=(x+1)*(size-1)/2;v=(1-y)*(size-1)/2
        i=min(size-2,max(0,int(u)));j=min(size-2,max(0,int(v)));fu=u-i;fv=v-j
        return ((1-fu)*(1-fv)*a[j][i]+fu*(1-fv)*a[j][i+1]+(1-fu)*fv*a[j+1][i]+fu*fv*a[j+1][i+1])/255.
    rings=15 if lod else 37;segments=64 if lod else 144;vs=[(0,.036-.022*sample(0,0),CENTRE)];fs=[]
    for ri in range(1,rings+1):
        rho=ri/rings
        for j in range(segments):
            ag=2*pi*j/segments;xn=rho*cos(ag);zn=rho*sin(ag)
            vs.append((R*.90*xn,.036-.022*sample(xn,zn),CENTRE+R*.91*zn))
        off=1+(ri-1)*segments
        for j in range(segments):
            nx=(j+1)%segments
            if ri==1:fs.append((0,off+j,off+nx))
            else:fs.append((off-segments+j,off+j,off+nx,off-segments+nx))
    b.add(vs,fs,'sculpted stone','carved stone roundel from Antigng 2018 CC BY-SA 4.0')
    profile=[(.898,.036),(.915,.011),(.939,.005),(.953,.012),(.970,.005),(.985,-.001),(1,.004),(1,.08)]
    vs=[];fs=[]
    for j in range(segments):
        ag=2*pi*j/segments
        for radius,depth in profile:vs.append((R*radius*cos(ag),depth,CENTRE+R*1.01*radius*sin(ag)))
    s=len(profile)
    for j in range(segments):
        for k in range(s-1):fs.append((j*s+k,(j+1)%segments*s+k,(j+1)%segments*s+k+1,j*s+k+1))
    b.add(vs,fs,'round rim','two raised beads around the shield')


def add_building(b,lod=False):
    # The square recess behind the carving has a real back and four returns.
    left,right=-.295,.295;low,high=.652,1.268
    block(b,-.72,.72,.096,.33,0,1.48,'joint','solid stone pier and exposed joints')
    block(b,left,right,.081,.21,low,high,'recess','square backing to stone relief')
    courses=[0,.255,.516,low,.941,high,1.464]
    for j in range(len(courses)-1):
        low1,high1=courses[j:j+2]
        slots=[(-.72,left),(right,.72)] if low<=low1 and high1<=high else [(-.72,.0),(.0,.72)] if j%2==0 else [(-.72,-.34),(-.34,.37),(.37,.72)]
        for k,(a,c) in enumerate(slots):block(b,a+.002,c-.002,.017,.105,low1+.0024,high1-.0024,('sandstone','light ashlar','cool ashlar')[(k+j)%3],'ashlar course '+str((j+1,k+1)))
    medallion(b,lod)
    for x in [-.609,.609]:fascio(b,x,lod)
    for i,(w,depth,z1,z2) in enumerate([(.735,-.015,1.465,1.508),(.748,-.042,1.508,1.580),(.775,-.064,1.581,1.618),(.766,-.052,1.619,1.693),(.779,-.071,1.694,1.722)]):
        block(b,-w,w,depth,.333,z1,z2,'sandstone' if i%2 else 'light ashlar','separate projecting crown band '+str(i+1))
