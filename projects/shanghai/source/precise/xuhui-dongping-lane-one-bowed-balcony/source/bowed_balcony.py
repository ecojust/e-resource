"""The arched glazed opening and shallow bow balcony in Fayhoo's photograph of Lane 1 Dongping Road."""
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box, Point, Polygon, LineString
from shapely.affinity import scale,rotate,translate
ID='xuhui-dongping-lane-one-bowed-balcony'
STONE='Cream ashlar render';TRIM='Raised cream window moulding';GLASS='Grey sea-green glazing';STEEL='Black painted balcony iron';WOOD='Brown glazed door frame';GLAZE='Olive stained glass leaves';AMBER='Amber stained glass';PLINTH='Grey limestone balcony sill'
PALETTE={k:dict(color=c,roughness=r) for k,c,r in [(STONE,[1,1,1],.92),(TRIM,[.77,.737,.653],.83),(GLASS,[.544,.653,.606],.36),(STEEL,[.105,.12,.119],.61),(WOOD,[.19,.15,.10],.68),(GLAZE,[.273,.425,.294],.44),(AMBER,[.603,.405,.197],.46),(PLINTH,[.597,.578,.513],.89)]}
R=.585;SPRING=1.841
def arch(r,base=.23,n=48):return Polygon([(-r,base),(r,base),(r,SPRING),*[(r*np.cos(t),SPRING+r*np.sin(t))for t in np.linspace(0,np.pi,n+1)],(-r,base)])
def texture():
    f=Path(__file__).with_name('cream-ashlar.png')
    if not f.exists():
        y,x=np.indices((384,384));g=np.random.default_rng(759)
        v=np.array([202,196,179])+g.normal(0,3,x.shape)[:,:,None];v[y%74<2]=[163,159,143]
        Image.fromarray(v.clip(0,255).astype('uint8')).quantize(100).save(f)
    PALETTE[STONE]['texture']=str(f)
def balcony(t):return np.array([1.03*np.sin(t),-.12-.59*np.cos(t)])
def add_building(b,far=False):
    texture();res=18 if far else 44
    def relief(p,lo,hi,m,name):
        if p.area>1e-9:b.prism(p,lo,hi,lambda x,z,d:(x,-d,z),m,name)
    outer=arch(.735,.22,res);hole=arch(R,.22,res)
    relief(box(-1.32,.11,1.32,2.74).difference(outer),-.19,0,STONE,'Pale wall and level joints')
    relief(outer.difference(hole),-.16,.067,TRIM,'Wide moulded architrave')
    for delta in [.018,.052,.086,.12]:
        edge=arch(R+delta+.011,.215,res).difference(arch(R+delta,.20,res))
        relief(edge,.065,.083,TRIM,'Concentric narrow arch and jamb ribs')
    key=Polygon([(-.070,2.412),(.070,2.412),(.115,2.599),(-.115,2.599)])
    relief(key,.064,.146,TRIM,'Projecting tapered keystone')
    relief(box(-.046,2.458,.046,2.573),.143,.156,PLINTH,'Raised narrow tongue of the keystone')
    for sign in [-1,1]:
        center=sign*.654;relief(box(center-.114,1.793,center+.114,1.868),.063,.116,TRIM,'Square impost at springing')
    relief(hole.difference(arch(R-.032,.264,res)),-.101,-.017,WOOD,'Dark narrow glazing frame')
    relief(arch(R-.032,.264,res),-.120,-.091,GLASS,'Pair of glazed doors and rounded fanlight')
    relief(box(-.572,1.800,.572,1.847),-.095,-.012,WOOD,'Transom below coloured fanlight')
    relief(box(-.022,.256,.022,1.798),-.096,-.010,WOOD,'Central stile of paired doors')
    def leaf(cx,cz,rx,rz,angle,mat):
        oval=Point(0,0).buffer(1,resolution=6 if far else 12);p=translate(rotate(scale(oval,rx,rz),angle),cx,cz)
        relief(p,-.091,-.082,mat,'Original geometric stained-glass motif')
    for sign in [-1,1]:
        x=sign*.289
        stem=LineString([(x-.05,.409),(x+.065,.789),(x-.055,1.084),(x+.035,1.541)]).buffer(.007)
        relief(stem,-.092,-.082,GLAZE,'Curved green stem in rectangular light')
        for dx,z,ang in [(-.045,.715,35),(.017,.868,-30),(-.070,1.243,40),(.055,1.426,-35)]:leaf(x+dx,z,.031,.065,ang,GLAZE)
        leaf(x,1.342,.048,.064,sign*30,AMBER);leaf(sign*.261,2.023,.058,.088,sign*34,AMBER)
        leaf(sign*.128,2.134,.069,.102,sign*49,GLAZE)
    outline=lambda rad,depth:Polygon([(rad*np.sin(t),-.08-depth*np.cos(t))for t in np.linspace(-np.pi/2,np.pi/2,res+1)]+[(rad,.04),(-rad,.04)])
    for bot,top,r,dep,mat in [(0,.067,.991,.578,PLINTH),(.066,.131,1.063,.667,TRIM),(.130,.181,1.046,.650,PLINTH),(.180,.209,1.064,.674,TRIM)]:
        b.plan_prism(outline(r,dep),bot,top,mat,'Bowed stone balcony slab and projecting edge')
    def tube(vertices,radius,name):
        verts=[];faces=[];n=6 if far else 10;vertices=np.array(vertices)
        for i,pt in enumerate(vertices):
            axis=vertices[min(i+1,len(vertices)-1)]-vertices[max(0,i-1)];axis/=np.linalg.norm(axis)
            seed=np.array([0.,1.,0.]);seed=np.array([1.,0.,0.])if abs(np.dot(axis,seed))>.91 else seed
            v=np.cross(axis,seed);v/=np.linalg.norm(v);q=np.cross(axis,v)
            verts.extend(pt+radius*(v*np.cos(k*2*np.pi/n)+q*np.sin(k*2*np.pi/n))for k in range(n))
        for i in range(len(vertices)-1):
            for k in range(n):
                a=i*n+k;c=i*n+(k+1)%n;faces.extend([(a,c,c+n),(a,c+n,a+n)])
        b.add(verts,faces,STEEL,name)
    for h,r in [(.235,.014),(.343,.012),(.866,.027)]:
        tube([[*balcony(t),h]for t in np.linspace(-np.pi/2,np.pi/2,res+1)],r,'Bowed horizontal iron rail')
    for t in np.linspace(-np.pi/2,np.pi/2,15):
        loc=balcony(t);inward=np.array([np.sin(t),-np.cos(t)])
        tube([[*(loc+inward*.042*np.sin(np.pi*s)),.227+.641*s]for s in np.linspace(0,1,8 if far else 15)],.010,'Light bellied iron upright')
        if abs(t)>1.46:continue
        tangent=np.array([np.cos(t),.56*np.sin(t)])
        for sign in [-1,1]:
            pts=[]
            for s in np.linspace(0,1,12 if far else 24):
                angle=s*1.40*np.pi;dist=.056*(1-.65*s)
                v=loc+inward*.029+tangent*sign*(.051+dist*np.sin(angle))
                pts.append([*v,.779+dist*np.cos(angle)])
            tube(pts,.007,'Inward curl just below handrail')
    for part in b.parts:
        if part['material']==STONE:part['texcoords']=[[(x+1.32)/1.6,z/1.52]for x,y,z in part['vertices']]
