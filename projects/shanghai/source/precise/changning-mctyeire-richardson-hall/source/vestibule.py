"""Model the Five-Four lecture building entrance from Ctny's August 2017 interior photograph."""
import math
from pathlib import Path
import numpy as np
from shapely.geometry import Point,Polygon,box
from shapely.ops import unary_union
from fit_vestibule import plane_point, HALF, REAR

IVORY='warm ivory plaster'
OAK='dark oak'
TRIM='bronze-black joinery'
GLASS='honey lantern glass'
BRASS='aged bronze'
SKIRT='charcoal stone skirting'
INSET='pale panel recess'
FLOOR='polished mottled floor'
HEIGHT=8.30
PHOTO_SCALE=np.array([1600/950,1067/634])
def bezel(builder,shape,low,high,mapper,mat,label,width=.046):
    band=shape.buffer(width,join_style=1,quad_segs=3).difference(shape)
    builder.prism(band,low,high,mapper,mat,label)

def arch(a,b,bottom,shoulder,rise,segments):
    middle=(a+b)/2;half=(b-a)/2
    points=[(a,bottom),(b,bottom),(b,shoulder)]
    points.extend((middle+half*math.cos(t),shoulder+rise*math.sin(t)) for t in np.linspace(0,math.pi,segments+1)[1:])
    return Polygon(points)

def triple_path(left,right,bottom,shoulder,centre,segments):
    # A broad shouldered four-centred head, gently rising across the middle.
    middle=(left+right)/2;half=(right-left)/2
    quarter=[(left,bottom),(left,shoulder)]
    quarter.extend((left+half*(1-math.cos(t))*.13,shoulder+(centre-shoulder)*math.sin(t)*.55) for t in np.linspace(0,math.pi/2,segments+1)[1:])
    quarter.extend([(middle-half*.32,centre-.09),(middle,centre)])
    return Polygon(quarter+[(2*middle-x,z) for x,z in reversed(quarter[:-1])])

def add_doors(b,mapper,doors,lod):
    for i,opening in enumerate(doors):
        a,z,c,t=opening.bounds;mid=(a+c)/2
        stile=.045
        b.prism(opening.difference(opening.buffer(-stile,join_style=2)),-.065,.008,mapper,OAK,'Vestibule/rear door casing')
        # The middle right leaf opens toward the auditorium in the photograph.
        for j,(left,right) in enumerate(((a+stile,mid-.005),(mid+.005,c-stile))):
            panel=opening.intersection(box(left,z+.019,right,t))
            hinge=right if j else left
            angle=math.radians(72) if i==1 and j==1 else 0
            def leaf(u,h,d):
                effective=-d
                return (hinge+(u-hinge)*math.cos(angle)+effective*math.sin(angle),
                        REAR+.305-(u-hinge)*math.sin(angle)+effective*math.cos(angle),h)
            b.prism(panel,-.04,0,leaf,OAK,'Vestibule/rear door leaf')
            frames=[]
            for band in range(3):
                lo=z+.15+band*(t-z-.27)/3
                for col in range(2 if not lod else 1):
                    n=2 if not lod else 1;x1=left+(right-left)*col/n+.038;x2=left+(right-left)*(col+1)/n-.038
                    rect=box(x1,lo,x2,lo+(t-z-.27)/3-.055)
                    if x2>x1:frames.append(rect.difference(rect.buffer(-.022,join_style=2)))
            b.prism(unary_union(frames).intersection(panel),.003,.021,leaf,OAK,'Vestibule/raised oak panel mouldings')

def railing(b,mapper,a,c,z,h,lod):
    w=c-a
    for offset,thickness in [(0,.065),(h*.74,.052),(h,.065)]:
        b.prism(box(a,z+offset,c,z+offset+thickness),.01,.085,mapper,TRIM,'Vestibule/gallery rails')
    count=max(3,round(w/.24))
    decorations=[]
    for i in range(count+1):
        x=a+w*i/count
        decorations.append(box(x-.014,z+.045,x+.014,z+h))
        if i<count:
            step=w/count
            loop=arch(x+.014,x+step-.014,z+h*.69,z+h*.76,h*.19,5 if lod else 8)
            decorations.append(loop.difference(loop.buffer(-.024,join_style=2)).intersection(box(x,z+h*.75,x+step,z+h)))
    b.prism(unary_union(decorations),.019,.054,mapper,TRIM,'Vestibule/pointed gallery balusters')

def lantern(b,m,lod):
    def photo(u,v,axis,k):return plane_point(m,*(np.array([u,v])*PHOTO_SCALE),axis,k)
    mount=photo(507,54,2,HEIGHT)
    cx,y=mount[:2];n=10
    def level(v):return photo(510,v,1,y)[2]
    def radius(u,v):return abs(photo(u,v,1,y)[0]-cx)
    upper=level(192);lower=level(245);r=radius(587,207);inner_r=r*.48
    b.lathe((cx,y),[(HEIGHT-.115,.072),(HEIGHT-.06,.12),(HEIGHT,.102),(HEIGHT+.075,.066)],TRIM,10,'Lantern/ceiling rose')
    b.tube([(cx,y,level(149)),(cx,y,HEIGHT-.09)],.019,TRIM,6,'Lantern/suspension chain')
    def rim(z,outer,inner,thickness,label):
        edge=Polygon([(cx+outer*math.cos(i*math.tau/n),y+outer*math.sin(i*math.tau/n)) for i in range(n)])
        void=Polygon([(cx+inner*math.cos(i*math.tau/n),y+inner*math.sin(i*math.tau/n)) for i in range(n)])
        b.plan_prism(edge.difference(void),z,z+thickness,BRASS,label)
    rim(lower-.02,r*1.012,r*.937,.061,'Lantern/open lower crown ring')
    rim(upper-.015,r*1.015,r*.938,.052,'Lantern/open upper crown ring')
    def post(r,a,h):return (cx+r*math.cos(a),y+r*math.sin(a),h)
    for i in range(n):
        a=math.tau*i/n;aa=a+math.tau/n
        b.tube([post(r,a,lower-.07),post(r,a,upper+.075)],.025,TRIM,6,'Lantern/crown jamb')
        b.tube([post(r,a,upper+.04),(cx,y,level(148))],.019,BRASS,6,'Lantern/crown hipped wire')
        p=np.array(post(r*.97,a,0));q=np.array(post(r*.97,aa,0));length=float(np.linalg.norm(q-p));direction=(q-p)/length;normal=np.cross(direction,[0,0,1.])
        def facet(u,z,d):
            out=(p+q)/2+direction*u+normal*d;return (out[0],out[1],z)
        w=length/2;h=upper-lower
        outline=Polygon([(-w+.04,lower+.14*h),(-w+.04,upper-.13*h),(-w*.50,upper-.13*h),(-w*.30,upper-.025*h),(0,upper-.085*h),(w*.30,upper-.025*h),(w*.5,upper-.13*h),(w-.04,upper-.13*h),(w-.04,lower+.14*h),(w*.42,lower+.14*h),(0,lower+.038*h),(-w*.42,lower+.14*h)])
        b.prism(outline,-.015,.013,facet,GLASS,'Lantern/lobed honey-coloured crown panels')
        quatre=[]
        for lift in [.23,.75]:
            radius=w*.27;cz=lower+h*lift
            lobes=unary_union([Point(math.cos(t)*radius*.64,cz+math.sin(t)*radius*.64).buffer(radius,quad_segs=4 if lod else 7) for t in np.arange(4)*math.pi/2])
            quatre.append(lobes.boundary.buffer(.012,quad_segs=2).intersection(outline))
        grille=unary_union([*quatre,outline.difference(outline.buffer(-.025,join_style=2))])
        b.prism(grille,.014,.034,facet,BRASS,'Lantern/floral brass overlay')
    for z1,z2,rad in [(level(289),level(237),inner_r),(level(307),level(291),inner_r*.48)]:
        b.lathe((cx,y),[(z1,rad*.89),(z1+.027,rad),(z2-.027,rad),(z2,rad*.96)],GLASS,n,'Lantern/pendant amber glazing')
        for z in [z1,z2]:b.lathe((cx,y),[(z-.022,rad),(z+.022,rad)],BRASS,n,'Lantern/pendant metal rim')
        for i in range(n):b.tube([post(rad,i*math.tau/n,z1),post(rad,i*math.tau/n,z2)],.016,BRASS,5,'Lantern/pendant ribs')

def build_vestibule(b,lod=False):
    import json
    path=Path(__file__).resolve().parents[1]/'measurements/vestibule-station.json'
    m=np.array(json.loads(path.read_text())['projection'])
    def point(uv,axis,k):return plane_point(m,*(np.asarray(uv)*PHOTO_SCALE),axis,k)
    def rx(u,v):return point((u,v),1,REAR)[0]
    def rz(u,v):return point((u,v),1,REAR)[2]
    rear=lambda u,z,d:(u,REAR-d,z)
    surface=box(-HALF,0,HALF,HEIGHT)
    broad=triple_path(rx(419,524),rx(688,524),.04,rz(421,444),rz(545,423),5)
    galleries=[];segments=10 if lod else 19
    for a,c,v in [(428,478,254),(490,581,229),(598,653,235)]:
        left=rx(a,345);right=rx(c,345);top=rz((a+c)/2,v)
        galleries.append(arch(left,right,rz((a+c)/2,359),top-(right-left)*.53,(right-left)*.53,segments))
    b.prism(surface.difference(unary_union([broad,*galleries])),-.32,0,rear,IVORY,'Vestibule/rear plaster arcade')
    for i,q in enumerate(galleries):
        bezel(b,q,-.025,.063,rear,IVORY,'Vestibule/round upper archivolt',.085)
        a,z,c,t=q.bounds;railing(b,rear,a,c,z,.77,lod)
        if i!=2:
            between=(c+galleries[i+1].bounds[0])/2
            b.lathe((between,REAR-.008),[(z,.151),(z+.068,.15),(z+.111,.096),(t-.45,.095),(t-.39,.133),(t-.29,.145)],IVORY,8 if lod else 12,'Vestibule/gallery column')
    bezel(b,broad,-.016,.065,rear,IVORY,'Vestibule/auditorium portal stepped moulding',.065)
    bezel(b,broad.buffer(.079,join_style=2),-.012,.036,rear,IVORY,'Vestibule/outer portal bead',.038)
    doors=[]
    for a,c,v in [(422,498,454),(508,606,449),(616,680,446)]:
        left=rx(a,530);right=rx(c,530)
        doors.append(triple_path(left,right,.065,rz((a+c)/2,v+12),rz((a+c)/2,v),4))
    b.prism(broad.difference(unary_union(doors)),-.69,-.24,rear,INSET,'Vestibule/recessed three-door screen')
    add_doors(b,rear,doors,lod)
    floor_back=REAR+1.5
    b.box((0,floor_back/2,.025),(HALF*2,floor_back,.05),FLOOR,label='Vestibule/polished stone floor')
    for z in [.044,.105,.18]:
        b.prism(box(-HALF,z,HALF,z+.033).difference(broad),0,.056,rear,SKIRT,'Vestibule/stone rear skirting')
    # Low-relief blind panels in the band under the gallery and fluted jambs at the rear corners.
    panels=[]
    for i in range(19):
        cx=-2.30+i*.256
        q=arch(cx-.081,cx+.081,3.47,3.65,.087,5)
        panels.append(q.difference(q.buffer(-.017,join_style=2)))
    b.prism(unary_union(panels),.006,.021,rear,INSET,'Vestibule/subtle gallery frieze')
    for sign in (-1,1):
        for n in range(3):
            u=sign*(2.68+n*.072)
            b.prism(box(u-.025,.065,u+.025,HEIGHT-.15),.007,.050,rear,IVORY,'Vestibule/rear plaster pilaster fillets')
    # The position of the west arcade is read directly; the partly cropped opposite return is mirrored.
    def sidepoint(u,v):
        p=point((u,v),0,-HALF);return (p[1],p[2])
    def sidearch(a,c,base,sp,peak):
        left=sidepoint(a,sp)[0];right=sidepoint(c,sp)[0]
        top=sidepoint((a+c)/2,peak)[1];shoulder=sidepoint((a+c)/2,sp)[1]
        return arch(left,right,base,shoulder,max(.2,top-shoulder),segments)
    low=sidearch(170,264,.04,405,388);up=sidearch(191,254,sidepoint(217,306)[1],184,138)
    niche=sidearch(279,299,.67,510,495)
    wall=box(.12,0,REAR,HEIGHT)
    for sign in (-1,1):
        def side(u,z,d):return (sign*(HALF-d),-sign*u,z)
        def oriented(q):
            if sign==-1:return q
            from shapely.affinity import scale
            return scale(q,xfact=-1,yfact=1,origin=(0,0))
        for q in [low,up,niche]:
            bezel(b,oriented(q),-.012,.082,side,IVORY,'Vestibule/side arcade architrave',.084)
        b.prism(oriented(wall.difference(unary_union([low,up,niche]))),-.33,0,side,IVORY,'Vestibule/side arcade')
        for q in [up,low]:
            a,z,c,t=oriented(q).bounds
            if q is up:railing(b,side,a,c,z,.70,lod)
        b.prism(oriented(niche),-.212,-.155,side,INSET,'Vestibule/side niche back')
        b.prism(oriented(box(.12,.055,REAR,.26).difference(low)),-.006,.045,side,SKIRT,'Vestibule/side skirting')
        # The two amber wall sconces flank the broad rear doors on the plaster pilaster faces.
        u=sign*3.43
        b.box((u,REAR-.09,3.11),(.094,.14,.30),TRIM,label='Vestibule/wall light mounting')
        b.tube([(u,REAR-.08,3.11),(u,REAR-.29,3.16),(u,REAR-.32,3.30)],.030,TRIM,7,'Vestibule/wall light bracket')
        for z,w in [(3.24,.15),(3.64,.175)]:b.box((u,REAR-.32,z),(w,.15,.04),BRASS,label='Vestibule/wall lantern rim')
        b.box((u,REAR-.32,3.44),(.134,.125,.35),GLASS,label='Vestibule/wall lantern glazing')
        for sx in (-1,1):
            b.box((u+sx*.078,REAR-.388,3.44),(.018,.023,.40),TRIM,label='Vestibule/wall lantern ribs')
    # Plaster coffer beams meet at actual rectangular crossings; mouldings step back to the ceiling.
    b.box((0,REAR/2,HEIGHT+.171),(HALF*2,REAR,.20),IVORY,label='Vestibule/coffer ceiling slab')
    ys=[.14,3.0,6.0,9.05,12.04,REAR];xs=[-HALF,-2.18,1.26,HALF]
    for n,(width,base,thick) in enumerate([(.25,HEIGHT-.14,.20),(.37,HEIGHT+.001,.07),(.48,HEIGHT+.062,.058)]):
        strips=[box(u-width/2,0,u+width/2,REAR) for u in xs]+[box(-HALF,y-width/2,HALF,y+width/2) for y in ys]
        b.plan_prism(unary_union(strips),base,base+thick,IVORY,'Vestibule/stepped ceiling beam tier '+str(n+1))
    lantern(b,m,lod)
