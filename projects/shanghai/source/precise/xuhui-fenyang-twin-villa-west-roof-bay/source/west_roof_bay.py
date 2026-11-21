"""South-west end roof at Fenyang Road 152–154, from the 2020 survey and the conservation photographs."""
from math import hypot
from random import Random
import numpy as np
from shapely.geometry import Polygon, box as rectangle
from shapely.geometry.polygon import orient
from photo_architecture import Facade

HALF_WALL = 4.0813
EAVE = 10.40
CUT_BOTTOM = 6.75
REAR = 6.10
TILE = ('Terracotta red','Terracotta ochre','Terracotta umber','Terracotta salmon')
RIDGE='Weathered ridge tile'
JOINT='Deep tile bed'
PLASTER='Combed grey render'
PALE='Off-white plaster band'
DARK='Brown structural timber'
GLASS='Deep reflected glazing'
LIGHT='Pale glass reflections'
SHADOW='Window recess'
BRONZE='Aged bronze window frame'
GUTTER='Weathered eaves gutter'
SLATE='Rear roof closing surface'

PALETTE={k:{'color':v,'roughness':r}for k,v,r in [
 (TILE[0],[.52,.258,.17],.89),(TILE[1],[.585,.321,.197],.87),(TILE[2],[.40,.204,.138],.91),
 (TILE[3],[.595,.34,.252],.89),(RIDGE,[.66,.372,.252],.83),(JOINT,[.303,.17,.125],.96),
 (PLASTER,[.48,.443,.394],.95),(PALE,[.75,.75,.686],.90),(DARK,[.165,.114,.085],.83),
 (GLASS,[.12,.146,.154],.32),(LIGHT,[.193,.229,.235],.43),(SHADOW,[.089,.080,.070],.94),
 (BRONZE,[.24,.191,.155],.75),(GUTTER,[.28,.269,.229],.73),(SLATE,[.34,.28,.24],.96)]}

def cuboid(b, label, material, x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),material,label=label)

def timber(b,label,a,c,width,height,material=DARK):
    a,c=np.array(a),np.array(c);axis=c-a;length=np.linalg.norm(axis);axis/=length
    ref=np.array([0.,0.,1.]) if abs(axis[2])<.97 else np.array([0.,1.,0.])
    side=np.cross(axis,ref);side/=np.linalg.norm(side);up=np.cross(side,axis)
    b.box((a+c)*.5,(length,width,height),material,basis=[axis,side,up],label=label)
    # Both end faces must average to the requested measured edge endpoints.
    v=np.asarray(b.parts[-1]['vertices'])
    assert np.allclose(v[[0,3,4,7]].mean(axis=0),a) and np.allclose(v[[1,2,5,6]].mean(axis=0),c),(label,a,c)

def tiled_face(b,label,points,lod,seed):
    """Lay actual staggered tiles in the plane, cutting edge tiles against the hips."""
    v=np.array(points,dtype=float)
    normal=np.cross(v[1]-v[0],v[2]-v[0]);normal/=np.linalg.norm(normal)
    if normal[2]<0:normal=-normal
    along=np.cross(np.array([0.,0.,1.]),normal);along/=np.linalg.norm(along)
    rise=np.cross(normal,along)
    if rise[2]<0:rise=-rise
    base=v[0];coords=[(np.dot(p-base,along),np.dot(p-base,rise))for p in v]
    outline=Polygon(coords)
    assert outline.is_valid and outline.area>.3,(label,coords)
    def world(u,z,off):return tuple(base+u*along+z*rise+off*normal)
    b.prism(outline,-.091,0,world,JOINT,label+' board')
    step=.316 if lod else .268;gauge=.30 if lod else .217
    xmin,ymin,xmax,ymax=outline.bounds;row=0;rng=Random(seed)
    z=ymin
    while z<ymax:
        x=xmin-step/2*(row%2)
        while x<xmax:
            area=outline.intersection(rectangle(x+.008,z+.012,x+step-.007,z+gauge-.006))
            shade=rng.choices(TILE,weights=[9,7,4,3])[0]
            if area.area>.002 and area.geom_type=='Polygon':
                coords=list(orient(area, sign=1).exterior.coords)[:-1]
                top=[world(u,h,.012+.026*(1-(h-z)/gauge))for u,h in coords]
                bottom=[world(u,h,.002)for u,h in coords]
                n=len(top)
                b.add(bottom+top,[tuple(range(n,2*n)),*[(i,(i+1)%n,n+(i+1)%n,n+i)for i in range(n)]],shade,label+' tile courses')
            x+=step
        row+=1;z=ymin+row*gauge

def double_window(b,f,cx,width,bottom,top,col,row,prefix):
    h=top-bottom
    f.box(cx,(top+bottom)/2,width+.18,h+.15,.08,-.18,SHADOW,prefix+' opening back')
    inset=.095
    pane_width=(width-2*inset)/col; pane_height=(h-2*inset)/row
    for i in range(col):
        for j in range(row):
            f.box(cx-width/2+inset+(i+.5)*pane_width,bottom+inset+(j+.5)*pane_height,pane_width-.037,pane_height-.036,.035,-.048,GLASS if (i+j)%3 else LIGHT,prefix+' glass')
    for x in [cx-width/2+inset/2,cx+width/2-inset/2]:
        f.box(x,(top+bottom)/2,inset,h,.14,.014,DARK,prefix+' timber jambs')
    for k in range(1,col):
        f.box(cx-width/2+inset+k*pane_width,(top+bottom)/2,.056,h-2*inset,.10,.003,BRONZE,prefix+' vertical sash')
    for z in [bottom+inset/2,top-inset/2]:
        f.box(cx,z,width,inset,.14,.014,DARK,prefix+' head and sill')
    for j in range(1,row):
        f.box(cx,bottom+inset+j*pane_height,width-.16,.046,.10,.01,BRONZE,prefix+' meeting rail')

def add_building(b,lod):
    z=EAVE;a=HALF_WALL
    street=Facade(b,(-a,0),(a,0),'Upper residential bay')
    top=z-.10;head=z-.36;sill=z-2.10;width=2.68
    holes=[rectangle(c-width/2-.035,sill-.035,c+width/2+.035,head+.035)for c in (-1.69,1.69)]
    street.wall(CUT_BOTTOM,top,holes,thickness=.30,material=PLASTER)
    street.box(0,CUT_BOTTOM+.16,2*a+.085,.21,.20,.025,PALE,'Upper storey lower stringcourse')
    for c in (-1.69,1.69):
        double_window(b,street,c,width,sill,head,3,2,'Twin upper windows')
        street.box(c,sill-.095,width+.16,.11,.24,.04,PALE,'Projecting window stool')
    for side in [-1,1]:
        x=side*a
        cuboid(b,'Return render shell',PLASTER,x-.12,x+.12,.06,REAR,CUT_BOTTOM,z-.09)
        for pair in (-2.40,2.40):
            off=pair+side*.115
            cuboid(b,'Paired corbel wall block',DARK,off-.07,off+.07,-.06,.15,z-.83,z-.17)
            timber(b,'Paired corbel diagonal',(off,-.01,z-.75),(off,-.82,z-.12),.116,.133)
            cuboid(b,'Paired corbel cap',DARK,off-.075,off+.075,-.83,.17,z-.19,z-.08)
    cuboid(b,'Lower eave boarded soffit',DARK,-4.76,4.76,-1.00,REAR,z-.106,z-.062)
    cuboid(b,'Lower rain gutter',GUTTER,-4.76,4.76,-1.045,-.942,z-.143,z-.028)
    half=4.76;rear=REAR;inner=3.98;lip=2.34
    lowl=(-half,-1,z);lowr=(half,-1,z);lowl_back=(-half,rear,z);lowr_back=(half,rear,z)
    upperl=(-lip,-.38,z+2.37);upperr=(lip,-.38,z+2.37)
    hip=(0,2.67,z+5.85);ridge=(0,rear,z+5.85)
    silll=(-inner,.02,z+.91);sillr=(inner,.02,z+.91)
    tiled_face(b,'Lower front apron',[lowl,lowr,sillr,silll],lod,101)
    tiled_face(b,'Front upper hip',[upperl,upperr,hip],lod,113)
    for sign in (-1,1):
        low=lowl if sign<0 else lowr;upper=upperl if sign<0 else upperr;end=lowl_back if sign<0 else lowr_back
        shoulder=(-inner if sign<0 else inner,.02,z+.91)
        # Three sloping polygons also preserve the plane change beside the attic opening.
        tiled_face(b,'Western long roof' if sign<0 else 'Eastern long roof',[low,end,ridge,hip],lod,126+sign)
        tiled_face(b,'Sloped attic side' if sign<0 else 'Sloped attic return',[low,hip,upper],lod,139+sign)
        b.add([shoulder,upper,(sign*1.99,.04,z+.91)],[(0,1,2)],PALE,'Attic plaster cheek')
        timber(b,'Light fascia to cheek',shoulder,upper,.105,.115,PALE)
        timber(b,'Long ceramic hip roll',low,hip,.12,.095,RIDGE)
        timber(b,'Short front hip roll',upper,hip,.12,.105,RIDGE)
    attic=Facade(b,(-2.12,.16),(2.12,.16),'Recessed attic band')
    double_window(b,attic,0.,4.16,z+1.02,z+2.22,4,2,'Attic horizontal sash')
    attic.box(0,z+.99,4.55,.12,.23,.014,PALE,'Pale attic sill')
    for x in (-2.17,2.17):cuboid(b,'Attic cheek mullion',DARK,x-.061,x+.061,-.05,.36,z+.91,z+2.31)
    for x in np.linspace(-2.22,2.22,13 if not lod else 9):
        timber(b,'Upper lip rafter ends',(x,-.38,z+2.32),(x,.04,z+2.39),.085,.11)
    cuboid(b,'Upper lip dark fascia',DARK,-lip,lip,-.415,-.32,z+2.27,z+2.36)
    timber(b,'Short central ridge',hip,ridge,.18,.13,RIDGE)
    b.add([lowl_back,lowr_back,ridge],[(0,1,2)],SLATE,'Rear roof cut plane')
    cuboid(b,'Rear storey cut',SLATE,-a,a,rear-.12,rear,CUT_BOTTOM,z-.061)
