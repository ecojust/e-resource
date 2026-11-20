"""Original office-and-court exterior based on National Archives plates NA30-005–015."""
from math import ceil,cos,pi,sin
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
from photo_architecture import Facade,opening

PALETTE={k:{'color':v,'roughness':rough} for k,v,rough in [
    ('buff ashlar',[.676,.621,.523],.94),('lime trim',[.785,.738,.628],.90),
    ('rusticated joint',[.512,.484,.418],.98),('warm render',[.649,.591,.490],.94),
    ('cool plinth',[.579,.560,.505],.91),('pale sill',[.775,.743,.665],.86),
    ('painted sash',[.213,.186,.150],.76),('aged glazing',[.234,.271,.274],.40),
    ('olive shutter',[.213,.233,.192],.86),('shadow ashlar',[.517,.477,.394],.95),
    ('dark hardwood',[.205,.153,.104],.85),('lead flashing',[.335,.352,.347],.87),
    ('grey butterfly tile',[.253,.265,.264],.95),('ridge tile',[.337,.348,.341],.95),
    ('terrace paving',[.644,.611,.544],.96),('roof light',[.350,.415,.425],.42),
    ('roof light frame',[.262,.312,.307],.80),('soffit',[.615,.578,.487],.96)
]}
PLINTH=.73
FLOOR=5.78
CORNICE=11.52

def courses(face,field,lod):
    """Rustication is inset in the piers and stops at each arch or shutter."""
    if lod:
        return
    width=face.length
    for j in range(1,22):
        z=PLINTH+j*.465
        belt=field.intersection(box(-width/2,z,width/2,z+.022))
        if belt.area>.0001:
            face.prism(belt,.005,.014,'rusticated joint','fine ashlar joints')
        for x in range(-28,29,3):
            u=x+(1.5 if j%2 else 0)
            seam=field.intersection(box(u,z+.028,u+.014,z+.457))
            if seam.area>.0001:face.prism(seam,.005,.013,'rusticated joint','offset vertical stone joints')

def cornices(face):
    for z,h,depth,material in [
        (PLINTH-.08,.15,.22,'cool plinth'),(FLOOR-.32,.10,.13,'lime trim'),
        (FLOOR-.13,.17,.32,'lime trim'),(FLOOR+.03,.10,.42,'pale sill'),
        (CORNICE-.38,.13,.18,'lime trim'),(CORNICE-.20,.17,.34,'lime trim'),
        (CORNICE+.03,.15,.66,'pale sill')]:
        face.beam(z,h,depth,material,label='moulded string course')

def arch_trim(face,u,bottom,width,height,rise,lod):
    ap=opening(u,bottom,width,height,rise,12 if lod else 22)
    rad=width/2
    contour=ap.buffer(.136,join_style=2).difference(ap)
    face.prism(contour,.012,.112,'lime trim','voussoir surround')
    if not lod:
        for t in range(1,10):
            angle=t*pi/10;zz=bottom+height-rise
            p=(u+rad*cos(angle),zz+rise*sin(angle),.12)
            q=(u+(rad+.136)*cos(angle),zz+(rise+.136)*sin(angle),.12)
            face.line(p,q,.008,'rusticated joint',4,'voussoir joints')
    return ap

def sash(face,ap,lod,outside=False):
    """Recessed glass and solid mullions are local to each reveal."""
    x0,z0,x1,z1=ap.bounds
    face.prism(ap,-.32,-.30,'aged glazing','recessed glass')
    inner=ap.buffer(-.074,join_style=2)
    bars=[box((x0+x1)/2-.027,z0,(x0+x1)/2+.027,z1)]
    for t in ([.50] if lod else [.33,.67]):
        h=z0+(z1-z0)*t;bars.append(box(x0,h-.022,x1,h+.022))
    panes=inner.difference(unary_union(bars))
    face.prism(ap.difference(panes),-.235,-.16,'painted sash','sash frames and mullions')
    if outside and not lod:
        for sign in (-1,1):
            x=(x0-.22 if sign<0 else x1+.22);z=(z0+z1)/2
            face.box(x,z,.35,z1-z0-.12,.082,.07,'olive shutter','slatted shutters')
            for n in range(1,10):
                h=z0+(z1-z0)*n/10
                face.box(x,h,.27,.028,.025,.119,'painted sash','shutter slats')

def balusters(face,center,width,z,d,lod):
    face.box(center,z+.105,width,.13,.23,d,'lime trim','balcony stone base')
    face.box(center,z+.83,width+.06,.13,.31,d,'pale sill','balcony handrail')
    n=max(3,round(width/.25));b=face.builder
    for ix in range(n):
        u=center-width/2+(ix+.5)*width/n;v=face.point(u,z,d)
        b.lathe(v[:2],[(z+h,r) for h,r in [(0,.061),(.10,.077),(.17,.052),(.32,.091),(.43,.074),(.57,.046),(.69,.071),(.76,.067)]],'lime trim',6 if lod else 10,'Turned stone balcony balusters')

def gallery(face,indices,lod):
    centers=list(indices);lower=[];upper=[]
    for x in centers:
        lower.append(arch_trim(face,x,PLINTH,2.21,4.28,1.07,lod))
        upper.append(opening(x,FLOOR+.05,2.24,4.43,0))
    return lower,upper

def main_front(b,start,end,count,lod,name):
    """Five central lower arches and a recessed upper loggia, flanked by windows."""
    f=Facade(b,start,end,name);step=f.length/count;centers=[(i-(count-1)/2)*step for i in range(count)]
    low_gallery,high_gallery=gallery(f,centers[count//2-2:count//2+3],lod)
    lo=list(low_gallery);hi=list(high_gallery);ends=[];rearcenters=[]
    for j,x in enumerate(centers):
        if abs(j-count//2)<=2:
            rearcenters.append(x);balusters(f,x,2.21,FLOOR+.05,-.01,lod)
        else:
            a=opening(x,PLINTH+.38,1.48,3.29,0);h=arch_trim(f,x,FLOOR+.65,1.52,3.59,.72,lod)
            lo.append(a);hi.append(h);ends.extend([a,h]);balusters(f,x,1.48,FLOOR+.49,-.008,lod)
    field=f.wall(PLINTH,CORNICE,lo+hi,.46,'buff ashlar');courses(f,field,lod);cornices(f)
    for ap in ends:sash(f,ap,lod)
    bld=Facade(b,(f.point(0,0,-2.44)-f.t*5*step/2)[:2],(f.point(0,0,-2.44)+f.t*5*step/2)[:2],name+'/loggia rear')
    inside=[]
    for j in range(5):
        x=(j-2)*step
        if j==2:
            glass=opening(x,PLINTH,1.62,3.57,.25,12)
            bld.prism(glass,-.18,-.11,'dark hardwood','recessed double leaves')
            bld.box(x,2.55,.038,3.3,.045,-.065,'painted sash','central door stile')
            inside.append(glass)
        else:
            ap=opening(x,PLINTH+.44,1.55,3.0,0);inside.append(ap);sash(bld,ap,lod)
        ap=opening(x,FLOOR+.48,1.49,3.15,0);inside.append(ap);sash(bld,ap,lod)
    bld.wall(PLINTH,CORNICE,inside,.35,'shadow ashlar')
    half=2*step+1.13
    for k in (-1,1):
        loc=f.point(k*half,0,-1.445)
        b.box((loc[0],loc[1],(PLINTH+CORNICE)/2),(.14,1.99,CORNICE-PLINTH),'shadow ashlar',basis=[f.t,f.n,[0,0,1]],label=name+'/gallery returns')
    for z in (PLINTH-.10,FLOOR-.11,CORNICE-.13):
        loc=f.point(0,z,-1.24);b.box(loc,(2*half,2.52,.20),'soffit',basis=[f.t,f.n,[0,0,1]],label=name+'/gallery floors and soffit')
    f.box(0,PLINTH/2,f.length,PLINTH,.54,-.16,'cool plinth','raised ground plinth')

def wing_wall(b,start,end,count,lod,name,upper_arch=False,lower_arch=False):
    f=Facade(b,start,end,name);step=f.length/count;holes=[]
    for i in range(count):
        x=(i-(count-1)/2)*step
        up=upper_arch[i] if isinstance(upper_arch,tuple) else upper_arch
        down=lower_arch[i] if isinstance(lower_arch,tuple) else lower_arch
        for z,w,h,r in [(1.32,1.64,3.21,.75 if down else 0),(6.51,1.60,3.48,.78 if up else 0)]:
            if r:ap=arch_trim(f,x,z,w,h,r,lod)
            else:
                ap=opening(x,z,w,h,0)
                f.box(x,z+h+.12,w+.42,.14,.29,.09,'lime trim','rectangular window hood')
            holes.append(ap);sash(f,ap,lod,outside=True);f.box(x,z-.036,w+.23,.12,.31,.08,'pale sill','window sill')
    field=f.wall(PLINTH,CORNICE,holes,.38,'warm render');courses(f,field,lod);cornices(f)
    f.box(0,PLINTH/2,f.length,PLINTH,.40,-.20,'cool plinth','raised foundation')

def tribunal(b,lod):
    """The west office/court front in the labelled 1911 and 1913 archival plates."""
    x=-21.88;y0=17.0;y1=40.6
    f=Facade(b,(x,y1),(x,y0),'West former court colonnade');centers=[(v-2.5)*3.22 for v in range(6)]
    openings=[]
    for i in (-3,-2,-1,1,2,3):
        u=i*2.84;ap=opening(u,1.05,1.29,2.93,.25);openings.append(ap);sash(f,ap,lod)
    door=opening(0,.76,2.04,3.37,0);openings.append(door);f.prism(door,-.29,-.27,'dark hardwood','court entrance')
    field=f.wall(PLINTH,FLOOR-.15,openings,.42,'buff ashlar');courses(f,field,lod)
    for u in centers[1:-1]:
        p=f.point(u,0,.04)
        b.lathe(p[:2],[(FLOOR,.34),(FLOOR+.13,.39),(FLOOR+.28,.30),(FLOOR+.43,.245),(10.64,.208),(10.84,.26),(10.95,.33),(11.08,.33)],'lime trim',10 if lod else 18,'Court portico stone columns')
        f.box(u,11.16,.81,.18,.79,.03,'pale sill','column abacus')
    for u in (-8.08,8.08):f.box(u,8.53,.56,5.45,.63,.04,'buff ashlar','outside engaged pier')
    for u in (-2*3.22,-3.22,0,3.22,2*3.22):balusters(f,u,2.75,FLOOR+.02,-.08,lod)
    rear=Facade(b,(x+2.55,y1),(x+2.55,y0),'Court upper set-back');holes=[]
    for u in [-2*3.22,-3.22,0,3.22,2*3.22]:
        ap=opening(u,6.30,1.72,3.84,0);holes.append(ap);sash(rear,ap,lod)
    rear.wall(FLOOR,CORNICE,holes,.40,'shadow ashlar')
    for u in [-9.93,9.93]:
        head=opening(u,FLOOR+.51,1.35,3.54);wall=box(u-1.70,FLOOR-.04,u+1.70,CORNICE)
        f.prism(wall.difference(head),-.49,0,'buff ashlar','end pavilions');sash(f,head,lod,outside=True)
    cornices(f);f.box(0,PLINTH/2,f.length,PLINTH,.4,-.15,'cool plinth','court foundation')
    f.box(0,CORNICE-.34,16.74,.53,.76,.03,'lime trim','classical entablature')
    f.box(0,FLOOR-.15,16.5,.26,2.81,-1.30,'soffit','colonnade floor')
    for u in [-7.6,-4.55,-1.52,1.52,4.55,7.6]:balusters(f,u,2.79,CORNICE+.16,-.02,lod)
    for u in [-8.96,-6.08,-3.04,0,3.04,6.08,8.96]:f.box(u,CORNICE+.61,.36,.98,.40,-.02,'lime trim','parapet piers')
    for k in (-1,1):
        u=k*1.57;p=f.point(u,0,.62)
        b.lathe(p[:2],[(.72,.23),(.90,.22),(1.02,.17),(3.98,.15),(4.10,.21),(4.27,.22)],'lime trim',10 if lod else 16,'Court doorway columns')
    f.box(0,4.36,3.91,.23,1.08,.43,'pale sill','doorcase hood')

def hip(b,x0,x1,y0,y1,eave,height,lod,label):
    L=x1-x0;D=y1-y0;span=min(L,D);z=eave+height
    if L>=D:
        a=(x0+span*.45,(y0+y1)/2,z);d=(x1-span*.45,(y0+y1)/2,z)
    else:
        a=((x1+x0)/2,y0+span*.45,z);d=((x1+x0)/2,y1-span*.45,z)
    q=[(x0,y0,eave),(x1,y0,eave),(x1,y1,eave),(x0,y1,eave)]
    faces=[[q[0],q[1],d,a],[q[1],q[2],d],[q[2],q[3],a,d],[q[3],q[0],a]] if L>=D else [[q[0],q[1],a],[q[1],q[2],d,a],[q[2],q[3],d],[q[3],q[0],a,d]]
    for face in faces:b.add(face,[tuple(range(len(face)))],'grey butterfly tile',label+'/hip planes')
    for i,t in enumerate(q):b.tube([t,a if i in ([0,3]if L>=D else[0,1])else d],.073,'ridge tile',6,label+'/hip rolls')
    b.tube([a,d],.092,'ridge tile',8,label+'/ridge')
    if not lod:
        for f in faces:
            for i in range(1,16):
                t=i/16;u,v=f[0],f[1];s,e=f[-1],f[2];a0=tuple(A+(B-A)*t for A,B in zip(u,s));a1=tuple(A+(B-A)*t for A,B in zip(v,e))
                b.tube([a0,a1],.018,'ridge tile',4,label+'/butterfly tile courses')

def terrace(b,lod):
    x0,x1,y0,y1=20.64,25.25,11.65,30.72
    b.plan_prism(box(x0,y0,x1,y1),.03,PLINTH-.03,'terrace paving','East garden terrace')
    for i,(a,c) in enumerate([((x1,y0),(x1,y1)),((x0,y0),(x1,y0)),((x1,y1),(x0,y1))]):
        f=Facade(b,a,c,'East terrace stone rail')
        seg=6 if i==0 else 2
        for j in range(seg):
            u=((j+.5)/seg-.5)*f.length
            if i==0 and j in (2,3):continue
            balusters(f,u,f.length/seg-.18,PLINTH-.04,0,lod)
        for j in range(seg+1):
            if i==0 and j==3:continue
            f.box((j/seg-.5)*f.length,PLINTH+.45,.29,.93,.31,0,'lime trim','square terrace pillars')
    for i in range(4):
        # Stair stays within the table's eastern central projection.
        b.plan_prism(box(x1+i*.259,18.18,x1+(i+1)*.26,24.14),.017,PLINTH-(i+1)*.155,'terrace paving','East garden stair')

def office(b,lod):
    main_front(b,(-8.40,.78),(20.63,.78),9,lod,'South five-bay entry')
    main_front(b,(20.63,1.25),(20.63,41.55),13,lod,'East garden gallery')
    wing_wall(b,(20.63,41.94),(-8.4,41.94),9,lod,'Northern 1913 office elevation',
              (False,False,True,True,False,False,False,False,False),
              (True,True,False,False,True,True,True,False,False))
    wing_wall(b,(-8.4,5.90),(-8.4,1.25),2,lod,'Southwest office return',True)
    wing_wall(b,(-21.88,5.90),(-8.4,5.90),4,lod,'South court addition',False)
    wing_wall(b,(-21.88,17),(-21.88,6.29),3,lod,'1913 west extension',False)
    tribunal(b,lod)
    wing_wall(b,(-8.4,40.6),(-21.88,40.6),4,lod,'North former court wall',False,True)
    narrow=Facade(b,(-8.4,41.55),(-8.4,40.6),'North junction return')
    narrow.wall(0,CORNICE,[],.36,'warm render');cornices(narrow)
    for x0,x1,y0,y1,z,rise,name in [(-8.65,20.85,.54,42.15,CORNICE+.09,2.84,'Main butterfly-tile roof'),(-22.07,-8.38,5.72,16.95,CORNICE+.09,1.48,'South court roof'),(-21.85,-8.35,16.92,33.1,CORNICE+.06,1.64,'Court western roof'),(-22.02,-8.32,33.12,40.8,CORNICE+.06,1.46,'North court roof')]:
        hip(b,x0,x1,y0,y1,z,rise,lod,name)
    # Low glazed roof observed on the aerial west of the office's main ridge.
    b.plan_prism(box(-8.63,17.02,-1.65,32.36),11.50,12.92,'roof light frame','West roof light curb')
    for i in range(4):
        for j in range(8):
            u=-8.53+i*1.69;v=17.1+j*1.89
            b.plan_prism(box(u,v,u+1.62,v+1.83),12.925,13.04,'roof light','West rectangular roof glazing')
    for x in (-2.5,9.1):
        for y in (10.2,19.2,28.2,37.1):
            b.box((x,y,14.01),(1.05,.88,2.81),'warm render',label='Office chimneys')
            b.box((x,y,15.43),(1.32,1.13,.21),'pale sill',label='Chimney head caps')
    for x,y in [(-17.0,14.2),(-16,36.1)]:
        b.box((x,y,13.25),(.98,.86,2.87),'warm render',label='Court chimneys')
        b.box((x,y,14.76),(1.24,1.09,.20),'pale sill',label='Court chimney caps')
    b.plan_prism(box(-8.40,.78,20.63,41.94),-.06,PLINTH-.10,'cool plinth','Garden office foundation')
    b.plan_prism(box(-21.88,5.90,-8.395,40.6),-.06,PLINTH-.10,'cool plinth','Court foundation')
    terrace(b,lod)
    for i in range(3):
        b.plan_prism(box(2.82,-.02+i*.26,9.25,.24+i*.26),-.015,.18*(i+1),'terrace paving','South entrance steps')
