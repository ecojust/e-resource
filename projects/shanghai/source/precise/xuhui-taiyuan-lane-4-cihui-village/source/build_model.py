"""Street elevations of Cihui Village, reconstructed from the measured 2016 and 2023 photographs."""
import json
import math
import sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
from shapely.geometry import Polygon,box,LineString
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent; PROJECT=HERE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
SURVEY=json.loads((HERE.parent/'measurements/registered-street-cameras.json').read_bytes())
METRIC=json.loads((HERE.parent/"measurements/street-station-scale.json").read_bytes())
SLUG='xuhui-taiyuan-lane-4-cihui-village'
META={'id':SLUG,'name':'慈惠村太原路4弄1—2号临街转角','address':'上海市徐汇区太原路4弄1—2号','viewer_page':'taiyuan-lane-4-cihui-village.html','heritage_group':'第五批 XH-J-035-V；市表印作 D5035','period':'1922年建成。主体取2023年徐汇区政务图中的外观，另参2016年3月独立街照及2013—2020年街景。','scope':'太原路临街券窗、三层凸窗及其铁饰，北转汾阳路的阶折窗墙及一处窗湾。','source':'Original reconstruction from public exterior views.','photo_source':'https://www.thepaper.cn/newsDetail_forward_22920333','photos_embedded':False,'geometry_license':'MIT','texture_license':'MIT','copyright':'Original geometry and two procedural textures under MIT. Photographs remain with their credited publishers and photographers.'}
WALL='Cihui | ochre stippled and raked render';BASE='Cihui | grey plinth stone';CREAM='Cihui | sheltered ivory render';CAP='Cihui | grey stone sill';BROWN='Cihui | brown projecting bay frame';STEEL='Cihui | dark steel sash';GLASS='Cihui | pale reflected glass';BLUE='Cihui | blue green glass';AMBER='Cihui | warm reflected glass';DARK='Cihui | shaded glass';IRON='Cihui | ornamental metalwork';PIPE='Cihui | charcoal rainwater pipe';PALE='Cihui | pale painted timber';AWN='Cihui | green glass rain hood';JOINT='Cihui | plinth bed joints'
COLORS={WALL:(204,191,158),BASE:(125,125,112),CREAM:(210,198,174),CAP:(151,148,131),BROWN:(81,69,61),STEEL:(61,62,57),GLASS:(143,156,157),BLUE:(105,135,142),AMBER:(185,153,121),DARK:(76,83,84),IRON:(74,71,61),PIPE:(90,89,79),PALE:(197,192,172),AWN:(112,151,143),JOINT:(107,107,94)}
PALETTE={k:{'color':[(v/255)**2.2 for v in c],'roughness':.34 if k in (GLASS,BLUE,AMBER,DARK) else .86}for k,c in COLORS.items()}
for k,file in [(WALL,'raked-stucco.png'),(BASE,'plinth-stone.png')]:PALETTE[k].update(color=[1,1,1],texture=str(HERE/file))
def textures():
    rng=np.random.default_rng(768);n=240
    grey=Image.new('L',(n,n),128);draw=ImageDraw.Draw(grey)
    for i in range(2800):
        x,y=rng.integers(n,size=2);a=rng.uniform(-1.45,2.05);length=rng.integers(2,8);v=int(rng.integers(74,155))
        dx=round(length*math.cos(a));dy=round(length*math.sin(a))
        for ox in (0,-n,n):
            for oy in (0,-n,n):
                draw.line((x+ox,y+oy,x+ox+dx,y+oy+dy),fill=v,width=1)
                draw.line((x+ox+1,y+oy+1,x+ox+dx+1,y+oy+dy+1),fill=min(232,v+65),width=1)
    grain=(np.asarray(grey).astype(float)-128)*.40+rng.normal(0,4,(n,n))
    Image.fromarray(np.clip(np.array(COLORS[WALL])+grain[:,:,None],0,255).astype('uint8')).save(HERE/'raked-stucco.png')
    noise=rng.normal(size=(n,n));im=Image.fromarray(np.clip(120+noise*35,0,255).astype('uint8')).filter(ImageFilter.GaussianBlur(1.1))
    Image.fromarray(np.clip(np.array(COLORS[BASE])+(np.asarray(im).astype(float)-120)[:,:,None]*.66+noise[:,:,None]*3,0,255).astype('uint8')).save(HERE/'plinth-stone.png')
def face(a,b):
    ax,ay=a;bx,by=b;length=math.hypot(bx-ax,by-ay);vx=(bx-ax)/length;vy=(by-ay)/length
    # u along the street, z vertical, d positive towards the street.
    return lambda u,z,d:(ax+vx*u+vy*d,ay+vy*u-vx*d,z)
def sheet(b,F,poly,near,far,mat,name):
    if not poly.is_empty:b.prism(poly,near,far,F,mat,name)
def band(b,F,u,v,z,h,d0,d1,mat,name):sheet(b,F,box(u,z,v,z+h),d0,d1,mat,name)
def arc(u,s,w,t,segments):
    r=w/2;head=t-r
    return Polygon([(u-r,s),(u+r,s)]+[(u+r*math.cos(a),head+r*math.sin(a)) for a in np.linspace(0,math.pi,segments+1)])
def poly(row,arched,lod):
    u,w,z,t=row['along'],row['width'],row['sill'],row['top']
    return arc(u,z,w,t,12 if lod else 32) if arched else box(u-w/2,z,u+w/2,t)
def glazed(b,F,row,shape,arched,cols,rows,d,lod,name,paint=STEEL,warm=False):
    u,z,v,t=shape.bounds;width=v-u;height=t-z
    margin=.038;inner=shape.buffer(-margin,join_style='mitre');w=.021
    sheet(b,F,shape.difference(inner),d-.193,d-.097,paint,name+' | sash outer frame')
    divs=[u+margin+(width-2*margin)*i/cols for i in range(1,cols)]
    spring=t-width*.5 if arched else t
    transoms=list(np.linspace(z,spring,rows+1)[1:-1]) + ([spring] if arched else [])
    for i,x in enumerate(divs):
        sheet(b,F,box(x-w/2,z+.02,x+w/2,t).intersection(inner),d-.152,d-.11,paint,name+f' | upright {i+1}')
    xs=[u-.01,*divs,v+.01];zs=[z-.01,*transoms,t+.01]
    for i,(a,c) in enumerate(zip(xs,xs[1:])):
        for j,(low,high) in enumerate(zip(zs,zs[1:])):
            pane=box(a+w/2,low+w/2,c-w/2,high-w/2).intersection(inner)
            if pane.is_empty or pane.area<.0001:continue
            material=AMBER if warm and j>=len(zs)-3 else (DARK if arched and (i+j)%4!=2 else (BLUE if (i+j)%3==0 else GLASS))
            sheet(b,F,pane,d-.178,d-.163,material,name+f' | pane {i+1}.{j+1}')
        for j,h in enumerate(transoms):
            pane=box(a+w/2,h-.013,c-w/2,h+.013).intersection(inner)
            sheet(b,F,pane,d-.151,d-.108,paint,name+f' | transom {i+1}.{j+1}')
def casing(b,F,shape,d,arched,lod,name):
    l,z,r,t=shape.bounds;h=.09 if arched else .065
    ring=shape.buffer(h,join_style='mitre').difference(shape).intersection(box(l-h-.01,z,r+h+.01,t+h+.01))
    sheet(b,F,ring,d-.065,d+.035,CREAM,name+' | reveal')
    band(b,F,l-.105,r+.105,z-.084,.084,d-.081,d+.115,CAP,name+' | projecting sill')
def lip(b,F,a,c,h,lod,name):
    band(b,F,a,c,h-.169,.112,-.17,.076,CREAM,name+' | soffit')
    band(b,F,a-.022,c+.022,h-.057,.057,-.19,.128,CAP,name+' | drip')
def oval_panel(b,F,u,z,w,h,depth,lod,name,shield):
    # Two small horizontal fields flank a taller, downward-stepped central field.
    if shield:
        points=[(-.50,1),(.50,1),(.50,.32),(.37,.32),(.37,.18),(.24,.18),(.20,0),(-.20,0),(-.24,.18),(-.37,.18),(-.37,.32),(-.5,.32)]
    else:points=[(-.5,0),(.5,0),(.5,1),(-.5,1)]
    rim=Polygon([(u+a*w,z+c*h)for a,c in points]);inside=rim.buffer(-.026,join_style='mitre')
    sheet(b,F,rim.difference(inside),depth,depth+.023,IRON,name+' | perimeter')
    ons=[]
    if shield:
        for sign in (-1,1):
            for a in (.24,.39):
                line=[(u+sign*w*(a+.025*math.sin(3*math.pi*v)),z+h*v)for v in np.linspace(.19,.97,9 if lod else 23)]
                ons.append(LineString(line).buffer(.009,cap_style='flat'))
            for layer in (.29,.64):
                line=[(u+sign*w*(.095+.117*(1-.71*v)*math.cos(2.15*math.pi*v)),z+h*(layer+.16*(1-.71*v)*math.sin(2.15*math.pi*v)))for v in np.linspace(0,1,12 if lod else 30)]
                ons.append(LineString(line).buffer(.010,cap_style='flat'))
    else:
        for i in range(3):
            line=[(u+w*((i+.5)/3-.5+.146*math.cos(t)),z+h*(.5+.36*math.sin(t))) for t in np.linspace(0,2*math.pi,10 if lod else 23)]
            ons.append(LineString(line).buffer(.009,cap_style='flat'))
    for k,g in enumerate(ons):
        sheet(b,F,g.intersection(inside),depth+.003,depth+.020,IRON,name+f' | curled inset {k+1}')
def plynth(b,F,width,lod,name):
    band(b,F,0,width,0,.43,-.18,.018,JOINT,name+' | base')
    for course in range(3):
        tile=.69;offset=(course%2)*.35
        for i in range(-1,math.ceil(width/tile)+1):
            l=max(0,i*tile+offset+.006);r=min(width,(i+1)*tile+offset-.006)
            if r>l:band(b,F,l,r,course*.145+.005,.133,.018,.031,BASE,name+f' | course {course+1} stone {i+2}')
def drain(b,F,points,lod,name):
    b.tube([F(*v)for v in points],.043,PIPE,sides=6 if lod else 12,label=name)
    for i,z in enumerate((1.1,2.95,5.2,7.6)):
        u=points[0][0];sheet(b,F,box(u-.058,z-.018,u+.058,z+.018),.031,.13,PIPE,name+f' clamp {i+1}')
def add_northern_facets(b,lod):
    record=json.loads((HERE.parent/'measurements/fenyang-wing-street-registration.json').read_bytes())
    scale=METRIC['display_m_per_local_unit']
    for section in record['face_sections']:
        name=section['face'];a=np.array(section['a'])/scale;c=np.array(section['b'])/scale
        length=np.linalg.norm(c-a);F=face(a,c);h=section['top_z']/scale
        if name=='wing-joint':h=10.50/scale
        holes=[];labels=[]
        for row in section['windows']:
            u=row['along_m']/scale;w=row['width_m']/scale
            if row['id']=='door':
                # One edge of this near-corner recessed opening is behind the returning wall.
                w=min(w,2*(u-.02))
            r={'along':u,'width':w,'sill':row['sill_m']/scale,'top':row['head_m']/scale}
            arched=row['kind']=='arch';o=poly(r,arched,lod);holes.append(o)
            labels.append((row,r,o))
        # The two near angled faces rise behind the garden screen. Only the section
        # reaching the street beside the black-framed arch is fully observable below sill level.
        bottom=3.35 if name in ('near-flank','ac-window-wall','middle-pier','far-flank','short-return') else 0.
        shell=box(0,bottom,length,h).difference(unary_union(holes))
        sheet(b,F,shell,-.205,0,WALL,'Return bay | '+name+' faceted wall')
        lip(b,F,0,length,h,lod,'Return bay | '+name+' cornice')
        if bottom==0 and name!='wing-joint':
            for lower,upper in ([(0,length)] if name!='western-wing' else [(0,min(x[2].bounds[0]for x in labels if x[0]['kind']=='door')),(max(x[2].bounds[2]for x in labels if x[0]['kind']=='door'),length)]):
                if upper-lower>.04:
                    lface=lambda u,z,d,F=F,move=lower:F(u+move,z,d)
                    plynth(b,lface,upper-lower,lod,'Return bay | '+name+' plinth')
        for row,win,o in labels:
            k=row['id'];kind=row['kind'];namepart='Return bay | '+k
            if kind=='door':
                sheet(b,F,o,-.188,-.162,DARK,namepart+' recessed door')
                sheet(b,F,o.difference(o.buffer(-.041,join_style='mitre')),-.16,-.095,STEEL,namepart+' frame')
            elif kind=='grille':
                glazed(b,F,win,o,False,4,5,0,lod,namepart)
                q0,z0,q1,z1=o.bounds
                for k0 in range(5):
                    x0=q0+.012+((q1-q0)-.024)*k0/4
                    band(b,F,x0-.009,x0+.009,z0,z1-z0,-.048,-.022,IRON,namepart+f' metal bar {k0+1}')
            else:
                count=2 if kind=='arch' or k=='upper-1' or win['width']>.65 else 1
                glazed(b,F,win,o,kind=='arch',count,2 if kind=='arch' else 3,0,lod,namepart,paint=PALE if k.startswith('white-') else STEEL)
                casing(b,F,o,0,kind=='arch',lod,namepart)
def public_street_screen(b,lod):
    # The 2016 street-corner photo shows the screen meeting the corner at its southern end.
    # At station 5 the far stone post stands just before the base of the black-arched bay.
    scale=METRIC['display_m_per_local_unit'];R=SURVEY['width_assumption']
    A=np.array([R+.10,0]);B=np.array([R+1.38/scale,14.05/scale])
    F=face(A,B);length=np.linalg.norm(B-A);h=1.78/scale;rail=.59/scale
    # The original local fence photo shows a flush door under the rail on the left section.
    a=3.8/scale;v=a+.9/scale
    gap=box(a,0,v,h-.02)
    sheet(b,F,box(0,0,length,h).difference(gap),-.20,0,WALL,'Return | street screen rendered base')
    sheet(b,F,gap,-.095,-.064,DARK,'Return | flush street screen leaf')
    for l,r in [(0,a),(v,length)]:
        if r>l:
            shifted=lambda u,z,d,offset=l:F(u+offset,z,d)
            plynth(b,shifted,r-l,lod,'Return | screen street plinth')
    band(b,F,0,length,h-.041,.064,-.228,.035,CAP,'Return | street screen stone cap')
    for hrail in (.10,.48):
        band(b,F,.04,length-.04,h+hrail/scale,.023,-.102,-.076,IRON,'Return | rail crossbar '+str(hrail))
    bays=6
    for i in range(bays+1):
        u=.045+(length-.09)*i/bays
        band(b,F,u-.026,u+.026,h,rail+.035,-.128,-.069,IRON,'Return | street screen square standard '+str(i+1))
    for i in range(bays):
        for j in range(1,12):
            u=.045+(length-.09)*(i+j/12)/bays
            band(b,F,u-.0065,u+.0065,h+.032,rail-.055,-.098,-.078,IRON,f'Return | street screen slender rail {i+1}.{j}')
    for i,u in enumerate([0,length-.115]):
        band(b,F,u,u+.115,0,h+rail+.035,-.25,.055,WALL,'Return | screen terminal pier '+str(i+1))
        band(b,F,u-.025,u+.14,h+rail+.035,.055,-.275,.078,CAP,'Return | screen terminal coping '+str(i+1))
def build(lod=False):
    R=SURVEY['width_assumption'];top=SURVEY['cornice_z'];extra=SURVEY['return_step_z'];bay_d=SURVEY['bay_projection'];rows=SURVEY['windows']
    b=CrownBuilder(PALETTE);front=face((0,0),(R,0));side=face((R,0),(R,1));bay=rows['bay'];ctr=bay['along'];l=ctr-bay['width']/2;r=ctr+bay['width']/2
    # Only the lower two sashes in the upper oriel are on the projecting plane; the whole opening is cut through the parent shell.
    front_parts={k:poly(row,k.startswith('a'),lod)for k,row in rows.items()if k[0]!='s'}
    start=METRIC['south_end_local_x']
    upper=top+.29
    h=Polygon([(start,0),(R,0),(R,top),(8.32,top),(8.32,upper),(start,upper)])
    sheet(b,front,h.difference(unary_union(list(front_parts.values()))),-.23,0,WALL,'Front | Taiyuan Road raked wall')
    lip(b,front,start,8.32,upper,lod,'Front | oriel wing parapet');lip(b,front,8.32,R,top,lod,'Front | corner parapet')
    plynth(b,face((start,0),(R,0)),R-start,lod,'Front | dark plinth')
    for k,q in front_parts.items():
        if k=='bay':continue
        ach=k.startswith('a');small=k.endswith('1') and k.startswith('r')
        glazed(b,front,rows[k],q,ach,1 if small else 2,2 if ach else 3,0,lod,'Front | '+k,warm=k=='rg2')
        casing(b,front,q,0,ach,lod,'Front | '+k)
        if k in ('rm1','rm2'):
            u0,z0,u1,z1=q.bounds
            fall=lambda u,z,d:(u,-d,z-.16*d)
            band(b,fall,u0-.053,u1+.053,z1+.100,.028,.012,.206,AWN,'Front | green glass hood '+k)
            band(b,fall,u0-.060,u1+.060,z1+.097,.040,.197,.211,STEEL,'Front | hood drip '+k)
    o=front_parts['bay'];lo=bay['sill'];hi=bay['top'];bottom=lo-.85
    glazed(b,front,bay,o,False,3,1,bay_d,lod,'Oriel | three glazed lights',paint=BROWN)
    sheet(b,front,box(l-.065,bottom,r+.065,lo),-.028,bay_d,CREAM,'Oriel | projecting spandrel')
    band(b,front,l-.085,r+.085,bottom,.057,-.03,bay_d+.061,CAP,'Oriel | lower drip')
    band(b,front,l-.083,r+.083,bottom+.057,.116,-.035,bay_d+.038,CREAM,'Oriel | stepped lower fascia')
    band(b,front,l-.10,r+.10,hi,.13,-.035,bay_d+.05,CREAM,'Oriel | projecting hood')
    for k,x in enumerate([l,r]):
        edge=face((x,0),(x,-1 if k==0 else 1))
        if k==0:sp=box(0,lo,bay_d,hi)
        else:sp=box(-bay_d,lo,0,hi)
        glazed(b,edge,bay,sp,False,1,1,0,lod,'Oriel | side light '+str(k+1),paint=BROWN)
    for i,(cx,cz,span,rise,shield) in enumerate([(ctr,lo-.52,.81,.52,True),(l+.54,lo-.20,.59,.20,False),(r-.51,lo-.20,.59,.20,False)]):
        oval_panel(b,front,cx,cz,span,rise,bay_d+.002,lod,'Oriel | ironwork '+str(i+1),shield)
    drain(b,front,[(8.14,top-.02,.052),(8.14,3.99,.052),(8.22,3.85,.055),(R-.13,3.85,.055),(R-.095,3.74,.055),(R-.095,.48,.045)],lod,'Front | turned downpipe')
    # The left ground return window lies behind the boundary wall in the photographs.
    ret={k:poly(row,False,lod)for k,row in rows.items() if k.startswith('s') and k!='sg1'}
    step=3.30;end=5.95;rt=top+1.08
    edge=Polygon([(0,0),(end,0),(end,rt),(step,rt),(step,top),(0,top)])
    sheet(b,side,edge.difference(unary_union(list(ret.values()))),-.23,0,WALL,'Return | stepped Fenyang facade')
    lip(b,side,0,step,top,lod,'Return | low parapet');lip(b,side,step,end,rt,lod,'Return | high parapet')
    plynth(b,side,end,lod,'Return | corner plinth')
    for k,q in ret.items():
        glazed(b,side,rows[k],q,False,2,3,0,lod,'Return | '+k);casing(b,side,q,0,False,lod,'Return | '+k)
    drain(b,side,[(.23,top,.044),(.23,.35,.044)],lod,'Return | corner downpipe')
    drain(b,side,[(6.077,rt,.24),(6.077,.35,.24)],lod,'Return | high wall downpipe')
    add_northern_facets(b,lod)
    public_street_screen(b,lod)
    scale=METRIC['display_m_per_local_unit']
    for part in b.parts:
        part['vertices']=(np.asarray(part['vertices'])*scale).tolist()
    return b
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('path',type=Path);p.add_argument('--lod',action='store_true');p.add_argument('--textures',action='store_true');a=p.parse_args()
    if a.textures:textures()
    print(build(a.lod).save(a.path,META)['sha256'])
