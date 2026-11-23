"""Photo-constrained garden wing, return, dormers and east chimney of 236 Xinhua Road."""
import argparse,json,math,os,sys
from pathlib import Path
import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
COMMON=Path('source/precise/hongkou-general-post-office/source/common')
CROWN=Path('source/precise/hongkou-tanggu-road-apartment-dated-crown/source')
roots=list(HERE.parents)
if os.environ.get('E_RESOURCE_SHANGHAI'):roots.insert(0,Path(os.environ['E_RESOURCE_SHANGHAI']))
ROOT=next((p for p in roots if (p/COMMON/'photo_architecture.py').is_file() and (p/CROWN/'crown_builder.py').is_file()),None)
if ROOT is None:raise ImportError('Install the two shared architecture helpers in the project tree or set E_RESOURCE_SHANGHAI.')
sys.path[:0]=[str(ROOT/COMMON),str(ROOT/CROWN)]
from crown_builder import CrownBuilder
ID='changning-xinhua-236-english-garden-villa'
META=dict(id=ID,name='新华路236号住宅木格山墙、双老虎窗与砖烟囱',heritage_id='sh-historic-b3-113',protection_number='3M015',address='上海市长宁区新华路236号',unit='metre',viewer_page='xinhua-236-english-garden-villa.html',photos_embedded=False,camera_views=json.loads((HERE/'cameras.json').read_text()))
TILE='Salmon flat machine tile';BRICK='Weathered chimney brick';PLASTER='Cream textured exterior plaster';BASE='Ochre garden wall base';WOOD='Blackened timber frame';SASH='Deep green steel sash';GLASS='Recessed blue green glass';RIDGE='Weathered clay ridge cap';STONE='Stone window sill'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in [(TILE,[1,1,1],.87),(BRICK,[1,1,1],.88),(PLASTER,[.87,.84,.74],.94),(BASE,[.60,.39,.28],.90),(WOOD,[.17,.155,.115],.84),(SASH,[.20,.235,.195],.63),(GLASS,[.28,.36,.35],.28),(RIDGE,[.68,.43,.28],.85),(STONE,[.66,.655,.60],.91)]}
PALETTE[TILE]['texture']=str(HERE/'salmon-plain-roof-tiles.png')
PALETTE[BRICK]['texture']=str(HERE/'clinker-chimney-running-bond.png')

def plate(b,orient,polygon,level,t,material,label):
    # Garden walls face -Y. Return walls face +X and are expressed in depth and height.
    if polygon.is_empty:return
    if orient=='y':b.prism(polygon,-level-t,-level,lambda u,z,v:(u,-v,z),material,label)
    else:b.prism(polygon,level-t,level,lambda d,z,v:(v,d,z),material,label)

def band(b,orient,level,p,q,width,material,label,thick=.065):
    x,z=p;u,v=q;dx=u-x;dz=v-z;ln=math.hypot(dx,dz);hx=-dz/ln*width/2;hz=dx/ln*width/2
    poly=Polygon([(x+hx,z+hz),(u+hx,v+hz),(u-hx,v-hz),(x-hx,z-hz)])
    plate(b,orient,poly,level,thick,material,label)

def wall(b,orient,face,rim,windows,mat,label,lod):
    outer=rim.difference(unary_union([box(*r[:4]) for r in windows]))
    plate(b,orient,outer,face,.20,mat,label+' plaster and jambs')
    sign=1 if orient=='y' else -1
    for name,r in enumerate(windows,1):
        x,z,u,v,cols,rows=r;nm=label+' window '+str(name)
        plate(b,orient,box(x,z,u,v),face+sign*.15,.035,GLASS,nm+' recessed glass')
        if lod:
            frame=box(x-.029,z-.029,u+.029,v+.029).difference(box(x+.029,z+.029,u-.029,v-.029))
            plate(b,orient,frame,face+sign*.064,.059,SASH,nm+' continuous distance frame')
        else:
            for i,(a,c) in enumerate([((x,z),(x,v)),((u,z),(u,v)),((x,z),(u,z)),((x,v),(u,v))]):
                band(b,orient,face+sign*.064,a,c,.058,SASH,nm+' perimeter '+str(i))
        for i in range(1,cols):
            if lod and cols>=4 and i%2:continue
            a=x+(u-x)*i/cols;band(b,orient,face+sign*.095,(a,z),(a,v),.045,SASH,nm+' vertical '+str(i))
        for i in range(1,rows):
            if lod and rows>2 and i%2:continue
            a=z+(v-z)*i/rows;band(b,orient,face+sign*.097,(x,a),(u,a),.034,SASH,nm+' horizontal '+str(i))
        band(b,orient,face-sign*.075,(x-.07,z-.065),(u+.07,z-.065),.09,STONE,nm+' sill',.21)

def left_wing(b,lod):
    left=-5.42;right=-.10;front=.13;back=9.40
    rim=Polygon([(left,3.55),(right,3.55),(right,6.41),(-2.81,10.08),(left,6.41)])
    wall(b,'y',front,rim,[(-4.94,4.62,-.54,6.13,7,3),(-3.34,7.30,-2.11,8.64,3,2)],PLASTER,'garden timber gable',lod)
    for i,(p,q,width) in enumerate([((left,6.42),(-2.81,10.09),.145),((-2.81,10.09),(right,6.42),.145),((left,6.40),(right,6.40),.18),((left,3.61),(right,3.61),.12),((-2.81,8.68),(-2.81,9.84),.11),((-4.55,6.46),(-4.55,7.58),.10),((-1.07,6.46),(-1.07,7.64),.11),((-4.15,6.50),(-3.34,7.65),.11),((-2.11,7.60),(-1.36,6.47),.11)]):
        band(b,'y',front-.102,p,q,width,WOOD,'gable timbers '+str(i))
    for i,x in enumerate([-5.28,-4.35,-3.40,-2.5,-1.50,-.32]):
        band(b,'y',front-.067,(x,3.65),(x,4.63),.108,WOOD,'veranda lower upright '+str(i))
    wall(b,'y',front+.07,box(left,.04,right,3.55),[(-4.74,1.02,-3.14,2.67,3,2),(-1.96,.94,-.88,2.70,2,2)],PLASTER,'gable ground floor',lod)
    wall(b,'x',-.12,box(.15,3.52,2.52,6.42),[(.40,4.70,2.25,6.15,3,2)],PLASTER,'veranda side return',lod)
    for i,y in enumerate([.20,.95,1.74,2.41]):
        band(b,'x',-.035,(y,3.52),(y,6.36),.115,WOOD,'veranda return post '+str(i))
    for i,z in enumerate([3.60,4.70,6.35]):
        band(b,'x',-.035,(.14,z),(2.49,z),.135,WOOD,'veranda return rail '+str(i))
    wall(b,'x',-.14,box(.15,.04,2.47,3.52),[(.65,.93,1.60,2.60,2,2)],BASE,'return at garden base',lod)
    plate(b,'x',box(front,.04,back,6.38),left,.12,PLASTER,'screened outer side, plain closure')
    plate(b,'y',rim.union(box(left,.04,right,3.60)),back-.10,.12,PLASTER,'rear gable, plain closure')

def principal(b,lod):
    wall(b,'y',2.53,box(-.08,3.53,4.32,6.42),[(.73,4.49,3.11,6.02,3,4)],PLASTER,'garden central upper bay',lod)
    wall(b,'y',2.59,box(-.08,.04,4.30,3.53),[(.94,1.0,1.90,2.80,2,2)],PLASTER,'garden central lower bay',lod)
    for x in [-.04,4.15]:
        band(b,'y',2.51,(x,.07),(x,3.51),.19,BRICK,'central lower brick pier '+str(x))
    band(b,'y',2.44,(-.04,3.54),(4.26,3.54),.125,STONE,'garden intermediate string course',.22)
    cheek=Polygon([(2.54,.05),(10.62,.05),(10.62,6.38),(6.37,10.35),(2.54,6.38)])
    wall(b,'x',4.32,cheek,[(3.46,4.8,4.22,5.91,2,2),(5.87,6.64,6.50,8.0,2,2)],PLASTER,'east gable adjacent to chimney',lod)
    plate(b,'y',box(-2.86,.05,4.30,6.38),10.55,.12,PLASTER,'main rear, plain closure')
    # Lower return is recessed behind the chimney, with an independent lower roof line.
    g=Polygon([(5.05,.05),(8.68,.05),(8.68,5.76),(6.92,8.17),(5.05,5.76)])
    wall(b,'x',6.46,g,[(6.90,3.96,8.43,5.42,2,2)],PLASTER,'low east gable return',lod)
    wall(b,'y',5.07,box(4.36,.05,6.43,5.74),[(4.72,3.98,5.92,5.22,2,2)],PLASTER,'recessed garden wing front',lod)
    plate(b,'y',box(4.35,.05,6.42,5.73),8.52,.12,PLASTER,'hidden low wing rear')
    plate(b,'x',g,4.40,.12,PLASTER,'screened low wing junction')
    for x in [4.60,5.30]:
        band(b,'y',4.91,(x,.06),(x,2.34),.13,BRICK,'entrance pier '+str(x),.31)
    plate(b,'y',box(4.48,2.33,5.44,2.58),4.87,.55,BRICK,'entrance canopy front lip')
    # The original field note identifies red brick; the flue stands above the east gable peak.
    def shaft(x0,x1,y0,y1,z0,z1,material,label):
        b.prism(box(x0,y0,x1,y1),z0,z1,lambda x,y,z:(x,y,z),material,label)
    shaft(4.33,4.98,3.31,4.32,.05,6.62,BRICK,'east chimney broad lower stack')
    b.prism(Polygon([(3.31,6.62),(4.32,6.62),(4.29,7.85),(3.58,7.85)]),4.33,4.98,lambda y,z,x:(x,y,z),BRICK,'chimney sloped shoulder')
    shaft(4.33,4.98,3.58,4.29,7.85,11.42,BRICK,'exposed tall flue')
    shaft(4.27,5.04,3.53,4.35,11.42,11.58,BRICK,'stepped chimney cap')
    shaft(4.33,4.98,3.60,4.29,11.58,11.63,STONE,'chimney weathering')

def roofs(b,lod):
    # Combine intersecting roof-plane footprints. A lower pitch stops at the valley of its neighbour.
    slopes=[]
    def plane(name,xy,heights):
        coeff=np.linalg.solve([[x,y,1.]for x,y in xy[:3]],heights[:3])
        assert all(abs(coeff@[x,y,1]-z)<1e-6 for (x,y),z in zip(xy,heights))
        slopes.append((name,Polygon(xy),coeff))
    def pitch(name,x0,xm,x1,y0,y1,eave,top):
        plane(name+' west slope',[(x0,y0),(xm,y0),(xm,y1),(x0,y1)],[eave,top,top,eave])
        plane(name+' east slope',[(xm,y0),(x1,y0),(x1,y1),(xm,y1)],[top,eave,eave,top])
    pitch('garden projecting gable',-5.59,-2.81,.10,-.12,9.65,6.41,10.20)
    plane('long garden pitch',[(-2.94,2.30),(4.53,2.30),(4.53,6.40),(-2.94,6.40)],[6.40,6.40,10.45,10.45])
    plane('long rear pitch',[(-2.94,6.40),(4.53,6.40),(4.53,10.90),(-2.94,10.90)],[10.45,10.45,6.4,6.4])
    plane('lower garden pitch',[(4.10,4.89),(6.64,4.89),(6.64,6.92),(4.10,6.92)],[5.79,5.79,8.34,8.34])
    plane('lower rear pitch',[(4.10,6.92),(6.64,6.92),(6.64,8.83),(4.10,8.83)],[8.34,8.34,5.79,5.79])
    # The small projecting dormer looks east. The long three-light dormer faces the garden.
    plane('short dormer roof',[(-1.87,1.0),(-.69,1.0),(-.69,2.37),(-1.87,2.37)],[9.15,8.64,8.64,9.15])
    plane('long dormer roof',[(.71,3.02),(3.45,3.02),(3.45,4.75),(.71,4.75)],[8.71,8.71,9.16,9.16])
    def higher(a,b,c):
        edge=[(-40,-40),(40,-40),(40,40),(-40,40)];poly=[]
        for p,q in zip(edge,edge[1:]+edge[:1]):
            u=a*p[0]+b*p[1]+c;v=a*q[0]+b*q[1]+c
            if u>=0:poly.append(p)
            if u*v<0:poly.append(tuple(p[j]+(q[j]-p[j])*u/(u-v) for j in (0,1)))
        return Polygon(poly) if len(poly)>=3 else Polygon()
    for i,(name,plan,c) in enumerate(slopes):
        exposed=plan
        for j,(_,other,oc) in enumerate(slopes):
            if i!=j and np.linalg.norm(oc-c)>1e-5:
                exposed=exposed.difference(other.intersection(higher(*(oc-c))))
        if exposed.is_empty:continue
        b.prism(set_precision(exposed,.0001),-.11,0,lambda x,y,t:(x,y,c@[x,y,1.]+t),TILE,name)
    for name,p,q in [('front projecting ridge',(-2.81,-.12,10.24),(-2.81,5.98,10.24)),('back projecting ridge',(-2.81,6.98,10.24),(-2.81,9.65,10.24)),('main high ridge',(-2.94,6.4,10.49),(4.53,6.4,10.49)),('recessed lower ridge',(4.13,6.92,8.37),(6.64,6.92,8.37))]:
        b.tube([p,q],.075,RIDGE,6 if lod else 10,name)
    def dormer(label,orient,level,a,horizontal_end,zmin,zmax,near,far,side_profile,cols):
        wall(b,orient,level,box(a,zmin,horizontal_end,zmax),[(a+.14,zmin+.13,horizontal_end-.14,zmax-.11,cols,2)],PLASTER,label,lod)
        for loc in [a+.065,horizontal_end-.065]:
            if orient=='y':plate(b,'x',Polygon(side_profile),loc,.09,PLASTER,label+' triangular cheek '+str(loc))
            else:plate(b,'y',Polygon(side_profile),loc,.09,PLASTER,label+' triangular cheek '+str(loc))
    dormer('short dormer front','x',-.77,1.03,2.33,7.39,8.58,-1.87,-.77,[(-.77,7.39),(-1.87,8.95),(-1.87,9.06),(-.77,8.57)],2)
    dormer('long dormer front','y',3.11,.73,3.40,7.57,8.61,3.11,4.75,[(3.11,7.55),(4.75,8.88),(4.75,9.06),(3.11,8.61)],4)

def build(lod=False):
    b=CrownBuilder(PALETTE);left_wing(b,lod);principal(b,lod);roofs(b,lod);return b

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--lod',action='store_true')
    args=p.parse_args();print(build(args.lod).save(args.output,META)['sha256'])
