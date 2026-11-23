"""Exterior reconstructed from the archived Wukang elevation and the 1947 building outline."""
import argparse
import json
import math
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon, Point, box as rect
from shapely.ops import unary_union
from finishes import PALETTE, RENDER, BASE, TOE, CAP, METAL, GLASS, LIGHT, ROOF, SEAM

SOURCE=Path(__file__).resolve().parent
PROJECT=next(p for p in SOURCE.parents if (p/'tools/package_architectural_model.py').is_file())
PRECISE=PROJECT/'source/precise'
for shared in ['hongkou-general-post-office/source/common','hongkou-tanggu-road-apartment-dated-crown/source']:
    sys.path.insert(0,str(PRECISE/shared))
from crown_builder import CrownBuilder as Builder

ID='xuhui-capetown-apartments-wukang-road-wedge'
SLUG='capetown-apartments-wukang-road-wedge'
DATA=json.loads((SOURCE/'elevation.json').read_bytes())
L=DATA['front_length']
D=DATA['rear_depth']
R=DATA['round_tip_radius']
URL='https://sghexport.shobserver.com/html/baijiahao/2024/01/22/1239744.html'
META=dict(id=ID,name='开普敦公寓',address=DATA['address'],heritage_group='5D011',period='1940年建，依2024年1月刊发的修缮后外观复原',scope='沿武康路立面、南端圆角与平屋顶外形。后部据1947街廓图和屋面影像收束。',geometry_license='MIT',texture_license='MIT',license_url='https://opensource.org/license/mit',photos_embedded=False,third_party_models_embedded=False,source=URL,photo_source=URL,photo_author='徐汇通，上海市徐汇区官方账号。公开修缮报道所载图4、6、9，2024年1月22日。',viewer_page=SLUG+'.html',camera_views=json.loads((SOURCE/'cameras.json').read_bytes()))

def x(u):return (u-DATA['left_u'])*L/(DATA['right_u']-DATA['left_u'])
def z(v):return (DATA['grade_v']-v)*DATA['eaves_z']/(DATA['grade_v']-DATA['eaves_v'])
def shape(u0,v0,u1,v1):return rect(x(u0),z(v1),x(u1),z(v0))
def facade(b,poly,front,back,material,name):
    if not poly.is_empty:b.prism(poly,-back,-front,lambda u,h,d:(u,-d,h),material,name)
def block(b,x0,x1,y0,y1,h0,h1,m,label):
    b.box([(x0+x1)/2,(y0+y1)/2,(h0+h1)/2],[x1-x0,y1-y0,h1-h0],m,label=label)
def window(b,box,columns,rows,front,label,lod):
    u0,v0,u1,v1=box;a,c,lo,hi=x(u0),x(u1),z(v1),z(v0)
    glassd=front+.112
    for i in range(columns):
        for j in range(len(rows)-1):
            l=a+(c-a)*i/columns;r=a+(c-a)*(i+1)/columns
            btm=lo+(hi-lo)*rows[j];top=lo+(hi-lo)*rows[j+1]
            block(b,l+.008,r-.008,glassd,glassd+.021,btm+.008,top-.008,
                  LIGHT if (i+j)%5==0 else GLASS,label+f' pane {i+1}.{j+1}')
    for i in range(columns+1):
        u=a+(c-a)*i/columns;w=.053 if i in (0,columns) else .035
        block(b,max(a,u-w/2),min(c,u+w/2),front+.028,glassd+.007,lo,hi,METAL,label+f' vertical {i+1}')
    for j,h in enumerate(rows):
        v=lo+(hi-lo)*h;w=.052 if j in (0,len(rows)-1) else .029
        block(b,a,c,front+.021,glassd+.005,max(lo,v-w/2),min(hi,v+w/2),METAL,label+f' rail {j+1}')
    if not lod and columns>=3:
        for i in (0,columns-1):
            u=a+(c-a)*(i+.52)/columns
            block(b,u-.032,u+.032,front+.007,front+.030,lo+.44*(hi-lo),lo+.485*(hi-lo),METAL,label+f' latch {i+1}')
def casing(b,outline,front,width,lip,label):
    facade(b,outline.buffer(width,join_style='mitre').difference(outline),front-lip,front+.035,CAP,label)
def porthole_moulding(b,cx,cz,lod,label):
    # Section from the rounded outer shoulder to the bevel around the inset square light.
    profile=[(.363,.045),(.463,.045),(.474,-.036),(.462,-.092),(.430,-.133),
             (.387,-.142),(.356,-.109),(.340,-.066),(.340,.022)]
    sections=24 if lod else 56;verts=[];faces=[]
    for i in range(sections):
        th=2*math.pi*i/sections
        for r,y in profile:verts.append((cx+r*math.cos(th),y,cz+r*math.sin(th)))
    k=len(profile)
    for i in range(sections):
        for j in range(k):
            v=(i*k+j,(i+1)%sections*k+j,(i+1)%sections*k+(j+1)%k,i*k+(j+1)%k)
            faces.append(v)
    tri=np.asarray(verts)
    vol=sum(np.dot(tri[a],np.cross(tri[c],tri[d]))+np.dot(tri[a],np.cross(tri[d],tri[e]))for a,c,d,e in faces)
    b.add(verts,[tuple(reversed(f))for f in faces] if vol<0 else faces,CAP,label)
def nose_plan(steps):
    back=np.array([DATA['rear_x'],D]);angle=math.atan2(D,DATA['rear_x'])
    for _ in range(4):
        virtual=R-R/math.tan(angle/2)
        angle=math.atan2(D,DATA['rear_x']-virtual)
    center=np.array([R,R]);angles=np.linspace(-math.pi/2,angle-3*math.pi/2,steps+1)
    arc=[center+R*np.array([math.cos(t),math.sin(t)]) for t in angles]
    return Polygon([*arc,back,[L,0]]).buffer(0)
def front_shell(b,lod):
    centre=shape(315,38,554,465);nose_stop=90
    outer=Polygon([(x(nose_stop),0),(L,0),(L,z(65)),(x(554),z(65)),(x(554),z(38)),(x(315),z(38)),(x(315),z(65)),(x(nose_stop),z(65))])
    openings=[]; grouped=[]
    for field,columns,face in [('left_windows',3,0.),('centre_windows',6,-.23),('paired_windows',2,0.),('stair_windows',2,-.06)]:
        for j,row in enumerate(DATA[field]):
            label={'left_windows':'Bow-side rectangular','centre_windows':'Central projecting','paired_windows':'North paired','stair_windows':'North vertical'}[field]+f' F{j+2}'
            openings.append(shape(*row));grouped.append((field,columns,face,row,label))
    circles=[]
    for u,v in DATA['round_windows']:
        circ=Point(x(u),z(v)).buffer(.363,quad_segs=12 if lod else 32);circles.append(circ);openings.append(circ)
    ground=[shape(*r) for r in DATA['ground_openings']];openings+=ground
    wall=outer.difference(unary_union(openings))
    base=rect(-1,-1,L+1,z(DATA['render_base_v']))
    toe=rect(-1,-1,L+1,z(DATA['base_v']))
    facade(b,wall.intersection(toe),-.026,.20,TOE,'Ground | tooled plinth')
    facade(b,wall.intersection(base).difference(toe),0,.20,BASE,'Ground | washed aggregate')
    facade(b,wall.difference(base).difference(centre),0,.20,RENDER,'Upper | principal street wall')
    facade(b,wall.intersection(centre),-.23,.22,RENDER,'Upper | wide projected panel')
    for field,columns,face,row,label in grouped:
        opening=shape(*row)
        if field=='paired_windows':
            lo,v0,hi,v1=row;span=(hi-lo)*.32
            for i,(left,right) in enumerate([(lo,lo+span),(hi-span,hi)]):
                window(b,(left,v0,right,v1),2,[0,.46,.81,1],face,label+f' leaf {i+1}',lod)
            facade(b,shape(lo+span,v0,hi-span,v1),face,face+.18,RENDER,label+' pier')
            casing(b,opening,face,.060,.075,label+' frame')
        else:
            window(b,row,columns,[0,.44,.79,1] if field!='stair_windows' else [0,.37,.71,1],face,label,lod)
            casing(b,opening,face,.078 if field!='centre_windows' else .108,.080,label+' reveal')
        a,lo,c,_=opening.bounds
        block(b,a-.08,c+.08,face-.123,face+.045,lo-.087,lo+.001,CAP,label+' sill')
        if field in ('left_windows','centre_windows'):
            for side,xp in enumerate((a+.065,c-.065)):
                # Short canted lugs below the front lip are clear in the post-repair view.
                b.prism(Polygon([(face-.117,lo-.083),(face+.010,lo-.083),
                                 (face+.010,lo-.196),(face-.068,lo-.160)]),
                        xp-.037,xp+.037,lambda y,h,d:(d,y,h),CAP,label+f' sill lug {side+1}')
    for j,(circle,(u,v)) in enumerate(zip(circles,DATA['round_windows'])):
        label=f'Porthole F{j+2}'; cx,cz=x(u),z(v)
        porthole_moulding(b,cx,cz,lod,label+' bevelled surround')
        square=rect(cx-.225,cz-.223,cx+.225,cz+.223)
        facade(b,circle.difference(square),.058,.131,CAP,label+' round inner cheek')
        block(b,cx-.222,cx+.222,.143,.166,cz-.221,cz+.221,GLASS,label+' square glass')
        facade(b,square.difference(square.buffer(-.030)),.091,.148,METAL,label+' square steel frame')
    for j,row in enumerate(DATA['ground_openings']):
        op=shape(*row);label=f'Ground opening {j+1}'
        window(b,row,1 if j in [0,5,6,7] else 3,[0,.58,.87,1] if j in [1,3,6] else [0,.72,1],.038,label,lod)
        casing(b,op,0,.044,.030,label+' reveal')
    for a,c,y,top in [(90,315,0,z(65)),(315,554,-.23,z(38)),(554,820,0,z(65))]:
        block(b,x(a),x(c),y-.050,y+.22,top-.075,top+.032,SEAM,'Street | flat parapet lip '+str(a))
    for a,c,v in [(90,545,509),(545,820,498)]:
        block(b,x(a),x(c),-.143,.15,z(v)-.082,z(v)+.049,CAP,'Street | shop head drip '+str(a))
def envelope(b,lod):
    plan=nose_plan(10 if lod else 24);cut=x(90)
    tip=plan.intersection(rect(-2,-2,cut,D+1))
    base=z(509);cap=z(33)
    def tip_part(bottom,top,material,label):
        b.plan_prism(tip,bottom,top,material,label)
    tip_part(0,z(567),TOE,'Bow | stone toe');tip_part(z(567),base,BASE,'Bow | washed base')
    at=base
    for j,(v0,v1) in enumerate(DATA['corner_slits']):
        bot,top=z(v1),z(v0);tip_part(at,bot,RENDER,'Bow | curved drum '+str(j+1))
        inset=tip.buffer(-.047,join_style='mitre');b.plan_prism(inset,bot,top,GLASS,'Bow | wrapped slot '+str(j+1))
        for px in (.32*cut,.83*cut):
            sec=tip.intersection(rect(px-.040,-.018,px+.040,.060))
            if not sec.is_empty:b.plan_prism(sec,bot-.012,top+.012,CAP,'Bow | narrow pier '+str(j+1)+' '+str(round(px,2)))
        at=top
    tip_part(at,cap,RENDER,'Bow | top curved drum')
    b.plan_prism(tip.buffer(.036,join_style='mitre'),cap,cap+.050,SEAM,'Bow | crown cap')
    floor_roof=z(65)-.40;roof=plan.intersection(rect(cut,-1,L+1,D+1))
    b.plan_prism(roof, floor_roof-.14,floor_roof,ROOF,'Roof | flat triangular deck')
    edge=plan.boundary.buffer(.11,cap_style='flat',join_style='mitre').intersection(rect(cut,.205,L+.2,D+.2))
    b.plan_prism(edge,0,z(65),RENDER,'Rear | courtyard and party wall outline')
    b.plan_prism(edge,z(65),z(65)+.042,SEAM,'Roof | thin rear coping')
    b.plan_prism(plan,.0,.12,TOE,'Base | building footprint')
    # Interior slabs meet the inner face of the 0.20 m street wall.
    floor_plan=roof.intersection(rect(cut,.205,L-.11,D))
    for i,v in enumerate((443,325,207)):
        level=z(v);b.plan_prism(floor_plan,level-.11,level,BASE,'Floor | inner slab '+str(i+2))
def add_building(b,lod=False):
    envelope(b,lod)
    front_shell(b,lod)
def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('--output',type=Path,required=True);cli.add_argument('--lod',action='store_true');args=cli.parse_args()
    builder=Builder(PALETTE);add_building(builder,args.lod);args.output.parent.mkdir(parents=True,exist_ok=True)
    report=builder.save(args.output,META);print(json.dumps({k:report[k]for k in ['triangles','parts','bytes','sha256']}))
if __name__=='__main__':main()
