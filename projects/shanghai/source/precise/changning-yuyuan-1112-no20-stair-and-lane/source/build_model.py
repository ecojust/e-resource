"""The numbered northern house: courtyard elevation and independently registered stair flight."""
from pathlib import Path
import sys,json,argparse,math
import numpy as np
from shapely.geometry import Polygon,box,LineString,Point
from shapely.ops import unary_union
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from photo_architecture import Builder
from crown_builder import CrownBuilder
import finishes
ID='changning-yuyuan-1112-no20-stair-and-lane'
META=dict(id=ID,name='愚园路1112弄20号北栋巷面与室内石阶',address='长宁区愚园路1112弄20号',heritage_id='sh-historic-b3-107',protection_number='3M009',geometry_license='MIT',photos_embedded=False,viewer_page='yuyuan-1112-no20-stair-and-lane.html',scope='2015年11月16日20号门牌、同址临弄立面与室内首跑石阶。立面和室内采用各自摄影机；照片间没有公共基准，室内组和立面的相对距离为展示安排。')
if (HERE/'cameras.json').is_file():META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())
M=HERE.parent/'measurements';views=json.loads((M/'two-stations.json').read_bytes());points=json.loads((M/'visible-openings.json').read_bytes());stair=json.loads((M/'visible-stair.json').read_bytes())
PL,TR,WOOD,GREY=finishes.STEMS;FRAME='twenty | chalk painted sash';GL='twenty | mottled grey glazing';DARK='twenty | recess';CANVAS='twenty | indigo cloth';BRONZE='twenty | dull metal';GREEN='twenty | faded green letter box';CREAM='twenty | cream enamel';RUST='twenty | red brown notice board';PAST='twenty | cream interior wall';PAN='twenty | brown interior dado';JOIN='twenty | grey masonry joints'
GROOVE='twenty | honed nosing rebate'
PALETTE=dict(finishes.PALETTE)
for m,c,r in [(GROOVE,[.17,.17,.155],.92),(FRAME,[.57,.60,.52],.72),(GL,[.13,.19,.18],.32),(DARK,[.054,.065,.06],.88),(CANVAS,[.115,.137,.215],.91),(BRONZE,[.22,.225,.2],.71),(GREEN,[.13,.285,.225],.68),(CREAM,[.71,.70,.61],.68),(RUST,[.34,.17,.137],.77),(PAST,[.55,.52,.465],.91),(PAN,[.39,.27,.2],.78),(JOIN,[.35,.35,.31],.91)]:PALETTE[m]={'color':c,'roughness':r}
class SurfaceBuilder(CrownBuilder):
    def add(self,vertices,faces,material='limestone',label='detail'):
        super().add(vertices,faces,material,label)
        if material in finishes.STEMS:finishes.metric_uv(self.parts[-1])
    def save(self,path,metadata=None):
        Builder.save(self,path,metadata);return finishes.writer.embed_normals(path)
def at(view,uv,axis,value):
    P=np.array(views[view]['P']);indices=[j for j in range(3)if j!=axis]
    A=np.column_stack((P[:,indices],P[:,3]+P[:,axis]*value));q=np.linalg.solve(A,[*uv,1]);a=np.zeros(3);a[axis]=value;a[indices]=q[:2]/q[2];return a
def xz(uv,depth=0):return at('photo-lane',uv,1,depth)[[0,2]]
def front(b,poly,y0,y1,material,label):
    if not poly.is_empty:b.prism(poly,-y1,-y0,lambda x,z,d:(x,-d,z),material,label)
def block(b,x0,x1,y0,y1,z0,z1,m,l):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),m,label=l)
def long_box(b,x0,x1,y0,y1,z0,z1,mat,label):
    # Short wall strips preserve open-near-plane photographic views in the offline triangle rasterizer.
    n=max(1,int(np.ceil((y1-y0)/.52)))
    ys=np.linspace(y0,y1,n+1);verts=[];faces=[]
    for yy in ys:verts.extend([(x0,yy,z0),(x1,yy,z0),(x1,yy,z1),(x0,yy,z1)])
    faces.append((0,1,2,3));end=4*n;faces.append((end+3,end+2,end+1,end))
    for i in range(n):
        for j in range(4):
            a=4*i+j;c=4*i+(j+1)%4;faces.append((a,a+4,c+4,c))
    b.add(verts,faces,mat,label)
def lane(b,lod):
    shell=Polygon([xz(uv)for uv in points['elevation_outline']]).buffer(0)
    apertures={}
    for k,r in points['windows'].items():
        # Each rectangular sash is analysed on the façade plane from the original four jamb corners.
        q=np.array([xz(uv)for uv in r['points']]);x0=(q[0,0]+q[3,0])/2;x1=(q[1,0]+q[2,0])/2;z0=(q[2,1]+q[3,1])/2;z1=(q[0,1]+q[1,1])/2
        apertures[k]=box(x0,z0,x1,z1)
    holes=unary_union(list(apertures.values()));wall=shell.difference(holes)
    xmin,zmin,xmax,zmax=shell.bounds
    front(b,wall.intersection(box(xmin-1,.70,xmax+1,zmax+1)),0,.31,PL,'lane/pale wall with through openings')
    front(b,wall.intersection(box(xmin-1,zmin-1,xmax+1,.70)),.001,.305,GREY,'lane/dark plinth')
    def bands(marks,h,d,m,key):
        pts=[xz(v)for v in marks];geom=LineString(pts).buffer(h/2,cap_style='flat',join_style='mitre')
        front(b,geom.intersection(shell.buffer(.12)), -d,-.006,m,key)
    for j,line in enumerate(points['wall_bands']):
        bands(line,[.065,.088,.145][j],[.055,.080,.12][j],GREY,'lane/horizontal course '+str(j+1))
    bands(points['sill_controls'],.14,.12,GREY,'lane/curved crown moulding')
    bands([(41,192),(92,123),(98,104),(105,84),(117,68),(125,64),(132,68)],.052,.16,JOIN,'lane/inner curve on the rounded crown')
    for k,hole in apertures.items():
        r=points['windows'][k];x0,z0,x1,z1=hole.bounds
        if r.get('door'):
            frame=hole.difference(box(x0+.053,z0-.01,x1-.053,z1-.064));front(b,frame,.09,.14,FRAME,k+'/jamb');front(b,box(x0+.052,z0+.011,x1-.052,z1-.068),.255,.275,DARK,k+'/deep opening')
            continue
        inset=hole.buffer(-.048,join_style='mitre');front(b,hole.difference(inset),.086,.16,FRAME,k+'/rebated casing')
        inner=inset.bounds
        bars=[];mid=(x0+x1)/2;bars.append(box(mid-.017,z0,mid+.017,z1))
        for f in r['rows']:
            z=z0+(z1-z0)*f;bars.append(box(x0,z-.018,x1,z+.018))
        grid=inset.intersection(unary_union(bars));front(b,grid,.122,.15,FRAME,k+'/mullions')
        for n,pane in enumerate(getattr(inset.difference(grid),'geoms',[inset.difference(grid)])):front(b,pane,.176,.186,GL,k+'/light '+str(n+1))
        front(b,box(x0-.075,z0-.078,x1+.075,z0-.006),-.108,-.003,GREY,k+'/sill')
    for j,uv in enumerate(points['exterior_downpipes']):
        a,c=[at('photo-lane',v,1,-.103)for v in uv];b.tube([a,c],.049,FRAME,8 if lod else 14,'lane/white downpipe '+str(j+1))
        for step in (.18,.49,.80):
            p=a*(1-step)+c*step;b.tube([p-[0,0,.019],p+[0,0,.019]],.061,GREY,8,'lane/downpipe collar '+str((j,step)))
    for k in points['fabric_hoods']:
        x0,z0,x1,z1=apertures[k].bounds;run=.47 if k=='first-middle' else .40;apron=.30;dr=.27
        b.prism(LineString([(-.045,z1+.080),(-run,z1-dr),(-run,z1-dr-apron)]).buffer(.018,cap_style='flat',join_style='mitre'),x0-.106,x1+.106,lambda y,z,x:(x,y,z),CANVAS,k+'/sloping cloth and hanging valance')
        for x in (x0-.063,x1+.063):b.tube([(x,-.025,z1-.52),(x,-run+.01,z1-dr-.055)],.014,BRONZE,6,k+'/side bracket')
    no=Polygon([xz(uv)for uv in points['lower_shuttered_notice_case']]);front(b,no,-.092,-.013,RUST,'lane/red-brown display cabinet')
    front(b,no.buffer(.042,join_style='mitre').difference(no),-.130,-.026,WOOD,'lane/cabinet rim')
    for u,v,w,h in [(109,325,.58,.39),(107,170,.56,.35),(187,117,.60,.37)]:
        x,z=xz((u,v));block(b,x-w/2,x+w/2,-.37,-.04,z-h/2,z+h/2,CREAM,'lane/condenser cabinet '+str(u))
        if not lod:
            for k in range(5):
                zz=z-h*.26+k*h*.11;block(b,x-w*.34,x+w*.34,-.383,-.371,zz-.006,zz+.006,BRONZE,'lane/vent grate '+str((u,k)))
def stairs(b,lod):
    q=views['photo-stair']['readings'];dx,dy,_=q['study_translation'];run,rise=q['run_m'],q['rise_m'];count=len(q['right_ends']);lo,hi=dx-.65,dx+.55
    # Construct the serrated stone flight from a single closed cross-section. Individual noses project only beyond the core.
    top=[(dy,0),(dy,rise)]
    for j in range(count):
        yy=dy+(j+1)*run;zz=(j+1)*rise;top.append((yy,zz))
        if j<count-1:top.append((yy,zz+rise))
    top.append((dy+count*run,0));b.prism(Polygon(top),lo,hi,lambda y,z,x:(x,y,z),TR,'stair/continuous fourteen-step stone flight')
    for j in range(count):
        y=dy+j*run; z=(j+1)*rise
        # The archival lower three steps show two narrow tooling lines along each forward edge.
        for t in ((.013,.034) if not lod else (.018,)):
            block(b,lo+.008,hi-.008,y+t,y+t+.012,z+.0008,z+.0021,GROOVE,'stair/tread front groove edge '+str((j+1,t)))
        if not lod:
            block(b,lo+.008,hi-.008,y-.013,y+.0005,z-.022,z-.004,TR,'stair/eased nosing '+str(j+1))
    long_box(b,lo-.04,hi+.13,dy-2.7,dy-.001,-.09,-.002,TR,'stair/entry landing')
    long_box(b,lo-.12,lo-.008,dy-.25,dy+count*run+.12,0,3.65,PAST,'stair/left wall')
    rx=hi+.085
    long_box(b,rx,rx+.115,dy-2.5,dy+count*run+.18,0,3.6,PAST,'stair/right wall')
    block(b,rx-.014,rx-.001,dy-2.5,dy+.055,0,.9,PAN,'stair/brown lower wall panel')
    a=at('photo-stair',(210,230),0,hi+.006);e=at('photo-stair',(97,83),0,hi+.006)
    if e[1]<a[1]:a,e=e,a
    rail=lambda y: a[2]+(y-a[1])*(e[2]-a[2])/(e[1]-a[1])
    y0=dy+.02;y1=dy+(count-.35)*run
    b.tube([(hi+.006,y0,rail(y0)),(hi+.006,y1,rail(y1))],.039,WOOD,8 if lod else 14,'stair/continuous timber handrail')
    b.tube([(hi+.006,dy-.25,rail(y0)),(hi+.006,y0,rail(y0))],.039,WOOD,8,'stair/level handrail return')
    for j in range(count):
        y=dy+(j+.18)*run;z=(j+1)*rise;w=.044 if j in (0,count-1) else .029
        block(b,hi-.01-w,hi-.01+w,y-w,y+w,z-.006,rail(y)-.015,WOOD,'stair/square timber baluster '+str(j+1))
    for j,(x0,y0,x1,y1,color)in enumerate(stair['right_wall_cases']):
        uv=[(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
        shell=Polygon([at('photo-stair',p,0,rx-.103)[1:] for p in uv]);m={'green':GREEN,'brown':WOOD,'pale':CREAM,'charcoal':DARK}[color]
        def side(poly,x0,x1,mat,label):b.prism(poly,x0,x1,lambda y,z,x:(x,y,z),mat,label)
        side(shell,rx-.135,rx-.018,m,'stair/mailbox '+str(j+1))
        yy0,zz0,yy1,zz1=shell.bounds;slot=shell.intersection(box(yy0+(yy1-yy0)*.19,zz1-.042,yy1-(yy1-yy0)*.16,zz1-.025))
        side(slot,rx-.140,rx-.136,DARK,'stair/letter slot '+str(j+1))
        if j in (0,1,2,3,4):
            card=shell.intersection(box(yy0+.14*(yy1-yy0),zz0+.28*(zz1-zz0),yy0+.70*(yy1-yy0),zz0+.67*(zz1-zz0)))
            side(card,rx-.142,rx-.136,CREAM,'stair/plain paper label '+str(j+1))
    # The green box and the upper group are fixed against the brown board above the dado.
    long_box(b,rx-.052,rx-.022,dy-2.14,dy-.10,.895,2.3,WOOD,'stair/letter case backboard')
    block(b,lo-.115,rx+.115,dy+count*run+.11,dy+count*run+.22,0,3.62,PAST,'stair/landing end wall')
def build(lod=False):
    b=SurfaceBuilder(PALETTE);lane(b,lod);stairs(b,lod);return b
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--lod',action='store_true');args=p.parse_args();print(build(args.lod).save(args.output,META)['sha256'])
