"""Visible stepped red-brick shaft, pebble-dashed gable and clay-tile verge at Yuyuan Road 699."""
from pathlib import Path
from math import ceil,pi,sin
from shapely.geometry import Polygon
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent
MORTAR='Flush grey-pink mortar'; DASH='Exposed coarse grey aggregate'; SLATE='Weathered shoulder coping'; FASCIA='Oxblood bargeboard'; FLASH='Folded metal verge'; TILE='Dull red interlocking tile'; ROOFBED='Dark tile underlap'
BRICKS=['Muted red brick','Russet brick','Oxidised red brick','Rose-coloured brick','Deep red brick']
PALETTE={name:dict(color=list(rgb),roughness=rough) for name,rgb,rough in [
 (MORTAR,(.43,.33,.29),.99),(DASH,(.95,.96,.96),.99),(SLATE,(.27,.25,.24),.94),(FASCIA,(.29,.10,.09),.85),(FLASH,(.53,.52,.47),.83),(TILE,(.72,.61,.60),.92),(ROOFBED,(.24,.16,.16),.98),
 *[(k,v,.96) for k,v in zip(BRICKS,[(.86,.79,.78),(.86,.76,.70),(.81,.72,.70),(.91,.82,.81),(.76,.67,.65)])]]}
ATLAS=384;BED=.070;UNIT=.212
def texture(path):
    if path.exists():return
    rng=np.random.default_rng(20180213)
    Y,X=np.mgrid[0:256,0:256];colors=np.empty((384,384,3),np.uint8)
    mix=rng.normal(0,14,X.shape)+rng.normal(0,12,X.shape)
    fragments=rng.choice([0,-42,31,-22,17],p=[.58,.085,.13,.1,.105],size=X.shape)
    colors[:256,:256]=np.clip([151,148,145]+(mix+fragments)[:,:,None]+rng.normal(0,3,(256,256,3)),0,255)
    frit=rng.normal(0,8,(256,128))+4*np.sin(np.arange(256)[:,None]*.22)+rng.normal(0,2,(256,128))
    colors[:256,256:]=np.clip([181,113,97]+frit[:,:,None],0,255)
    tile=rng.normal(0,6,(128,384))+3*np.sin(np.arange(384)[None,:]*.21)
    colors[256:]=np.clip([180,115,109]+tile[:,:,None],0,255)
    Image.fromarray(colors).quantize(128).save(path,'PNG')
def uv(part,kind):
    pts=part['vertices'];a=np.asarray(pts);base=np.min(a,axis=0)
    bb=np.maximum(np.ptp(a,axis=0),.001)
    if kind=='wall':
        # Map the wall as a continuous rectangle, including its sloping upper edge.
        return [[(.005+.644*(x+1.69)/3.38),(.006+.646*(1-z/3.65))]for x,y,z in pts]
    if kind=='brick':
        return [[.681+.306*(x-base[0])/bb[0],.007+.643*(1-(z-base[2])/bb[2])]for x,y,z in pts]
    return [[.02+.95*(x-base[0])/bb[0],.683+.306*(y-base[1])/bb[1]]for x,y,z in pts]
def surface_mapping(part,kind):
    """Assign a regular UV scale to the front, side return and stone edge."""
    points=np.asarray(part['vertices']);verts=[];uvs=[];tris=[]
    for tri in part['triangles']:
        pts=points[list(tri)]
        dominant=np.argmax(np.abs(np.cross(pts[1]-pts[0],pts[2]-pts[0])))
        for x,y,z in pts:
            if dominant==0:axis=y;vertical=z
            elif dominant==1:axis=x;vertical=z
            else:axis=x;vertical=y
            if kind=='wall':
                u=.012+.630*((axis+1.70)/3.45 if dominant!=0 else (axis+.03)/3.45)
                v=.012+.629*(1-vertical/3.7)
            else:
                axisvals=points[:,1] if dominant==0 else points[:,0]
                verticals=points[:,1] if dominant==2 else points[:,2]
                u=.681+.307*(axis-np.min(axisvals))/max(np.ptp(axisvals),.001)
                v=.009+.64*(1-(vertical-np.min(verticals))/max(.001,np.ptp(verticals)))
            verts.append((x,y,z));uvs.append([u,v])
        n=len(verts);tris.append([n-3,n-2,n-1])
    part.update(vertices=verts,triangles=tris,texcoords=uvs)
def box(b,lo,hi,mat,label):
    b.box([(x+y)*.5 for x,y in zip(lo,hi)],[y-x for x,y in zip(lo,hi)],mat,label=label)
def fascia(b,poly,front,back,mat,label):
    b.prism(Polygon(poly),-back,-front,lambda x,z,d:(x,-d,z),mat,label)
def tile_strip(b,x0,x1,y0,y1,face,lod):
    n=3 if lod else 7;verts=[];faces=[];side=1 if x0+x1>0 else -1
    # Each sloping tile spans its eaves-to-ridge row along X and overlaps the lower row.
    for hh in (0.,.028):
        for v in (x0,x1):
            for i in range(n+1):
                t=i/n; wave=.033*(.5+.5*sin(2*pi*t-.8));verts.append((v,y0+t*(y1-y0),3.68-.78*abs(v)+wave+hh+face+.036*(abs(v)-min(abs(x0),abs(x1)))/abs(x1-x0)))
    size=2*(n+1)
    for i in range(n):
        a=i;b0=n+1+i
        faces.extend([[a,a+1,b0+1,b0],[a+size,b0+size,b0+size+1,a+size+1],[a,a+size,a+size+1,a+1],[b0+1,b0+size+1,b0+size,b0]])
    faces.extend([[0,n+1,n+1+size,size],[n+size,2*n+1+size,2*n+1,n]])
    b.add(verts,faces,TILE,'Lapped tile rows');b.parts[-1]['texcoords']=uv(b.parts[-1],'tile')
def brick(b,l,r,front,back,z,t,mat,lod,label):
    bevel=.0035 if not lod else 0
    if lod:box(b,(l,front,z),(r,back,t),mat,label)
    else:
        # A single chamfered face and a square return keep the vertical joints readable in raking light.
        verts=[(l+bevel,front,z+bevel),(r-bevel,front,z+bevel),(r-bevel,front,t-bevel),(l+bevel,front,t-bevel)]
        for y in (front+bevel,back):verts.extend([(l,y,z),(r,y,z),(r,y,t),(l,y,t)])
        faces=[[0,1,2,3],[11,10,9,8]]
        for j in range(4):
            k=(j+1)%4;faces.extend([[j,4+j,4+k,k],[4+j,8+j,8+k,4+k]])
        b.add(verts,faces,mat,label)
    surface_mapping(b.parts[-1],'brick')
def add_building(b,lod=False):
    tex=HERE/'chimney-materials.png';texture(tex)
    for m in [DASH,TILE,*BRICKS]:b.palette[m]['texture']=str(tex)
    hw=1.66;peak=3.58;eave=peak-.78*hw
    fascia(b,[(-hw,0),(hw,0),(hw,eave),(0,peak),(-hw,eave)],.03,.27,DASH,'Pebble-dashed gable')
    for p in b.parts:surface_mapping(p,'wall')
    for side in (-1,1):
        xs=sorted((0,side*1.71))
        roof=lambda x:3.68-.78*abs(x)
        for fl,bk,upper,lower,material,label in [(-.075,.32,0,-.164,FASCIA,'Deep red bargeboard'),(-.083,-.054,.018,-.044,FLASH,'Folded verge edging'),(-.048,.96,-.01,-.065,ROOFBED,'Tile underlay')]:
            l,r=xs;fascia(b,[(l,roof(l)+lower),(r,roof(r)+lower),(r,roof(r)+upper),(l,roof(l)+upper)],fl,bk,material,label)
        for k in range(6):
            xlo=k*1.73/6;xhi=(k+1)*1.73/6
            x0,x1=sorted((side*max(0,xlo-.012),side*xhi))
            for j in range(7):
                y0=-.066+j*.148;tile_strip(b,x0,x1,y0,y0+.146,.01 if k%2 else .017,lod)
    rng=np.random.default_rng(127)
    for i in range(60):
        z=i*BED
        width,fr=(1.30,-.344) if i<10 else ((.91,-.302) if i<38 else (.69,-.262))
        # Narrow shaft breaks through the pitched roof. Its return depth is inferred from one street view.
        back=.308;core='Wide chimney breast' if i<10 else 'Middle shaft' if i<38 else 'Upper shaft'
        if i in (0,10,38):
            top=10*BED if i==0 else 38*BED if i==10 else 60*BED
            box(b,(-width/2+.003,fr+.012,z),(width/2-.003,back,top),MORTAR,core+' bed')
        left=-width/2;right=width/2;q=left-(.5*UNIT if i%2 else 0)
        while q<right:
            s=max(left,q)+.003;e=min(right,q+UNIT)-.003
            if e>s+.012:brick(b,s,e,fr,fr+.020,z+.003,z+BED-.004,BRICKS[int(rng.integers(5))],lod,core+' front courses')
            q+=UNIT
        for side in (-1,1):
            yy=fr+.018-(UNIT*.5 if i%2==0 else 0)
            while yy<back:
                start=max(fr+.018,yy)+.002;end=min(back,yy+UNIT)-.002
                if end>start+.008:
                    x=side*(width/2-.004)
                    box(b,(x-.006,start,z+.003),(x+.006,end,z+BED-.004),BRICKS[int(rng.integers(5))],core+' return courses')
                    surface_mapping(b.parts[-1],'brick')
                yy+=UNIT
    for z,outside,inner,front in [(10*BED,.653,.455,-.348),(38*BED,.459,.345,-.305)]:
        for sign in (-1,1):
            poly=[(sign*inner,z-.012),(sign*outside,z-.012),(sign*outside,z+.017),(sign*inner,z+.089)]
            fascia(b,poly,front,.310,SLATE,'Sloped shoulder weathering')
