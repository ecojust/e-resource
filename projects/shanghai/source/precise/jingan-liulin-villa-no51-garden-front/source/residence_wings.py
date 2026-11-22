"""No.51 twin garden bays, timber casements, upper enclosure and photographed rear loggia walls."""
from pathlib import Path
import json
import math
import numpy as np
from shapely.geometry import Polygon,box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
STUDY=json.loads((HERE.parent/'measurements/no51-wings-and-window-surrounds.json').read_bytes())
BRICK='Villa | silver-grey garden brick'
TILE='Villa | weathered red pan tile'
LIME='Villa | pale rendered surrounds'
STONE='Villa | grey-beige sill stone'
DARK='Villa | inner window shade'
WOOD='Villa | reddish-brown timber'
GLASS=['Villa | pale sky pane','Villa | reflected tree pane','Villa | shaded window pane']
BLIND='Villa | brown timber blinds'
METAL='Villa | painted rainwater pipes'
AWNING='Villa | blue canopy'
WHITE='Villa | white enclosure frames'
def finish(rgb,rough=.83,metal=0):
    a=np.array(rgb,dtype=float)/255
    return dict(color=np.where(a<=.04045,a/12.92,((a+.055)/1.055)**2.4).tolist(),roughness=rough,metallic=metal)
PALETTE={
    BRICK:dict(texture=str(HERE/'garden-grey-bricks.png'),color=[1.,1.,1.],roughness=.90),
    TILE:dict(texture=str(HERE/'garden-red-tiles.png'),color=[1.,1.,1.],roughness=.83),
    LIME:finish((215,206,184)),STONE:finish((184,181,164)),DARK:finish((54,54,47)),
    WOOD:finish((102,75,62),.59),GLASS[0]:finish((132,149,154),.32,.12),
    GLASS[1]:finish((102,116,112),.33,.13),GLASS[2]:finish((79,85,82),.36,.10),
    BLIND:finish((97,90,71)),METAL:finish((123,126,114),.57,.22),
    AWNING:finish((113,150,174),.47,.11),WHITE:finish((201,207,203),.65,.08)}
class Face:
    def __init__(self,b,start,end,tag):
        self.b=b;self.a=np.array(start,float);v=np.array(end,float)-self.a
        self.width=np.linalg.norm(v);self.u=v/self.width;self.n=np.array([-self.u[1],self.u[0]]);self.tag=tag
    def point(self,x,z,depth):
        xy=self.a+x*self.u+depth*self.n
        return float(xy[0]),float(xy[1]),float(z)
    def skin(self,poly,front,back,mat,name):
        if poly.is_empty:return
        if poly.geom_type!='Polygon':
            for area in poly.geoms:
                if area.geom_type=='Polygon':self.skin(area,front,back,mat,name)
            return
        self.b.prism(orient(poly,sign=1),-back,-front,lambda x,z,q:self.point(x,z,-q),mat,self.tag+' | '+name)
    def bar(self,l,r,b,t,front,back,mat,name):
        if r-l>.001 and t-b>.001:self.skin(box(l,b,r,t),front,back,mat,name)
def make_leaf(face,x,width,b,t,frame,glass,rows,cols,lod,angle=0,depth=.176,glass_recess=0.):
    origin=face.a+x*face.u+depth*face.n
    direction=math.cos(angle)*face.u-math.sin(angle)*face.n
    leaf=Face(face.b,origin,origin+width*direction,face.tag)
    edge=.038 if frame==WOOD else .027
    inside=box(edge,b+edge,width-edge,t-edge)
    leaf.skin(box(0,b,width,t).difference(inside),-.02,.026,frame,'casement perimeter')
    height=t-b-2*edge;run=width-2*edge
    for i in range(rows):
        for j in range(cols):
            l=edge+run*j/cols;r=edge+run*(j+1)/cols;low=b+edge+height*i/rows;high=b+edge+height*(i+1)/rows
            leaf.bar(l,r,low,high,.010+glass_recess,.021+glass_recess,glass[(i//2+j)%len(glass)],'glazing')
    for i in range(1,rows):
        z=b+edge+height*i/rows
        leaf.bar(edge,width-edge,z-.012,z+.012,-.011,.014,frame,'horizontal glazing bar')
    for j in range(1,cols):
        u=edge+run*j/cols
        leaf.bar(u-.013,u+.013,b+edge,t-edge,-.014,.012,frame,'vertical glazing bar')
def wood_window(face,rect,floor,wide,lod,opened=False,apron=True):
    l,r,b,t=rect
    void=box(l,b,r,t);extent=box(l-.16,b-.105,r+.16,t+.16)
    face.skin(extent.difference(void),-.043,.03,LIME,'cream window surround')
    face.skin(box(l-.025,b-.024,r+.025,t+.024).difference(box(l+.006,b+.006,r-.006,t-.006)),.0,.285,STONE,'recess lining')
    face.bar(l-.18,r+.18,t+.14,t+.235,-.061,.030,LIME,'projecting lintel')
    face.bar(l-.196,r+.196,b-.13,b-.035,-.136,.06,STONE,'outer sill')
    if apron:
        face.bar(l-.137,r+.137,b-.47,b-.122,-.038,.031,LIME,'apron')
        for x in (l-.16,r+.025):face.bar(x,x+.135,b-.59,b-.122,-.055,.025,LIME,'apron lug')
    w=r-l;bt=b+.025;tt=t-.025;transom=bt+(tt-bt)*(.76 if floor in (1,2) else .77)
    face.skin(void.difference(box(l+.042,b+.041,r-.042,t-.041)),.12,.215,WOOD,'outer fixed timber frame')
    face.bar(l+.034,r-.034,transom-.036,transom+.036,.104,.199,WOOD,'transom rail')
    count=2 if wide else 1
    topcount=3 if wide else 2
    glass=[GLASS[2],GLASS[1]] if floor==1 else [GLASS[1],GLASS[0]]
    for part in range(topcount):
        span=(w-.084)/topcount
        make_leaf(face,l+.042+span*part,span,transom+.036,tt-.018,WOOD,glass,1,1,lod,depth=.160)
    for part in range(count):
        span=(w-.084)/count;x=l+.042+span*part
        if opened:
            if part==0:make_leaf(face,x,span,bt+.021,transom-.036,WOOD,[GLASS[0]],3,1,lod,math.radians(68))
            else:
                # The opposite leaf hinges at its outer jamb and swings toward the photographer.
                origin=face.a+(x+span)*face.u+.176*face.n
                v=math.cos(math.radians(57))*face.u+math.sin(math.radians(57))*face.n
                leaf=Face(face.b,origin-span*v,origin,face.tag)
                make_leaf(leaf,0,span,bt+.021,transom-.036,WOOD,[GLASS[1]],3,1,lod,depth=0)
        else:make_leaf(face,x,span,bt+.021,transom-.036,WOOD,glass,4 if floor==1 else 3,2 if wide else 1,lod,glass_recess=.103 if floor==1 else 0.)
    face.bar(l-.014,r+.014,b-.015,t+.014,.324,.345,DARK,'deep window back')
    if opened or floor==1:
        height=transom-b-.07;num=max(8,round(height/(.104 if lod else .069)))
        if opened:
            face.bar(l+.058,r-.058,b+.046,transom-.045,.244,.264,BLIND,'drawn interior blind')
        for k in range(num):
            z=b+.047+height*k/num
            face.bar(l+.050,r-.050,z,z+height/num*.51,.229,.253,BLIND,'horizontal blind slat')
def bands(f,short=False):
    for z,h,front in [(4.40,.075,-.12),(4.475,.14,-.14),(4.615,.075,-.172),
                      (8.285,.085,-.094),(8.37,.15,-.13),(8.52,.062,-.16),
                      (11.988,.07,-.10),(12.058,.1,-.14),(12.158,.065,-.18)]:
        f.bar(0,f.width,z,z+h,front,.026,STONE if h<.08 else LIME,'horizontal eaves course' if z>11 else 'continuous floor moulding')
def apply_face(b,wing,label,pts,lod):
    f=Face(b,*pts,'Garden '+wing+' '+label)
    pane=STUDY['facets'].get(wing+'-'+label,{}).get('openings',[])
    holes=[]
    for window in pane:
        l,r,low,top=window['inner_sash_rect_m'];holes.append(box(l-.014,low-.014,r+.014,top+.014))
    f.skin(box(0,.34,f.width,12.15).difference(unary_union(holes)),0,.33,BRICK,'garden wall')
    f.bar(0,f.width,.022,.365,-.012,.30,STONE,'plinth')
    for win in pane:
        wood_window(f,win['inner_sash_rect_m'],win['floor'],label=='middle',lod,wing=='left' and label=='middle' and win['floor']==2)
    bands(f)
    return f
def roof_panel(b,foot,heights,mat,label,thickness=.080):
    layout=np.asarray(foot,float)
    for i in range(1,len(layout)-1):
        ids=[0,i,i+1];p=layout[ids];hs=np.array(heights)[ids]
        q=np.linalg.solve(np.c_[p,np.ones(3)],hs)
        def point(x,y,z):return x,y,q[0]*x+q[1]*y+q[2]+z
        b.prism(orient(Polygon(p),sign=1),-thickness,0,point,mat,label)
def wings(b,lod=False):
    b.palette.update(PALETTE)
    chain=STUDY['corner_chains_m']
    for wing in ('left','right'):
        pts=np.asarray(chain[wing],float)
        order=['outer','middle','inner'] if wing=='left' else ['inner','middle','outer']
        for pair,label in enumerate(order):apply_face(b,wing,label,pts[pair:pair+2],lod)
        end_idx=0 if wing=='left' else 3;edge=pts[end_idx];inner=pts[3-end_idx];sign=-1 if wing=='left' else 1
        outerback=[edge[0]+sign*.12,4.7]
        segment=[outerback,edge] if wing=='left' else [edge,outerback]
        outer=Face(b,*segment,'Garden '+wing+' outer wall')
        outer.bar(0,outer.width,.02,12.16,0,.29,BRICK,'visible roof return')
        bands(outer)
        high=np.array([(pts[1,0]+pts[2,0])*.50,2.82])
        top=12.36
        for i in range(3):
            roof_panel(b,[pts[i],pts[i+1],high],[top,top,13.03],TILE,'Roof | hipped bay tiles')
        roof_panel(b,[edge,outerback,high],[top,12.44,13.03],TILE,'Roof | photographed outside hip')
        # Conceal the inside of the measured facade section at its cropped rear edge.
        rear=Face(b,outerback,[inner[0],4.7],'Garden '+wing+' rear closure') if wing=='right' else Face(b,[inner[0],4.7],outerback,'Garden '+wing+' rear closure')
        rear.bar(0,rear.width,.26,12.08,0,.19,BRICK,'plain rear closure')
        b.plan_prism(orient(Polygon([*pts,[pts[-1,0],4.7],[pts[0,0],4.7]]),sign=1),12.14,12.25,STONE,'Roof | bay eaves')
    middle=Face(b,[-4.40,2.280],[4.29,2.280],'Garden ground loggia rear')
    try:
        from entrance_portal import combined_wall_cut
        left,right,bottom,top=combined_wall_cut()
    except ImportError:
        left,right,bottom,top=-2.62,2.20,.48,3.39
    entrance=box(left-middle.a[0],bottom,right-middle.a[0],top)
    middle.skin(box(0,.03,middle.width,4.59).difference(entrance),0,.35,BRICK,'wall beside portal')
    upstairs=Face(b,[-4.38,1.746],[4.32,1.746],'Garden upper loggia rear')
    rects=[(-2.58,-1.44,5.27,7.77),(-.88,.66,4.64,7.80),(1.12,2.35,5.26,7.79)]
    holes=[box(l-upstairs.a[0]-.014,z-.014,r-upstairs.a[0]+.014,t+.014) for l,r,z,t in rects]
    upstairs.skin(box(0,4.52,upstairs.width,8.55).difference(unary_union(holes)),0,.30,BRICK,'cloister rear wall')
    for i,(l,r,z,t)in enumerate(rects):
        wood_window(upstairs,[l-upstairs.a[0],r-upstairs.a[0],z,t],2,i==1,lod,apron=i!=1)
    # The attached light enclosure is separately visible behind the parapet in both photos.
    house=Face(b,[-3.12,.72],[3.12,.72],'Roof glazed enclosure')
    n=10;span=house.width/n
    for i in range(n):
        make_leaf(house,i*span,span,10.115,11.938,WHITE,[GLASS[0],GLASS[1]],1,1,lod,depth=0)
        if not lod:house.bar(i*span+.038,(i+1)*span-.038,11.56,11.586,-.024,.013,WHITE,'upper glazing light')
    for x,dx in [(-3.12,.76),(3.12,-.76)]:
        outer=Face(b,[x,.72],[x+dx,1.75],'Roof end sash')
        make_leaf(outer,0,outer.width,10.115,11.938,WHITE,[GLASS[0],GLASS[1]],1,2,lod,depth=0)
    awning=[[-3.24,.40],[3.24,.40],[3.24,1.45],[-3.24,1.45]]
    roof_panel(b,awning,[11.982,11.982,12.112,12.112],AWNING,'Roof | blue glazing canopy',.055)
    for x in np.linspace(-3.21,3.21,8):
        b.tube([(x,.408,12.012),(x,1.438,12.14)],.015,METAL,8,'Roof | canopy seam')
    # The ridge is visible in Gao 05. Its right end projects to (737,55)
    # in the 1234 x 910 view at the estimated ridge setback.
    end_l=(-8.03,1.74);end_r=(8.24,1.74)
    ridge_l=(-4.74,5.18);ridge_r=(3.58,5.18)
    roof_panel(b,[end_l,end_r,ridge_r,ridge_l],[12.22,12.22,14.64,14.64],TILE,'Roof | red main garden slope',.115)
    for end,ridge,sign in [(end_l,ridge_l,-1),(end_r,ridge_r,1)]:
        back=(end[0],6.06)
        roof_panel(b,[end,back,ridge],[12.22,12.52,14.64],TILE,'Roof | mitred end hip',.108)
    # Solid sill and returns below the upper glazing, behind the curved masonry.
    house.bar(0,house.width,9.50,10.12,0,.24,LIME,'enclosure sill wall')
    house.bar(0,house.width,10.04,10.17,-.065,.22,STONE,'enclosure sill')
    for x,dx in [(-3.12,.76),(3.12,-.76)]:
        end=Face(b,[x,.72],[x+dx,1.75],'Roof enclosure return')
        end.bar(0,end.width,9.46,10.12,0,.19,BRICK,'low end wall')
    for wing,id in [('left',2),('right',0),('right',3)]:
        x,y=chain[wing][id];b.tube([(x+.11,y-.12,.42),(x+.11,y-.12,11.86)],.041,METAL,8 if lod else 12,'Garden | vertical rain pipe')
def metric_uv(p,scale_x=.92,scale_y=.52):
    xyz=np.asarray(p['vertices']);vs=[];uv=[];tris=[];ref={}
    for old in p['triangles']:
        a,b,c=xyz[list(old)];n=np.cross(b-a,c-a);n=n/np.linalg.norm(n)
        u=(1,0,0) if abs(n[2])>.65 else (-n[1],n[0],0)
        v=(0,1,0) if abs(n[2])>.65 else (0,0,1)
        u=np.asarray(u)/np.linalg.norm(u);key=tuple(u.round(4))+tuple(v);new=[]
        for i in old:
            pair=(i,key)
            if pair not in ref:
                ref[pair]=len(vs);vs.append(tuple(xyz[i]));uv.append((xyz[i]@u/scale_x,xyz[i]@v/scale_y))
            new.append(ref[pair])
        tris.append(tuple(new))
    p.update(vertices=vs,texcoords=uv,triangles=tris)
