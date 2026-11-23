"""Garden-facing gable, attached shed dormer and intersecting tiled roofs at Xinhua Road 231."""
import argparse
import json
import math
import os
from pathlib import Path
import sys
import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
SHARED=Path('source/precise/hongkou-general-post-office/source/common')
CROWN=Path('source/precise/hongkou-tanggu-road-apartment-dated-crown/source')
roots=list(HERE.parents)
if configured:=os.environ.get('E_RESOURCE_SHANGHAI'):
    roots.insert(0,Path(configured).resolve())
PROJECT=next((p for p in roots if (p/SHARED/'photo_architecture.py').is_file() and (p/CROWN/'crown_builder.py').is_file()),None)
if PROJECT is None:
    raise ImportError('Set E_RESOURCE_SHANGHAI to the project directory containing both shared geometry helpers.')
sys.path[:0]=[str(PROJECT/SHARED),str(PROJECT/CROWN)]
from crown_builder import CrownBuilder

ID='changning-xinhua-231-rong-garden-roof'
META=dict(id=ID,name='新华路231号住宅花园侧木构山墙与交叉瓦顶',heritage_id='sh-historic-b3-110',
          protection_number='3M012',address='长宁区新华路231号',unit='metre',
          scope='Garden-facing gable, shed dormer and roof envelope. Rear and lower exterior are incomplete.',
          camera_views=json.loads((HERE/'cameras.json').read_text()))
TILE='mottled clay tiles';WOOD='dark timber';WHITE='cool lime infill';BRICK='weathered warm brick'
GLASS='shaded window';EDGE='clay ridge and verge';SHADOW='eaves liner'
PALETTE={n:dict(color=c,roughness=r) for n,c,r in [
 (TILE,[1,1,1],.86),(WOOD,[.175,.114,.086],.83),(WHITE,[.76,.785,.755],.94),
 (BRICK,[.57,.34,.21],.89),(GLASS,[.19,.27,.29],.27),(EDGE,[.49,.27,.195],.78),
 (SHADOW,[.26,.21,.185],.9)]}
PALETTE[TILE]['texture']=str(HERE/'garden-roof-tiles.png')

def face(b,shape,depth,thickness,mat,name):
    b.prism(shape,-depth-thickness,-depth,lambda x,z,t:(x,-t,z),mat,name)

def wall(b,rim,openings,depth,mat,name):
    cuts=[box(*bounds) for bounds in openings]
    face(b,rim.difference(unary_union(cuts)),depth,.25,mat,name)
    for j,(x0,z0,x1,z1) in enumerate(openings,1):
        face(b,box(x0,z0,x1,z1),depth+.19,.035,GLASS,f'{name} glass {j}')

def beam(b,x1,z1,x2,z2,y,width,depth,name):
    dx,dz=x2-x1,z2-z1;length=math.hypot(dx,dz)
    b.box(((x1+x2)/2,y,(z1+z2)/2),(length,depth,width),WOOD,
          [(dx/length,0,dz/length),(0,1,0),(-dz/length,0,dx/length)],name)

def garden_front(b,lod):
    left,right=-8.65,-2.95
    front=-5.86;peak=(left+right)/2
    mid=3.35;eave=6.54;top=9.54
    wall(b,box(left,0,right,mid),[(-8.04,1.02,-6.97,2.66),(-6.56,1.02,-5.40,2.66),(-4.96,.95,-3.77,2.7)],front,BRICK,'projecting gable red brick base')
    upper=Polygon([(left,mid),(right,mid),(right,eave),(peak,top),(left,eave)])
    wall(b,upper,[(-7.48,4.69,-4.17,6.16)],front,WHITE,'pale infill in projecting gable')
    for j,z in enumerate([3.42,4.50,6.22]):
        beam(b,left,z,right,z,front-.036,.16,.12,f'gable horizontal timber {j+1}')
    for j,x in enumerate([left+.11,-7.52,-6.48,-5.30,-4.14,right-.11]):
        h=eave+(top-eave)*max(0,1-abs(x-peak)/((right-left)/2))-.14
        beam(b,x,mid+.03,x,h,front-.05,.15,.13,f'gable upright {j+1}')
    beam(b,left-.04,eave,peak,top+.05,front-.07,.19,.16,'gable left verge')
    beam(b,peak,top+.05,right+.04,eave,front-.07,.19,.16,'gable right verge')
    if not lod:
        for j,x in enumerate([-7.01,-6.00,-4.72]):
            beam(b,x,4.75,x,6.13,front+.13,.045,.06,f'upper window mullion {j+1}')
    # The photograph shows only the upper garden wall to the right; shade hides the lower elevation.
    wall(b,box(-2.94,3.15,5.34,6.20),[(-2.33,4.46,-.92,5.43),(.79,3.73,2.18,5.52),(3.59,4.43,4.72,5.34)],-3.91,WHITE,'set-back garden wall')
    face(b,box(-2.94,3.05,5.34,3.23),-4.00,.17,BRICK,'garden storey band')

def roof_supports(b):
    # Use a plain return wherever trees prevent a reading of the masonry treatment.
    # Front openings have independent recessed panes in garden_front().
    def yz(shape,x,material,name):
        b.prism(shape,x-.105,x+.105,lambda y,z,t:(t,y,z),material,name)
    yz(box(-5.82,0,-3.84,6.42),-3.03,WHITE,'plain return at garden projection')
    yz(box(-5.82,0,-3.84,6.42),-8.54,BRICK,'plain brick west return at garden projection')
    face(b,box(-2.94,0,5.34,3.05),-3.85,.15,BRICK,'simplified garden base under recess')
    face(b,box(5.34,0,9.27,6.17),-3.85,.15,WHITE,'unresolved eastern garden wall')
    yz(box(-3.91,0,5.45,6.17),9.24,WHITE,'simplified eastern eaves return')
    yz(box(-3.92,0,5.42,6.17),-9.47,WHITE,'simplified western eaves return')
    face(b,box(-9.41,0,9.24,6.18),5.46,.16,WHITE,'neutral rear closure without invented openings')
    # The two cross slopes rise above the main roof. Close their junctions down to
    # the principal sloping roof instead of letting thin roof plates float in the air.
    def back_level(y):
        return 10.65-(10.65-6.27)*max(0.,y-.78)/(5.86-.78)
    for label,l,r,front,back,eave,ridge in [
            ('northwest',-10.55,-6.85,1.45,5.92,7.54,10.38),
            ('north central',-4.65,-.05,2.16,6.13,7.87,10.18)]:
        x=.5*(l+r)
        rim=Polygon([(l,6.15),(r,6.15),(r,eave),(x,ridge),(l,eave)])
        for end,yy in [('garden side',front+.07),('rear',back-.16)]:
            shape=rim.intersection(box(l-.01,min(back_level(yy),eave)-.02,r+.01,ridge+.01))
            if not shape.is_empty:face(b,shape,yy,.11,WHITE,label+' gable '+end)
        for tag,xx in [('west',l+.1),('east',r-.10)]:
            slope=Polygon([(front,back_level(front)-.05),(back,back_level(back)-.05),(back,11.2),(front,11.2)])
            visible=box(front,6.15,back,eave).intersection(slope)
            if not visible.is_empty:yz(visible,xx,WHITE,label+' '+tag+' cheek')

def higher_halfplane(a,b,c):
    limit=[(-64,-64),(64,-64),(64,64),(-64,64)]
    result=[]
    for p,q in zip(limit,limit[1:]+limit[:1]):
        f=a*p[0]+b*p[1]+c;g=a*q[0]+b*q[1]+c
        if f>=0:result.append(p)
        if (f>0 and g<0) or (f<0 and g>0):result.append(tuple(p[k]+(q[k]-p[k])*f/(f-g)for k in (0,1)))
    return Polygon(result) if len(result)>=3 else Polygon()

def roof_planes():
    planes=[]
    def add(name,xy,levels):
        coeff=np.linalg.solve([[x,y,1] for x,y in xy[:3]],levels[:3])
        assert all(abs(z-np.dot(coeff,(x,y,1)))<1e-5 for (x,y),z in zip(xy,levels))
        planes.append((name,Polygon(xy),coeff))
    x0,x1=-9.90,9.90;y0,y1=-4.22,5.86;ridge=.78;z0,z1=6.27,10.65
    add('main garden slope',[(x0,y0),(x1,y0),(6.72,ridge),(-7.15,ridge)],[z0,z0,z1,z1])
    add('main back slope',[(x1,y1),(x0,y1),(-7.15,ridge),(6.72,ridge)],[z0,z0,z1,z1])
    add('left hip',[(x0,y1),(x0,y0),(-7.15,ridge)],[z0,z0,z1])
    add('right hip',[(x1,y0),(x1,y1),(6.72,ridge)],[z0,z0,z1])
    def crossing(name,a,b,front,back,eave,top):
        m=.5*(a+b)
        add(name+' left',[(a,front),(m,front),(m,back),(a,back)],[eave,top,top,eave])
        add(name+' right',[(m,front),(b,front),(b,back),(m,back)],[top,eave,eave,top])
    crossing('garden gable',-8.92,-2.68,-6.08,2.06,6.46,9.72)
    crossing('northern cross gable',-10.55,-6.85,1.45,5.92,7.54,10.38)
    crossing('east cross gable',-4.65,-.05,2.16,6.13,7.87,10.18)
    add('wide shed dormer',[(-2.57,-3.34),(1.83,-3.34),(1.83,-.22),(-2.57,-.22)],[8.11,8.11,10.08,10.08])
    return planes

def roofs(b,lod):
    planes=roof_planes()
    for name,plan,coeff in planes:
        patches=plan
        for other,other_plan,other_coeff in planes:
            if name==other:continue
            # Expose only the higher of the two roof planes in their shared footprint.
            mask=higher_halfplane(*(other_coeff-coeff))
            patches=patches.difference(other_plan.intersection(mask))
        patches=set_precision(patches,.0001)
        if patches.is_empty:continue
        a,c,d=coeff
        b.prism(patches,-.115,0,lambda x,y,t:(x,y,a*x+c*y+d+t),TILE,name)
    b.tube([(-7.15,.78,10.72),(6.72,.78,10.72)],.092,EDGE,6 if lod else 10,'long main ridge')
    b.tube([(-5.80,-6.08,9.79),(-5.80,-.27,9.79)],.093,EDGE,6 if lod else 10,'projecting gable ridge')
    b.tube([(-2.60,-3.34,8.12),(1.86,-3.34,8.12)],.07,EDGE,6 if lod else 10,'dormer eave lip')
    wall(b,box(-2.50,7.01,1.76,8.03),[(-2.33,7.27,1.60,7.92)],-3.24,SHADOW,'shed dormer shaded opening')
    if not lod:
        for j,x in enumerate([-1.04,.30]):beam(b,x,7.28,x,7.93,-3.20,.055,.075,f'dormer sash division {j+1}')
    for x,n in [(-2.46,'left'),(1.67,'right')]:
        ys,zs=[-3.22,-.25,-3.22],[7.12,10.04,8.05]
        b.prism(Polygon(zip(ys,zs)),x-.07,x+.07,lambda y,z,t:(t,y,z),WHITE,'dormer '+n+' cheek')

def build(lod=False):
    b=CrownBuilder(PALETTE);garden_front(b,lod);roof_supports(b);roofs(b,lod)
    return b

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',required=True,type=Path);p.add_argument('--lod',action='store_true');a=p.parse_args()
    b=build(a.lod);print(b.save(a.output,META)['sha256'])
