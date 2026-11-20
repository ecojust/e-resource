"""Model the photo-checked north front of the Continental Bank, 111 Jiujiang Road."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
from package_architectural_model import build
from photo_architecture import Facade,opening
from sign_lettering import add_facade_lettering

P=json.loads((HERE/'parameters.json').read_bytes())
ID=P['id']
META={'id':ID,'name':'大陆银行（九江路111号北立面）','status':'photo-informed-partial-exterior',
      'scope':'North entrance to the Shanghai Continental Bank office on Jiujiang Road, with two tall projecting wings, a recessed seven-axis center and a deep stone entrance.',
      'model_scope_zh':'九江路111号北立面，涵盖中央高阶石门洞与两盏长灯、上投大厦铭牌、黄褐砖两翼及凹入中段、窗下浅浮雕与顶部女儿墙。附属后楼与东西邻楼保留城市原景。',
      'viewer_page':'continental-bank.html','audit_directory':'data/audit/continental-bank-v1/',
      'coordinate_convention':'glTF X along Jiujiang Road toward the west, Y up, Z toward the street to the north-northwest.',
      'source_register':'source/precise/'+ID+'/reference-review.json',
      'map_reference_license':'OpenStreetMap and Overture Maps, ODbL-1.0.','interiors_modeled':False}
PALETTE={
    'granite':{'color':[.446,.432,.401],'roughness':.88},'light granite':{'color':[.545,.522,.478],'roughness':.86},
    'carved pale stone':{'color':[.529,.500,.457],'roughness':.84},'mortar':{'color':[.330,.299,.257],'roughness':.94},
    'buff brick':{'color':[.459,.377,.294],'roughness':.91},'ochre brick':{'color':[.474,.383,.288],'roughness':.9},
    'sand brick':{'color':[.530,.457,.377],'roughness':.89},'brown brick':{'color':[.375,.317,.266],'roughness':.91},
    'limestone':{'color':[.522,.500,.453],'roughness':.89},'stone shade':{'color':[.348,.330,.293],'roughness':.91},
    'bronze window frame':{'color':[.106,.116,.120],'roughness':.52,'metallic':.44},
    'recessed glass':{'color':[.151,.189,.189],'roughness':.31,'metallic':.26},
    'bank glazing':{'color':[.103,.135,.142],'roughness':.37,'metallic':.29},
    'sign bronze':{'color':[.394,.332,.245],'metallic':.64,'roughness':.51},
    'lantern bronze':{'color':[.175,.193,.174],'metallic':.55,'roughness':.48},
    'lantern glass':{'color':[.558,.639,.585],'roughness':.42,'metallic':.13},
    'roof':{'color':[.285,.279,.260],'roughness':.94}}
FRONT=.18
HALF=P['registered_front_width_m']/2-.39
BAY=4.78
RECESS=1.76
FLOOR=[(9.88,2.06),(12.98,2.12),(16.07,2.15),(19.18,2.14),(22.28,2.13),(25.41,1.80)]
FONT=HERE/'fonts/ShanghaiTrust.otf'
RATIOS=P['photo_panels_midpoints_normalised']
ALL_AXES=[(x-.5)*2*HALF for row in [*RATIOS['east_to_west_upper_projecting_wings'],*RATIOS['recessed_central_window_groups']] for x in row]


def front_wall(builder,a,b,y,label):
    return Facade(builder,[a,y],[b,y],label)


def window(f,u,base,width,height,columns=2,rows=2,glass='recessed glass'):
    hole=opening(u,base,width,height)
    f.prism(hole.buffer(.010,join_style='mitre'),-.38,-.355,glass,'recessed rectangular glazing')
    x0,z0,x1,z1=hole.bounds
    panes=[]
    for k in range(columns):
        for j in range(rows):
            left=x0+k*width/columns;bottom=z0+j*height/rows
            panes.append(box(left+(.036 if k else .079),bottom+(.030 if j else .063),
                             left+width/columns-(.036 if k+1<columns else .079),
                             bottom+height/rows-(.030 if j+1<rows else .063)))
    f.prism(hole.difference(unary_union(panes)),-.255,-.158,'bronze window frame','dark sash')
    f.box(u,base-.04,width+.13,.08,.18,-.035,'stone shade','shallow sill')


def stone_spandrel(f,x,z,w,height):
    f.box(x,z,w,height,.18,.02,'limestone','stone spandrel plaque')
    for sign in (-1,1):
        for step in range(3):
            xx=x+sign*(.055+step*w*.135)
            corn=Polygon([(xx,z+height*.40),(xx+sign*.22,z+height*.26),(xx+sign*.21,z+height*.13)])
            f.prism(corn,.094,.145,'carved pale stone','faceted stone sunray')
        f.box(x+sign*w*.28,z-.07,.051,height*.54,.12,.077,'stone shade','incised vertical plaque border')
    for i in range(3):
        xx=x+(i-1)*w*.228
        dl=Polygon([(xx-.079,z-height*.29),(xx,z-height*.40),(xx+.079,z-height*.29),(xx,z-height*.34)])
        f.prism(dl,.096,.139,'stone shade','lower plaque chevrons')


def brick_courses(f,occupied,z1,z2,lod):
    """Lay exposed brick faces around actual voids, retaining 5 mm joint beds."""
    wall=box(-f.length/2,z1,f.length/2,z2)
    brick_size=.54 if lod else .34
    course=.232 if lod else .136
    mats=['buff brick','ochre brick','sand brick','brown brick']
    batched={m:([],[])for m in mats}
    for j,z in enumerate(np.arange(z1,z2,course)):
        for k,u in enumerate(np.arange(-f.length/2-brick_size+(j%2)*brick_size*.5,f.length/2,brick_size)):
            left=max(u+.009,-f.length/2);right=min(u+brick_size-.009,f.length/2)
            bottom=z+.005;top=min(z+course-.006,z2)
            if right-left<.02 or top-bottom<.03:continue
            # Rectangular windows and full-width stone plaques occupy exact
            # intervals. Skipping boundary fragments leaves their mortar bedding.
            if any(left<r and right>l and bottom<hi and top>lo for l,lo,r,hi in occupied):continue
            mat=mats[(k*19+j*13+(j*k)%11)%12//3];v,faces=batched[mat];i=len(v)
            v.extend(f.point(x,h,.015) for x,h in [(left,bottom),(right,bottom),(right,top),(left,top)])
            faces.append([i,i+1,i+2,i+3])
    for mat,(v,faces) in batched.items():
        if faces:f.builder.add(v,faces,mat,f.label+'/staggered Taishan brick '+mat)


def upper(f,global_axes,lod):
    mean_x=f.center[0];axes=[x-mean_x for x in global_axes]
    widths=[1.00 if f.label=='Recessed middle' else 1.12 for _ in axes]
    holes=[opening(u,z,w,h) for u,w in zip(axes,widths)for z,h in FLOOR]
    f.wall(9.27,27.97,holes,.37,'mortar')
    occupied=[s.bounds for s in holes]
    for x,w in zip(axes,widths):
        for k,(z,h)in enumerate(FLOOR):
            window(f,x,z,w,h,2,2 if k<5 else 1)
            if k:
                low=FLOOR[k-1][0]+FLOOR[k-1][1]+.06;hh=z-low-.09;ww=w+.09
                stone_spandrel(f,x,low+hh/2,ww,hh)
                occupied.append((x-ww/2,low,x+ww/2,z-.07))
    brick_courses(f,occupied,9.28,25.05,lod)
    # The top bay has a pale stone surround with a shallow faceted head and
    # narrow vertical bars continuing beyond the parapet.
    top_holes=[opening(u,25.41,w,1.8)for u,w in zip(axes,widths)]
    face=box(-f.length/2,25.03,f.length/2,27.94).difference(unary_union(top_holes))
    f.prism(face,.02,.085,'limestone','light attic stone')
    for x,w in zip(axes,widths):
        head=Polygon([(x-w*.51,27.20),(x-w*.36,27.40),(x+w*.36,27.40),(x+w*.51,27.20)])
        f.prism(head,.04,.165,'light granite','chamfered window crown')
    dividers=[-f.length/2+.11]+[(a+b)*.5 for a,b in zip(axes,axes[1:])]+[f.length/2-.11]
    for u in dividers:
        for dx,h,ww in [(0.,.81,.16),(-.11,.58,.10),(.11,.58,.10)]:
            f.box(u+dx,27.70+h/2,ww,h,.37,.055,'light granite','stepped parapet pier')
    f.beam(27.96,.13,.20,'granite',label='parapet top')


def fan(f,x,z,w,h,d):
    """Folded triangular sunrays, seen over the banking hall windows."""
    f.box(x,z,w,h,.22,d-.05,'granite','frieze field')
    for k in range(8):
        a=x-w/2+w*k/8;bb=x-w/2+w*(k+1)/8;mid=x if k<4 else x+.01
        f.prism(Polygon([(a,z+h*.28),(bb,z+h*.28),(mid,z-h*.31)]),d+.04,d+.105 if k%2 else d+.079,'light granite','cut stone fan')


def lamp(f,u,z,lod):
    # The octagonal lantern is suspended from a dark, angular top bracket.
    f.box(u,z+1.10,.34,.35,.17,.08,'lantern bronze','portal lamp bracket')
    f.line((u,z+1.21,.12),(u,z+1.12,.63),.047,'lantern bronze',7,'lamp upper bracket')
    f.line((u,z+1.12,.63),(u,z+.82,.63),.034,'lantern bronze',6,'lamp hanger')
    center=f.point(u,z,.64)[:2];sides=8
    f.builder.lathe(center,[(z-.76,.04),(z-.58,.235),(z+.50,.235),(z+.66,.06)],'lantern glass',sides,f.label+'/octagonal lantern glass')
    for hi,r in [(z-.62,.27),(z+.50,.275),(z+.65,.125)]:
        f.builder.lathe(center,[(hi-.045,r),(hi+.045,r)],'lantern bronze',sides,f.label+'/lantern rim')
    for ang in np.arange(sides)*math.tau/sides:
        dx=.238*math.cos(ang);dy=.238*math.sin(ang)
        points=[[center[0]+dx,center[1]+dy,z-.60],[center[0]+dx,center[1]+dy,z+.53]]
        f.builder.tube(points,.018,'lantern bronze',5,f.label+'/lantern facets')


def banking_hall(f,lod):
    width=f.length
    # From the rectified straight-on view, each side has a narrow outer
    # opening above a side door, a broad hall window and a narrow inner window.
    axes=[(-.461,1.24,4.22,3.46),(-.347,3.02,1.80,5.88),(-.242,1.12,1.80,5.88),(-.150,1.66,1.80,5.88),
          (.150,1.66,1.80,5.88),(.242,1.12,1.80,5.88),(.347,3.02,1.80,5.88),(.461,1.24,4.22,3.46)]
    holes=[opening(x*width,z,w,h)for x,w,z,h in axes]
    doorx=[width*.461,-width*.461]
    doors=[opening(u,.10,1.54,3.31)for u in doorx]
    basement=[opening(q*width,.42,.86,.59)for q in (-.36,-.24,-.15,.15,.24,.36)]
    portal=opening(0,.08,3.93,7.79)
    f.wall(.10,9.38,[*holes,*doors,*basement,portal],.55,'granite')
    for x,w,z,h in axes:
        u=x*width;window(f,u,z,w,h,3 if w>2 else 2,3,'bank glazing')
        fan(f,u,8.47,w+.14,.59,.115)
        if w>2 or abs(x)==.150:
            for k in range(6 if w>2 else 4):
                xx=u-w/2+.22+k*(w-.44)/(5 if w>2 else 3)
                for j in range(3):
                    h0=6.74+j*.19
                    for sign in (-1,1):
                        f.line((xx,h0,-.12),(xx+sign*.11,h0+.15,-.12),.019,'bronze window frame',4 if lod else 6,'hall grille chevrons')
    for s in doors+basement:
        f.prism(s.buffer(.01,join_style='mitre'),-.39,-.37,'bank glazing','side doors and cellar grilles')
        u,low,rr,hi=s.bounds
        for xx in np.arange(u+.17,rr,.18):
            f.box(xx,(low+hi)/2,.035,hi-low,.10,-.27,'bronze window frame','cellar and side-door bars')
    # Nine stone steps fill the central bay only. The entire flight is inside
    # the street line, ascending into the recessed double banking entrance.
    for i in range(9):
        depth=.255;y=FRONT+i*depth
        f.builder.box((0,y+depth/2,(i+1)*.073),(3.82,depth,(i+1)*.146),'granite',label='Portal/nine granite treads')
    for u in (-2.41,2.41):
        f.box(u,4.60,1.03,9.20,.92,-.14,'light granite','main portal jamb')
        for dx,high in [(-.25,.21),(-.09,.45),(.09,.45),(.25,.21)]:
            f.box(u+dx,9.08+high/2,.11,high,.75,-.06,'granite','stepped jamb crown')
        add_facade_lettering(f,'111',u,2.87,.43,.235,.326,.356,'sign bronze',font=FONT,label='111 street number')
        lamp(f,u,6.95,lod)
    f.box(0,8.74,4.08,1.29,.92,-.135,'granite','present carved sign lintel')
    add_facade_lettering(f,'上投大厦',0,8.98,3.20,.52,.333,.382,'sign bronze',font=FONT,label='Chinese name inscription')
    add_facade_lettering(f,'SITICO',0,8.34,1.95,.24,.333,.369,'sign bronze',font=FONT,label='present Latin inscription')
    f.box(0,6.75,3.82,1.94,.30,-1.96,'bank glazing','high inner portal glazing')
    f.box(0,4.90,3.82,.65,.34,-2.03,'granite','inner door lintel')
    fan(f,0,4.99,3.19,.42,-1.82)
    f.box(0,3.04,3.82,3.52,.21,-2.20,'bank glazing','recessed inner doors')
    for u in [-1.80,-.82,0,.82,1.80]:
        f.box(u,3.04,.066,3.52,.14,-2.01,'lantern bronze','inner door verticals')
    for u in [-1.90,1.90]:
        f.box(u,4.13,.22,7.68,2.29,-1.10,'granite','deep rectangular portal reveal')
    f.beam(9.27,.15,.24,'granite',label='top of stone banking hall')


def assemble(b,lod):
    front=front_wall(b,-HALF,HALF,FRONT,'Jiujiang Road banking hall')
    banking_hall(front,lod)
    zones=[(-HALF,-BAY,FRONT,'Eastern front wing'),(-BAY,BAY,RECESS,'Recessed middle'),(BAY,HALF,FRONT,'Western front wing')]
    for left,right,y,label in zones:
        f=front_wall(b,left,right,y,label)
        upper(f,[x for x in sorted(ALL_AXES)if left<x<right],lod)
    for left,x in [(True,-BAY),(False,BAY)]:
        a,e=([x,FRONT],[x,RECESS]) if left else ([x,RECESS],[x,FRONT])
        Facade(b,a,e,'Central recess sidewall').wall(9.27,27.96,(),.16,'buff brick')
    ground_plan=Polygon(P['study_uv_m'])
    notch=box(-BAY,-2.,BAY,RECESS)
    b.plan_prism(ground_plan,.0,.097,'granite','Plan/base')
    b.plan_prism(ground_plan,9.22,9.32,'roof','Plan/entrance terrace')
    b.plan_prism(ground_plan.difference(notch),27.86,28.03,'roof','Plan/street section roof')
    pts=list(ground_plan.exterior.coords)
    if not ground_plan.exterior.is_ccw:pts=pts[::-1]
    for a,e in zip(pts,pts[1:]):
        if max(a[1],e[1])<FRONT+.002:continue
        Facade(b,a,e,'Back or party-wall section').wall(.097,27.90,(),.17,'stone shade')


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
