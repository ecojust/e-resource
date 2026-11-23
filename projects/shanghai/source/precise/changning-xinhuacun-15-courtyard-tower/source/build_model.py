"""Build the garden-side tower, its north window stack and the visible oblique gallery at Xinhua Village No. 15."""
from pathlib import Path
import argparse,json,math,sys
import numpy as np
from shapely.geometry import box,Polygon
from shapely.ops import unary_union
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder
ID='changning-xinhuacun-15-courtyard-tower'
M='coarse grey-brown pebble dash';B='warm red facing brick';T='terracotta roof'
G='Tower 15 | green-grey glazing';W='Tower 15 | weathered green joinery';P='Tower 15 | warm grey coping';D='Tower 15 | eaves and rainwater iron';V='Tower 15 | pale gallery frames';I='Tower 15 | shaded interior'
PALETTE={m:dict(color=list(rgb),roughness=r) for m,rgb,r in [(M,[.36,.32,.29],.93),(B,[.60,.342,.26],.87),(T,[.52,.256,.182],.84),(P,[.67,.65,.60],.85),(W,[.081,.169,.141],.66),(D,[.175,.17,.15],.71),(V,[.67,.72,.66],.80),(G,[.113,.18,.177],.36),(I,[.092,.087,.075],.93)]};PALETTE[G]['alpha']=.75
MEASURE=HERE.parent/'measurements'
REGISTER=json.loads((MEASURE/'registered-tower.json').read_bytes())
STATIONS=json.loads((MEASURE/'three-tower-stations.json').read_bytes())['stations']
READ=json.loads((MEASURE/'window-readings.json').read_bytes())
g=REGISTER['geometry']
META=dict(id=ID,name='新华村15号院面方塔与斜接侧廊',heritage_id='sh-historic-b3-103',official_id='3M005',address='愚园路1320号新华村15号楼',scope='题注照片中的院面方塔、相接侧廊、四坡短脊瓦顶、近塔烟囱与长宁路599号门内实见的三层背窗。廊体截至相邻山墙遮挡处。',viewer_page='xinhuacun-15-courtyard-tower.html',geometry_license='MIT',texture_license='MIT',photos_embedded=False,photo_source='https://blog.sina.com.cn/s/blog_5d1bdf480101iqnm.html')
if (HERE/'cameras.json').is_file():META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())
def block(b,name,mat,x0,x1,y0,y1,z0,z1):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=name)
def photo_ray(key,uv):
    cam=STATIONS[key];q=np.asarray(cam['R']).T@np.linalg.solve(cam['K'],[*uv,1])
    return np.asarray(cam['C']),q
def on_y(key,uv,depth):
    c,q=photo_ray(key,uv);return c+(depth-c[1])/q[1]*q
def aperture(key,uv,depth):
    points=np.array([on_y(key,p,depth)for p in uv]);xs=np.sort(points[:,0]);zs=np.sort(points[:,2]);return (xs[:2].mean(),zs[:2].mean(),xs[2:].mean(),zs[2:].mean())
def xz(b,poly,y0,y1,mat,label):
    b.prism(poly,-y1,-y0,lambda x,z,n:(x,-n,z),mat,label)
def panel(b,label,rect,y,sign,mat,lod=False,swing=False,bars=3):
    x0,z0,x1,z1=rect;h=z1-z0;dx=(x1-x0)/bars
    for i in range(bars):
        left=x0+i*dx;right=left+dx;angle=math.radians(-28)if swing and i==0 else 0.
        e=np.array([math.cos(angle),sign*math.sin(angle),0]);n=np.array([-sign*math.sin(angle),math.cos(angle),0]);o=np.array([left,y,0])
        def sash(nm,a,c,z,v,th,fill):
            b.box(o+e*((a+c)/2)+[0,0,(z+v)/2],(c-a,th,v-z),fill,basis=[e,n,[0,0,1]],label=label+'/leaf '+str(i+1)+'/'+nm)
        sash('revealed glass',.036,dx-.036,z0+.039,z1-.039,.024,G)
        for side,a,c in [('hinged stile',0,.038),('meeting stile',dx-.038,dx)]:sash(side,a,c,z0,z1,.067,mat)
        for nm,z in [('lower rail',z0+.022),('transom',z0+h*.62),('top rail',z1-.022)]:sash(nm,.038,dx-.038,z-.022,z+.022,.068,mat)
        if not lod and bars>=3:sash('lower glazing bar',.038,dx-.038,z0+h*.32-.011,z0+h*.32+.011,.048,mat)
    if not swing:
        block(b,label+'/inner shadow',I,x0,x1,*sorted((y-sign*.17,y-sign*.20)),z0,z1)
def roof(b,L,R,F,H,e,z,half,material,label):
    cx=(L+R)/2;cy=(F+H)/2
    p=[(L,F,e),(R,F,e),(R,H,e),(L,H,e),(cx-half,cy,z),(cx+half,cy,z)]
    for i,face in enumerate([[0,1,5,4],[1,2,5],[2,3,4,5],[3,0,4]]):
        top=[np.array(p[k])for k in face];verts=top+[x-[0,0,.14]for x in top];n=len(top)
        faces=[list(range(n)),list(range(2*n-1,n-1,-1))]+[[j+n,(j+1)%n+n,(j+1)%n,j]for j in range(n)]
        b.add(verts,faces,material,label+'/pitched plane '+str(i+1))
    b.tube([p[4],p[5]],.080,material,10,label+'/rounded ridge')
    for i,j in [(0,4),(1,5),(2,5),(3,4)]:b.tube([p[i],p[j]],.050,material,8,label+'/hip roll '+str(i+1))
def tower(b,lod):
    a=g['width']/2;d=g['depth'];z=g['wall_top'];base=g['south_z0'];over=g['overhang'];th=.23
    for key,y,side in [('numbered-court',0.,-1),('street-2015',d,1)]:
        ap=[aperture(key,rows,y)for rows in READ[key]['window_outer_TL_TR_BR_BL']]
        if side<0:ap+=[aperture(key,READ[key]['garage'],y)]
        field=box(-a,base,a,z).difference(unary_union([box(*coords)for coords in ap]))
        xz(b,field,*sorted([y,y-side*th]),M,key+'/pierced tower wall')
        for i,rect in enumerate(ap):
            x0,z0,x1,z1=rect
            if i==3:
                for j in range(2):
                    u=x0+(x1-x0)*j/2;v=x0+(x1-x0)*(j+1)/2
                    block(b,'court/green lower door '+str(j+1),W,u+.015,v-.015,.08,.16,z0,z1)
                block(b,'court/light cornice above doors',P,x0-.30,x1+.22,-.10,.26,z1,z1+.48);continue
            panel(b,key+'/window '+str(i+1),rect,y-side*.066,side,W,lod,side<0 and i==0,3 if i==0 or side>0 else 2)
            for drop,label in [(z0-.048,'stone sill'),(z1+.036,'stone head')]:
                block(b,key+'/'+label+' '+str(i+1),P,x0-.088,x1+.082,*sorted([y+side*.11,y-side*.082]),drop-.035,drop+.038)
        for j in (-1,1):
            for k,lo in enumerate(np.arange(base,z,.44)):
                width=(.48 if k%2==0 else .32)
                x0,x1=(a-width,a)if j==1 else(-a,-a+width)
                block(b,key+'/bonded corner '+str(j)+'/'+str(k+1),B,x0,x1,*sorted([y+side*.020,y-side*.024]),lo,min(lo+.431,z))
    for j in (-1,1):
        x0,x1=sorted([j*a,j*(a-th)])
        block(b,'tower/non-windowed return '+str(j),M,x0,x1,th,d-th,base,z)
        for end in [0.,d]:
            for k,lo in enumerate(np.arange(base,z,.44)):
                v=.44 if k%2 else .31
                y0,y1=(.020,v)if end==0 else(d-v,d-.020)
                block(b,'tower/returning quoin '+str(j)+'/'+str(end)+'/'+str(k),B,*sorted([j*(a+.019),j*(a-.021)]),y0,y1,lo,min(lo+.430,z))
    block(b,'tower/dark exposed soffit',D,-a-over,a+over,-over,d+over,z-.035,z+.13)
    roof(b,-a-over,a+over,-over,d+over,z+.14,g['roof_top'],g['ridge_half'],T,'tower hipped roof')
    # The red stack terminates above the courtyard-facing eave just beyond the east plane.
    q=np.array([on_y('numbered-court',pt,2.85)for pt in READ['numbered-court']['tower_chimney_TL_TR']]);x=q[:,0].mean();h=q[:,2].mean();w=abs(q[1,0]-q[0,0])
    block(b,'adjacent courtyard chimney',B,x-w*.46,x+w*.46,2.54,3.39,8.6,h-.14)
    block(b,'adjacent chimney/projecting stone cap',B,x-w*.53,x+w*.53,2.48,3.45,h-.18,h)
    for j in [-1,1]:
        px=a*j+(.068*j);b.tube([(px,-.018,base+.12),(px,-.018,z-.14),(px,-.20,z-.02),(px,-over*.82,z+.12)],.047,D,6 if lod else 10,'tower/downpipe '+str(j))
def gallery(b,lod):
    near=g['width']/2;origin=np.array([near,.85,0]);t=np.array([1.,.59004,0]);t/=np.linalg.norm(t);n=np.array([-t[1],t[0],0]);up=np.array([0,0,1])
    def local(uv,offset=0.):
        c,q=photo_ray('numbered-court',uv);u=c+(offset+(origin-c)@n)/(q@n)*q;return (u-origin)@t,u[2]
    def beam(name,mat,l,r,front,back,lo,hi):
        if r<=l or back<=front or hi<=lo:return
        b.box(origin+t*((l+r)/2)+n*((front+back)/2)+up*((lo+hi)/2),(r-l,back-front,hi-lo),mat,basis=[t,n,up],label='court gallery/'+name)
    end=local((201,137))[0]
    for z,name in [(2.12,'lower floor'),(5.62,'upper gallery floor'),(8.68,'eaves and soffit')]:
        beam(name,P,0,end,-.135,2.31,z-.205,z)
    for j,pix in enumerate([88,156,199]):
        u=local((pix,137))[0];beam('facing brick support '+str(j+1),B,max(0,u-.20),min(end,u+.20),-.035,.31,2.12,8.64)
    for name,lo,hi in [('lower',2.12,3.0),('upper',5.62,6.93)]:
        beam(name+' coping rail',P,0,end,-.12,.17,hi-.102,hi);beam(name+' foot rail',P,0,end,-.06,.13,lo+.055,lo+.165)
        for j,u in enumerate(np.arange(.27,end-.11,.34)):
            beam(name+' recessed baluster '+str(j+1),P,u-.046,u+.046,-.006,.086,lo+.16,hi-.10)
    # Three retained groups on the enclosed upper gallery are separately read on the photograph.
    for name,z0,z1,glass in [('upper',6.95,8.64,[(98,113),(118,149),(186,200)]),('lower',2.50,4.93,[(92,111),(132,155)])]:
        gaps=[(max(.05,local((u,119 if name=='upper'else 159),1.38)[0]),min(end-.05,local((v,119 if name=='upper'else 159),1.38)[0]))for u,v in glass]
        last=0.
        for j,(l,r)in enumerate(gaps):
            if r<l+.18:continue
            beam(name+' solid spandrel '+str(j),M,last,l,1.38,1.6,z0,z1)
            beam(name+' inset glass '+str(j),G,l,r,1.44,1.466,z0,z1)
            cnt=max(1,round((r-l)/(.36 if name=='upper'else .46)))
            for k in range(cnt+1):
                u=l+(r-l)*k/cnt;beam(name+' glazing stile '+str(j)+'/'+str(k),V if name=='upper'else W,u-.023,u+.023,1.396,1.463,z0,z1)
            for h in np.linspace(z0+.025,z1-.025,3 if lod else 4):beam(name+' glazing rail '+str(j),V if name=='upper'else W,l,r,1.395,1.461,h-.018,h+.018)
            last=r
        beam(name+' wall to observed end',M,last,end,1.38,1.60,z0,z1)
    for lo,hi in [(g['south_z0'],2.5),(4.93,6.95)]:beam('rear wall band',M,0,end,1.38,1.6,lo,hi)
    a=origin+t*.01-n*.13+up*8.69;b0=origin+t*end-n*.13+up*8.69
    c=b0+n*2.66+up*2.90;d=a+n*2.66+up*2.90
    top=[a,b0,c,d];b.add(top+[p-up*.16 for p in top],[[0,1,2,3],[7,6,5,4],[4,5,1,0],[5,6,2,1],[6,7,3,2],[7,4,0,3]],T,'court gallery/visible sloping red roof')
    beam('outer grey drip edge',D,0,end,-.16,-.06,8.56,8.70)
def add_building(builder,lod=False):
    tower(builder,lod);gallery(builder,lod)
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--lod',action='store_true');args=parser.parse_args()
    b=Builder(PALETTE);add_building(b,args.lod);q=b.save(args.output,META);print(q['sha256'],q['parts'],q['triangles'])
if __name__=='__main__':main()
