"""Reconstruct Richardson Hall's lawn-facing classroom wing, traceried portal and dormers."""
import argparse
import json
import math
from pathlib import Path
import sys
import numpy as np
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Builder,Facade
sys.path.insert(0,str(HERE.parent/'measurements'))
from frontage import x,z,rect,SASH_GROUPS,DORMERS,SPAN,SCALE
ID='changning-mctyeire-richardson-hall';SLUG='mctyeire-richardson-hall'
WALL='grey ashlar';CUT='carved pale stone';WINDOW='smoky casement glass';STEEL='charcoal lead and steel'
OAK='dark oak';CLAY='rust red pantile';COPING='grey roof flashing';INSIDE='warm ivory plaster';FLOOR='polished mottled floor'
LAV='muted violet glazing';BLUE='deep blue stained glass';BRONZE='aged bronze'
PALETTE={name:dict(color=rgb,roughness=rough) for name,rgb,rough in [
    (WALL,[.49,.47,.425],.88),(CUT,[.61,.57,.49],.82),(WINDOW,[.126,.152,.176],.33),
    (STEEL,[.074,.068,.056],.57),(OAK,[.185,.083,.037],.65),(CLAY,[.38,.144,.081],.87),
    (COPING,[.29,.283,.253],.80),(INSIDE,[.79,.73,.60],.91),(FLOOR,[.28,.235,.197],.43),
    (LAV,[.265,.205,.276],.39),(BLUE,[.085,.144,.215],.32),(BRONZE,[.34,.228,.106],.53)]}
META=dict(id=ID,name='中西女中北楼景莲堂草坪立面与门厅',heritage_id='sh-historic-b2-070',
          address='江苏路155号北楼',viewer_page=SLUG+'.html',geometry_license='MIT',photos_embedded=False,
          source='https://www.meet-in-shanghai.net/cn/shanghai-cultural-relics-protection-unit/the-former-site-of-the-chinese-and-western-girls-school-788399/',
          scope='北楼临草坪教学翼、十一扇屋窗、中部门厅与摄影可读弧券。')
if (HERE/'cameras.json').exists():META['camera_views']=json.loads((HERE/'cameras.json').read_bytes())

def shallow(a,b,bottom,spring,peak):
    """Draw the low shouldered central portal in local metres."""
    w=b-a;c=(a+b)/2
    return Polygon([(a,bottom),(a,spring),(a+.016*w,spring+.29*(peak-spring)),
       (a+.052*w,spring+.54*(peak-spring)),(a+.11*w,spring+.69*(peak-spring)),
       (c,peak),(b-.11*w,spring+.69*(peak-spring)),(b-.052*w,spring+.54*(peak-spring)),
       (b-.016*w,spring+.29*(peak-spring)),(b,spring),(b,bottom)])
def gothic(u,bottom,peak,w,n):
    half=w/2;rise=1.28*half;r=(half**2+rise**2)/(2*half);spring=peak-rise
    left=[]
    for t in np.linspace(0,rise,n+1):left.append((u-half+r-math.sqrt(max(0,r*r-t*t)),spring+t))
    return Polygon([(u-half,bottom),*left,*[(2*u-v,y)for v,y in reversed(left[:-1])],(u+half,bottom)])
def grid(f,shape,steel,glass,nx,ny,depth,label):
    f.prism(shape,depth-.021,depth,glass,label+'/glazing')
    lo,base,hi,top=shape.bounds
    bars=[]
    for i in range(1,nx):
        u=lo+(hi-lo)*i/nx;bars.append(box(u-.014,base,u+.014,top))
    for i in range(1,ny):
        h=base+(top-base)*i/ny;bars.append(box(lo,h-.013,hi,h+.013))
    w=shape.difference(shape.buffer(-.033,join_style=2))
    if bars:w=w.union(shape.intersection(unary_union(bars)))
    f.prism(w,depth+.009,depth+.044,steel,label+'/muntins')
def casement(f,q,lod,row,label):
    lo,base,hi,top=q.bounds;cx=(lo+hi)/2;h=top-base
    grid(f,q,STEEL,WINDOW,2 if lod else 4,3 if lod else 6,-.205,label)
    # Stone cross windows have a heavy central mullion and a separate transom near the upper quarter.
    divisions=unary_union([box(cx-.037,base,cx+.037,top),box(lo,base+h*.70-.040,hi,base+h*.70+.040)])
    f.prism(q.intersection(divisions),-.122,-.048,CUT,label+'/stone cross')
    f.box(cx,base-.026,hi-lo+.097,.057,.119,.018,CUT,label+'/sill')
def doorway(f,q,label):
    lo,bt,hi,tp=q.bounds;w=hi-lo;h=tp-bt
    f.prism(q,-.207,-.16,OAK,label+'/leaves')
    for i in range(3):
        ul=lo+w*i/3+.035;ur=lo+w*(i+1)/3-.035
        ring=box(ul,bt+.115,ur,tp-.12)
        panels=[box(ul+.065,bt+h*.17,ur-.065,bt+h*.53),box(ul+.065,bt+h*.61,ur-.065,tp-.21)]
        f.prism(ring.difference(unary_union(panels)),-.153,-.103,OAK,label+'/panelled door')
        f.box(ur-.079,bt+h*.47,.027,.16,.052,-.079,BRONZE,label+'/pull')
def tracery(f,lod):
    left,right=x(535),x(621);bottom=z(378);peak=z(311)
    plate=shallow(left,right,bottom,z(316),peak)
    lights=[];widths=[.98,1.47,.98];centres=[x(548),x(577),x(607)]
    for i,(u,w)in enumerate(zip(centres,widths)):
        apex=z(322 if i==1 else 328);rise=.24 if i==1 else .18
        shape=gothic(u,bottom+.07,apex,w,7 if lod else 12)
        # The three-leaf heads above the dark vertical lights can be read in the frontal image.
        for side in (-1,1):shape=shape.union(Point(u+side*w*.255,apex-.40).buffer(w*.145,quad_segs=4 if lod else 8))
        lights.append(shape);grid(f,shape,STEEL,LAV if i!=1 else BLUE,3 if i==1 else 2,6,-.32,'Portal/lead light '+str(i+1))
        for j in [-1,0,1]:
            cc=u+j*w*.27;cz=apex+rise if j==0 else apex-.045
            quatre=unary_union([Point(cc+math.cos(a)*.072,cz+math.sin(a)*.072).buffer(.093,quad_segs=4 if lod else 8)for a in np.linspace(0,math.tau,4,endpoint=False)])
            if plate.covers(quatre):
                lights.append(quatre);f.prism(quatre,-.293,-.253,BLUE,'Portal/foliate spandrel pane')
    f.prism(plate.difference(unary_union(lights)),-.106,.015,CUT,'Portal/carved tracery screen')
def dormer(b,u,lo,front,width,lod):
    mid=front+.93;back=front+1.70;h=1.68
    side=Polygon([(front,lo-.085),(back,lo+.62),(back,lo+h+.07),(front,lo+h+.07)])
    for s in (-1,1):
        a=u+s*(width/2-.053)
        b.prism(side,a-.055,a+.055,lambda y,z,x:(x,y,z),WALL,'Roof dormers/cheek')
    face=Facade(b,(u-width/2,front),(u+width/2,front),'Dormer')
    cut=box(-width*.292,lo+.085,width*.292,lo+h-.16)
    face.prism(box(-width/2,lo-.075,width/2,lo+h+.07).difference(cut),-.12,0,WALL,'face opening')
    grid(face,cut,STEEL,WINDOW,2 if lod else 3,2 if lod else 3,-.095,'dormer sash')
    roof=Polygon([(-width/2-.095,lo+h+.08),(0,lo+h+.51),(width/2+.095,lo+h+.08),(width/2+.095,lo+h+.145),(0,lo+h+.58),(-width/2-.095,lo+h+.145)])
    b.prism(roof,-back,-front+.10,lambda x,z,d:(u+x,-d,z),CLAY,'Roof dormers/red pitched hood')
    face.box(0,lo+h+.02,width+.16,.095,.16,.03,COPING,'drip')
def add_building(b,lod=False):
    a,c=-SPAN/2,SPAN/2;d=17.01;front=Facade(b,(a,0),(c,0),'Lawn')
    left,right=x(181),x(972);eaves=z(220);floor=.04
    windows=[]
    for j,group in enumerate(SASH_GROUPS):
        for row,(top,bottom) in enumerate([(239,275),(307,345),(376,421)]):
            if j==3 and row>0:continue
            for k,(l,r)in enumerate(group):windows.append((rect(l,top,r,bottom),row,'Classroom sash '+str(j+1)+'-'+str(row+1)+'-'+str(k+1)))
    opening=shallow(x(528),x(626),floor,z(321),z(302))
    lawn=box(a,floor,c,eaves)
    front.prism(lawn.difference(unary_union([v[0]for v in windows]+[opening])),-.32,0,WALL,'perforated front')
    for window,row,label in windows:casement(front,window,lod,row,label)
    inner=shallow(x(532),x(622),floor,z(322),z(308))
    for outer,inside,back,fore in [
        (shallow(x(506),x(649),floor,z(310),z(281)),shallow(x(510),x(645),floor,z(312),z(285)),-.06,.055),
        (opening,inner,-.125,.028)]:
        front.prism(outer.difference(inside),back,fore,CUT,'Recessed portal/profiled archivolt')
    door=rect(534,392,621,434)
    doorway(front,door,'Portal')
    tracery(front,lod)
    front.prism(box(x(532),z(392),x(622),z(377)),-.13,-.023,CUT,'Portal carved head and three shields')
    for u in [x(546),x(577),x(608)]:
        shield=Polygon([(u-.135,z(380)),(u+.135,z(380)),(u+.12,z(384)),(u,z(387)),(u-.12,z(384))])
        front.prism(shield,-.027,.052,CUT,'Portal/uninscribed shield')
    for i in range(3):
        b.box(((x(527)+x(628))/2,-.20-i*.285,.063*(3-i)),(x(628)-x(527)+.16,.292,.126*(3-i)),CUT,label='Portal/approach tread')
    # Five classroom panels are divided by shallow pilasters below the continuous eaves.
    for px in [181,337,500,651,808,972]:
        front.box(x(px),eaves/2,.20,eaves,.195,.032,CUT,'Classroom panel pier')
    for end1,end2 in [(a,left),(right,c)]:
        centre=(end1+end2)/2;w=end2-end1
        b.box((centre,d/2,eaves+.07),(w,d,.14),COPING,label='End pavilions/flat roof')
        front.box(centre,eaves+.47,w,.72,.264,0,WALL,'End pavilion/parapet')
        for t in range(4):
            u=end1+w*(t+.5)/4;front.box(u,eaves+.86,w/7,.18,.291,.012,CUT,'End pavilion/stepped merlon')
        front.box(centre,eaves+.51,w+.045,.105,.315,.048,CUT,'End pavilion/lower string')
    # Red roof and stepped gable edges terminate against the two flat end pavilions.
    # Surveyed camera projection of the ridge at the half-depth plane in the 1200 px photo.
    f=1685.;distance=f/SCALE;horizon=439.-1.62*SCALE
    ridge=(439.*distance+horizon*d*.5-137.*(distance+d*.5))/f
    profile=Polygon([(-.13,eaves),(d/2,ridge),(d+.13,eaves),(d+.13,eaves+.11),(d/2,ridge+.11),(-.13,eaves+.11)])
    b.prism(profile,left,right,lambda y,z,x:(x,y,z),CLAY,'Teaching wing/double-pitched roof')
    for u in [left,right]:
        b.prism(Polygon([(0,eaves),(d,eaves),(d/2,ridge+.27)]),u-.096,u+.096,lambda y,z,x:(x,y,z),WALL,'Teaching wing/raised gable end')
        b.tube([(u,-.07,eaves+.09),(u,d/2,ridge+.29),(u,d+.07,eaves+.09)],.088,CUT,6 if lod else 10,'Gables/sloping stone coping')
    front.box((left+right)/2,eaves-.009,right-left+.12,.18,.29,.045,CUT,'Gutter and projecting eaves')
    for px in DORMERS:
        dormer(b,x(px),eaves+.67,.72,1.84,lod)
    for end in (a,c):
        b.box((end,d/2,eaves/2),(.25,d,eaves),WALL,label='Return wall/conditional plain depth')
    b.box((0,d,eaves/2),(SPAN,.24,eaves),WALL,label='Section closure/lawn wing only')
    return b
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',required=True,type=Path);parser.add_argument('--lod',action='store_true');a=parser.parse_args()
    builder=add_building(Builder(PALETTE),a.lod);report=builder.save(a.output,META)
    print(json.dumps(dict(sha256=report['sha256'],closed_parts=len(builder.parts),triangles=sum(len(s['triangles'])for s in builder.parts))))
