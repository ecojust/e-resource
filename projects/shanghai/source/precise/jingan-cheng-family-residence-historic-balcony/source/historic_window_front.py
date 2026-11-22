"""Second-floor windows, stone profiles and four perforations above the right bay."""
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,box,LineString,Point
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
DATA=json.loads((HERE.parent/'measurements/upper-wall-returns.json').read_bytes())
WALL='Cheng residence | dark mineral facing'
STONE='Cheng residence | pale window surround'
LIP='Cheng residence | projecting stone edge'
WOOD='Cheng residence | painted timber'
SHADOW='Cheng residence | dark recess'
GLASS='Cheng residence | silvery reflected light'
DARK_GLASS='Cheng residence | glass in shade'
LIGHT_PANEL='Cheng residence | light timber panel'
DULL_PANEL='Cheng residence | grey facing panel'

def plain(rgb,rough=.8,metal=0.):
    a=np.array(rgb,dtype=float)/255.
    return dict(color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={WALL:dict(texture=str(HERE/'street-roughcast.png'),color=[1.,1.,1.],roughness=.94),
STONE:dict(texture=str(HERE/'pale-stone.png'),color=[1.,1.,1.],roughness=.89),
LIP:plain([187,185,176]),WOOD:plain([177,174,161],.65),SHADOW:plain([38,38,36]),
GLASS:plain([150,154,151],.29,.12),DARK_GLASS:plain([57,62,61],.33,.10),
LIGHT_PANEL:plain([188,187,174],.71),DULL_PANEL:plain([155,154,145],.85)}
class Face:
    def __init__(self,b,record):
        self.b=b;self.idx=record['index'];self.origin=np.array(record['start'])
        d=np.array(record['end'])-self.origin;self.length=np.linalg.norm(d)
        self.u=d/self.length;self.n=np.array([-self.u[1],self.u[0]])
        self.label=['West return','Balcony wall','East splay','East projecting bay'][self.idx]
    def point(self,x,z,d):
        xy=self.origin+self.u*x+self.n*d
        return (xy[0],xy[1],z)
    def shape(self,poly,a,b,mat,label):
        if poly.is_empty:return
        if poly.geom_type!='Polygon':
            for p in poly.geoms:self.shape(p,a,b,mat,label)
            return
        self.b.prism(orient(poly,sign=1),-b,-a,lambda x,z,y:self.point(x,z,-y),mat,self.label+' | '+label)
    def rect(self,l,b,r,t,front,back,mat,label):
        if r-l>.0003 and t-b>.0003:self.shape(box(l,b,r,t),front,back,mat,label)
def rows(face,x0,x1,z0,z1,count,depth,color,name):
    for k in range(1,count):
        z=z0+(z1-z0)*k/count
        face.rect(x0,z-.012,x1,z+.012,depth,depth+.034,color,name)
def casement(f,w,lod):
    key=w['key'];ol,orr,ob,ot=w['surround_m'];l,r,b,t=w['opening_m'];span=r-l
    outer=box(ol,ob,orr,ot)
    opening=box(l,b,r,t)
    f.shape(outer.difference(opening),-.034,.025,STONE,'cut window surround')
    # A white-painted lining projects a little into the clear opening and covers the roughcast cut edges.
    edge=opening.buffer(.012,join_style=2).difference(box(l+.027,b+.021,r-.027,t-.027))
    f.shape(edge,-.018,.181,STONE,'painted inner reveal')
    frame=opening.difference(box(l+.057,b+.059,r-.057,t-.064))
    f.shape(frame,.132,.205,WOOD,'rebated fixed frame')
    f.rect(l-.004,b-.003,r+.005,t+.005,.249,.281,SHADOW,'recess back')
    L=l+.055;R=r-.055;B=b+.054;T=t-.062;m=(l+r)/2
    if key=='left_splay':
        f.rect(L-.016,B-.018,R+.016,T+.016,.165,.193,DARK_GLASS,'continuous shadowed sash')
    else:
        trans=min(w['transom_z_m'],T-.012)
        f.rect(L,trans-.022,R,trans+.022,.123,.197,WOOD,'transom rail')
        for i,(a,c) in enumerate(((L,m-.012),(m+.012,R))):
            dark=key=='left_splay' or (key in ('right_splay','balcony_right') and i==0)
            paint=DULL_PANEL if dark else WOOD
            surface=DARK_GLASS if dark else GLASS
            if T-trans>.06:
                f.rect(a+.015,trans+.023,c-.015,T,.182,.199,DARK_GLASS,'small upper light')
            leaf=box(a,B,c,trans-.018);pane=box(a+.029,B+.044,c-.029,trans-.063)
            f.shape(leaf.difference(pane),.134,.191,paint,'casement edges')
            z0=B+.04;z1=trans-.056
            # Only the outer bay has a bright opaque panel across the lower field of both leaves.
            if key=='right_front':
                split=b+.44*(t-b)
                f.rect(a+.024,z0,c-.024,split,.165,.202,LIGHT_PANEL,'lower field')
                f.rect(a+.02,split-.017,c-.02,split+.019,.13,.181,WOOD,'panel rail')
                z0=split+.016
            f.rect(a+.021,z0,c-.021,z1,.176,.198,surface,'glazed field')
            if not dark:
                rows(f,a+.026,c-.026,z0,z1,3 if key=='right_front' else 4,.157,WOOD,'small pane bars')
            elif key!='left_splay' and not lod:
                rows(f,a+.033,c-.033,z0,z1,3,.168,SHADOW,'shadowed rail')
            if key=='right_front' and not lod:
                x=(a+c)/2;f.rect(x-.009,z0,x+.009,z1,.149,.179,WOOD,'narrow upright')
            if not lod and not dark:
                f.rect(a+.018,z0,c-.018,z0+.011,.153,.186,LIP,'lower rebate')
        f.rect(m-.018,B,m+.018,T,.124,.191,WOOD,'meeting stile')
    if not key.startswith('balcony'):
        # The old photograph shows a continuous broad light panel below each
        # outer sill, cut off here at the recorded second-floor excerpt.
        f.rect(ol+.012,-.227,orr-.012,b-.208,-.014,.004,DULL_PANEL,'light apron beneath bay')
        f.rect(ol+.012,-.226,ol+.05,b-.202,-.021,.007,STONE,'apron west edge')
        f.rect(orr-.048,-.226,orr-.012,b-.202,-.021,.007,STONE,'apron east edge')
        f.rect(ol-.014,b-.13,orr+.014,b-.047,-.086,.024,LIP,'projecting sill')
        f.rect(ol+.013,b-.202,orr-.013,b-.129,-.053,.02,STONE,'sill bed')
        # In the old plate the light sill projects past a short, recessed apron.
        f.rect(ol+.07,b-.313,orr-.07,b-.197,-.026,.014,STONE,'shallow sill apron')
def offset_profile(faces,d):
    corners=[faces[0].origin+d*faces[0].n]
    for a,b in zip(faces,faces[1:]):
        ma=b.origin+d*a.n;mb=b.origin+d*b.n
        h=np.linalg.solve(np.column_stack((a.u,-b.u)),mb-ma)
        corners.append(ma+h[0]*a.u)
    corners.append(faces[-1].origin+faces[-1].length*faces[-1].u+d*faces[-1].n)
    return corners
def cornice(b,faces,z0,z1,d0,d1,mat,label):
    front=offset_profile(faces,d0);back=offset_profile(faces,d1)
    foot=orient(Polygon([*front,*back[::-1]]),sign=1)
    b.prism(foot,z0,z1,lambda x,y,z:(x,y,z),mat,label)
def ribbon(f,coords,width,mat,label):
    f.shape(LineString(coords).buffer(width/2,cap_style=1,join_style=1),-.108,-.065,mat,label)
def spiral(f,x,z,r,lod,label,sign=1):
    ang=np.linspace(-.45*math.pi,1.62*math.pi,15 if lod else 33)
    taper=np.linspace(1.,.2,len(ang))
    coords=np.column_stack((x+sign*r*taper*np.cos(ang),z+r*taper*np.sin(ang)))
    ribbon(f,coords,.021 if r<.15 else .028,LIP,label)
def top_details(faces,lod):
    f=faces[1]
    pts=DATA['left_and_centre_top'];j=[min(max(x,0.),f.length)for x,z in pts]
    for lab,l,r,z in [('west',0,j[1],pts[0][1]),('centre',j[1],j[5],pts[2][1]),('east',j[5],f.length,pts[-1][1])]:
        f.rect(l,3.201,r,z,-.005,.245,WALL,lab+' parapet face')
        f.rect(l-.002,z-.057,r+.002,z+.008,-.048,.253,LIP,lab+' parapet cap')
        f.rect(l,z-.087,r,z-.057,-.028,.248,STONE,lab+' parapet fillet')
    for side,base,x,s in [('west',pts[0][1],j[1],-1),('east',pts[-1][1],j[5],1)]:
        plate=[(x,base),(x,base+.235),(x+s*.047,base+.229),(x+s*.159,base+.166),(x+s*.23,base+.11),(x+s*.234,base)]
        f.shape(Polygon(plate),-.069,.064,STONE,side+' curled shoulder')
        spiral(f,x+s*.125,base+.102,.092,lod,side+' shallow rolled ornament',s)
    f=faces[3];c={k:np.array(v['face_xz_m'])for k,v in DATA['right_bay_crown'].items()}
    lz=DATA['right_shoulder_z'];outer=Polygon(c['outline']);l,b,r,t=outer.bounds
    # The four top lights show sky and foliage. The backing must end around the
    # pierced panel even where its lower lights lie below the side shoulders.
    crown_body=box(float(c['top_cap'][:,0].min()+.024),3.195,float(c['top_cap'][:,0].max()-.024),float(c['top_cap'][:,1].min()+.018))
    parapet=box(0,3.195,f.length,lz).union(crown_body)
    f.shape(parapet.difference(outer.buffer(.014,join_style=2)),-.003,.25,WALL,'projecting bay parapet around pierced crown')
    for a,e in ((0,l),(r,f.length)):
        f.rect(a,lz-.034,e,lz+.027,-.04,.255,LIP,'shoulder capping')
    aperture=unary_union([Polygon(c[k])for k in ('upper_light','right_light','lower_light','left_light')])
    f.shape(outer.buffer(.033,join_style=2).difference(aperture),-.047,.102,STONE,'square pierced crown and four openings')
    inner=Polygon(c['inner']);f.shape(outer.difference(inner),-.078,-.039,STONE,'outer surround of square crown')
    f.shape(Polygon(c['top_cap']),-.100,.158,LIP,'flat crown cap')
    f.shape(Polygon(c['stone_sill']),-.107,.086,LIP,'crown sill')
    for n,s in [('left',-1),('right',1)]:
        f.shape(Polygon(c[n+'_volute']),-.067,.11,STONE,n+' volute plate')
        pts=c[n+'_spiral_center'];r=np.linalg.norm(pts[1]-pts[0])
        spiral(f,*pts[0],r,lod,n+' raised scroll',s)
def add_historic_front(builder,lod=False):
    builder.palette.update(PALETTE)
    faces=[Face(builder,record)for record in DATA['faces']]
    for face in faces:
        obs=[r for r in DATA['windows']if r['face']==face.idx]
        holes=[]
        for w in obs:
            l,r,b,t=w['opening_m'];holes.append(box(l-.008,b-.009,r+.008,t+.009))
        main=box(0,-.232,face.length,2.495).difference(unary_union(holes))
        face.shape(main,0.,.278,WALL,'wall cut for observed windows')
        for w in obs:casement(face,w,lod)
    # Continuous, mitred changes of profile follow the actual return corners.
    courses=[(2.484,2.546,-.032,STONE),(2.546,2.583,-.057,LIP),(2.583,2.638,-.086,STONE),
             (2.638,2.731,-.100,STONE),(2.731,2.781,-.136,LIP),(2.781,3.058,-.090,STONE),
             (3.058,3.112,-.133,LIP),(3.112,3.174,-.098,STONE),(3.174,3.215,-.044,LIP)]
    for k,(lo,hi,dep,mat)in enumerate(courses):
        cornice(builder,faces,lo,hi,dep,.253,mat,'Eaves | change of profile '+str(k+1))
    for i in (0,2):
        f=faces[i];upper=DATA['right_shoulder_z'] if i==2 else DATA['left_and_centre_top'][0][1]
        f.rect(0,3.202,f.length,upper,-.002,.249,WALL,'low parapet')
        f.rect(0,upper-.025,f.length,upper+.026,-.047,.26,LIP,'low parapet cap')
    top_details(faces,lod)
    return faces
