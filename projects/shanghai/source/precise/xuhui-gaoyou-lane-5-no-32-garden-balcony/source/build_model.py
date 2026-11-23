"""Build the photographed garden balcony, two six-light-wide windows and brick return."""
import json
import math
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from shapely.geometry import box, Polygon, LineString
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
PROJECT=Path(os.environ['SHANGHAI_PROJECT']) if 'SHANGHAI_PROJECT' in os.environ else HERE.parents[3]
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder

SLUG='xuhui-gaoyou-lane-5-no-32-garden-balcony'
META={'id':SLUG,'name':'高邮路5弄32号住宅花园阳台与清水砖转角','viewer_page':'gaoyou-lane-5-no-32-garden-balcony.html','heritage_group':'5D015 / XH-J-015-V','address':'上海市徐汇区高邮路5弄32号','period':'1931年竣工。外观依2020年两篇实地记述所刊照片，具体拍摄日未载。','scope':'Upper garden elevation between the brickwork below the balcony and the eaves, returning along the visible projecting window bay.','dimensions':'两樘宽窗暂按1.44展示单位定标。摄影拟合误差及不可见范围见量测。','photo_author':'乐哥、祖强；另见华天和','photo_source':'https://www.meipian.cn/3byew56n','photos_embedded':False,'geometry_license':'MIT, original reconstruction','texture_license':'MIT, original procedural masonry and painted timber','copyright':'Original reconstruction and generated textures under MIT. Reference photographs are not embedded.'}
BRICK='No 32 | mottled orange and buff facing';RED='No 32 | red soldier heads and sills';TIMBER='No 32 | oxblood eave timber';SOFFIT='No 32 | pale soffit and curved brackets';STEEL='No 32 | dark steel sashes';GLASS='No 32 | reflected pale glass';GLASS2='No 32 | muted blue green glass';SHADOW='No 32 | shaded glazing';IRON='No 32 | brown scroll iron';CAP='No 32 | pale weathered coping';EDGE='No 32 | weathered metal coping';PIPE='No 32 | pale drainpipe';DRAIN='No 32 | aged dark rainwater metal';FLOOR='No 32 | balcony slab';JOINT='No 32 | dark bed joint'
COLORS={BRICK:(185,127,76),RED:(156,79,46),TIMBER:(114,57,48),SOFFIT:(188,176,146),STEEL:(55,53,48),GLASS:(153,163,157),GLASS2:(130,144,148),SHADOW:(72,78,73),IRON:(101,69,51),CAP:(150,141,118),EDGE:(87,85,71),PIPE:(187,182,158),DRAIN:(91,77,61),FLOOR:(149,134,111),JOINT:(104,86,67)}
PALETTE={k:{'color':[(i/255)**2.2 for i in c],'roughness':.32 if k in (GLASS,GLASS2,SHADOW) else .79}for k,c in COLORS.items()}
for k,f in ((BRICK,'garden-brick.png'),(TIMBER,'painted-eave.png')):PALETTE[k].update(color=[1,1,1],texture=str(HERE/f))
SURVEY=json.loads((HERE.parent/'measurements/garden-camera-survey.json').read_text())['parameters']

def textures():
    """Running bond, mixed firing colours and recessed horizontal and head joints."""
    rng=np.random.default_rng(748);n=400
    variants=np.array([[184,124,77],[194,137,83],[171,108,63],[204,153,98],[164,103,66],[188,146,96],[190,116,66]])
    y,x=np.indices((n,n));course=20;unit=80;face=np.zeros((n,n,3))
    for row in range(n//course):
        colors=variants[rng.integers(0,len(variants),n//unit)]
        ix=(x[row*course:(row+1)*course]+(row%2)*unit//2)%n
        face[row*course:(row+1)*course]=colors[ix//unit]
    off=(x+(y//course%2)*unit//2)%unit; mortar=(y%course<2)|(off<2)
    face[mortar]=[133,117,94];face[(y%course==2)|(off==2)]-=12.
    face+=rng.normal(0,4.8,(n,n,1))
    Image.fromarray(np.clip(face,0,255).astype('uint8')).save(HERE/'garden-brick.png')
    n=192;y,x=np.indices((n,n));a=np.array(COLORS[TIMBER])+3.8*np.sin(x[:,:,None]*.12+.24*np.sin(y[:,:,None]*.055))+rng.normal(0,3,(n,n,1))
    Image.fromarray(np.clip(a,0,255).astype('uint8')).save(HERE/'painted-eave.png')

def front(x,z,d):return x,-d,z
def side(y,z,d):return d,y,z
def cube(b,xa,xb,ya,yb,za,zb,m,n):
    b.box(((xa+xb)/2,(ya+yb)/2,(za+zb)/2),(xb-xa,yb-ya,zb-za),m,label=n)
def face(b,mapper,poly,d0,d1,material,name):
    if not poly.is_empty:b.prism(poly,d0,d1,mapper,material,name)
def wall(b,mapper,extent,holes,depth,mat,name):
    face(b,mapper,extent.difference(unary_union(holes)),depth-.235,depth,mat,name)
def glazed(b,mapper,opening,depth,ncols,nrows,lod,name,shade=False):
    l,bot,r,top=opening.bounds;edge=.029
    # The broad front lights have a continuous transom over three paired casements.
    # The slightly wider stiles at each paired leaf are visible in both close-ups.
    wx=np.linspace(l+edge,r-edge,ncols+1);height=top-bot
    if nrows==5:zs=bot+height*np.array([0,.205,.413,.615,.814,1.])
    else:zs=np.linspace(bot,top,nrows+1)
    cut=[]
    for i,(lo,hi)in enumerate(zip(wx,wx[1:])):
        for j,(z0,z1)in enumerate(zip(zs,zs[1:])):
            e0=.017 if i%2==0 else .008;e1=.017 if i%2==1 else .008
            pane=box(lo+e0,z0+(.026 if j==0 else .013),hi-e1,z1-(.025 if j==nrows-1 else .013))
            cut.append(pane);mat=SHADOW if shade else (GLASS2 if (i+j)%4==0 else GLASS)
            face(b,mapper,pane,depth-.11,depth-.092,mat,f'{name} light {i+1}-{j+1}')
    face(b,mapper,opening.difference(unary_union(cut)),depth-.103,depth-.061,STEEL,name+' frame, transom and paired casement stiles')
def brick_trims(b,mapper,opening,depth,lod,name):
    l,s,r,h=opening.bounds
    face(b,mapper,box(l-.085,h,r+.085,h+.137),depth-.231,depth+.003,JOINT,name+' head joints')
    count=round((r-l+.17)/.063)
    for i in range(count):
        u=l-.085+(r-l+.17)*i/count;v=l-.085+(r-l+.17)*(i+1)/count
        face(b,mapper,box(u+.002,h+.003,v-.002,h+.133),depth+.003,depth+.012,RED,name+f' straight soldier {i+1}')
    span=r-l+.17;nc=round(span/.117)
    for i in range(nc):
        a=l-.085+i*span/nc
        face(b,mapper,box(a+.001,s-.067,a+span/nc-.001,s),depth-.10,depth+.078,RED,name+f' projecting brick sill {i+1}')
def eaves(b,mapfn,a,c,base,top,depth,over,lod,name,brackets=True):
    # Folded painted board, pale underside, and the thin dark gutter cap seen edge-on.
    face(b,mapfn,box(a,base,c,top-.12),depth-.22,depth+over,SOFFIT,name+' soffit')
    face(b,mapfn,box(a,top-.12,c,top-.027),depth+over-.077,depth+over+.005,TIMBER,name+' fascia')
    face(b,mapfn,box(a-.014,top-.027,c+.014,top+.014),depth-.22,depth+over+.025,EDGE,name+' folded capping')
    if brackets:
        for i,t in enumerate(np.linspace(a+.28,c-.22,max(2,round((c-a)/1.11)))):
            face(b,mapfn,box(t-.045,base-.082,t+.045,base),depth+.015,depth+over-.06,TIMBER,name+f' exposed rafter {i+1}')
def curve_bracket(b,x,z,over,lod,name):
    outer=[(0,z),(-over,z),(-over,z-.10)]
    for ang in np.linspace(math.pi/2,0,8 if lod else 18)[1:]:
        outer.append((-over+(over-.082)*math.cos(ang),z-.49+.39*math.sin(ang)))
    outer.extend([(-.08,z-.52),(0,z-.52)])
    face(b,side,Polygon(outer),x-.038,x+.038,SOFFIT,name)
def tube(b,points,r,mat,name,lod):b.tube(points,r,mat,sides=6 if lod else 10,label=name)
def balcony(b,a,lod):
    h=a['front_slab_z'];top=a['column_top_z'];cl=a['left_canopy_x'];cr=a['right_canopy_x'];dy=a['centre_back_y'];d=a['column_front_depth'];post_r=a['column_right_x'];w=.38;end=cr-.18
    cube(b,cl,cr,d-.12,dy+.235,h-.15,h,FLOOR,'Balcony | overhanging slab')
    cube(b,cl-.018,cr+.018,d-.138,d-.105,h-.105,h-.025,CAP,'Balcony | pale slab edge')
    for x,n in ((post_r-w,'left'),(end-w,'right')):
        cube(b,x,x+w,d-.035,d+.31,h,top,BRICK,'Balcony | '+n+' exposed brick pier')
        cube(b,x-.055,x+w+.055,d-.084,d+.344,top,top+.065,CAP,'Balcony | '+n+' oversailing pier cap')
    start=post_r;finish=end-w;y=d-.01
    for k,z in enumerate((h+.063,h+.163,top-.059)):
        cube(b,start,finish,y-.018,y+.018,z,z+(.045 if k==2 else .025),IRON,f'Balcony | wrought rail horizontal {k+1}')
    count=7
    for i in range(count+1):
        x=start+i*(finish-start)/count
        tube(b,[(x,y,h+.075),(x,y,top-.038)],.010,IRON,f'Balcony | vertical {i+1}',lod)
    # Paired curling scrolls in the clear band below the handrail and above its foot.
    for i in range(count):
        centre=start+(i+.5)*(finish-start)/count;rw=(finish-start)/count*.46
        for sign in [-1,1]:
            for layer,z in enumerate((top-.21,h+.19)):
                pts=[]
                for t in np.linspace(0,1,10 if lod else 22):
                    angle=math.pi*.98-t*math.pi*2.03
                    rad=rw*(1-.80*t)
                    pts.append((centre+sign*(rw+rad*math.cos(angle))/2,y-.002,z+rad*math.sin(angle)*.65))
                tube(b,pts,.0065,IRON,f'Balcony | scroll cell {i+1}-{sign}-{layer+1}',lod)
    for i,x in enumerate((cl+.065,cr-.075)):
        curve_bracket(b,x,a['wing_eave_z']-.22,.64,lod,f'Balcony | curved canopy support {i+1}')
def build(lod=False):
    a=SURVEY;b=CrownBuilder(PALETTE);l=a['left_outer_x'];r=a['right_outer_x'];cl=a['left_canopy_x'];cr=a['right_canopy_x'];h=a['window_height'];base=-.91;z=a['wall_under_eave_z'];top=a['wing_eave_z'];rw=a['right_window_x'];over=a['eave_projection'];dy=a['centre_back_y']
    for s,e,wx,name in ((l,cl,0.,'left'),(cr,r,rw,'right')):
        o=box(wx,0,wx+1.44,h)
        wall(b,front,box(s,base,e,z),[o],0,BRICK,'Front | '+name+' garden brick wing')
        glazed(b,front,o,0,6,5,lod,'Front | '+name+' steel window')
        brick_trims(b,front,o,0,lod,'Front | '+name+' garden window')
        start=s-(.44 if name=='left' else 0);end=e+(.43 if name=='right' else 0)
        eaves(b,front,start,end,z,top,0,over,lod,'Front | '+name+' eave')
    dl=a['centre_door_left'];dr=a['centre_door_right'];floor=a['front_slab_z']
    door=box(dl,floor+.02,dr,h)
    wall(b,front,box(cl,base,cr,z),[door],-dy,BRICK,'Balcony | recessed upper masonry')
    glazed(b,front,door,-dy,1,2,lod,'Balcony | dark door in recessed wall',True)
    brick_trims(b,front,door,-dy,lod,'Balcony | back door')
    for x,n in ((cl,'left'),(cr,'right')):
        cube(b,x-.025,x+.025,0,dy,base,z,BRICK,'Balcony | '+n+' inner reveal')
    eaves(b,front,cl,cr,z-.046,top-.07,0,over+.14,lod,'Balcony | lower canopy',False);balcony(b,a,lod)
    # The return is seen obliquely in picture 102. The image ends beyond its two narrow windows.
    step=a['side_projection'];near=a['side_bay_start'];side_end=8.83
    wall(b,side,box(.235,base,near,z),[],r,BRICK,'Return | continuous wall to projected bay')
    cube(b,r-.235,r+step,near-.11,near,base,z,BRICK,'Return | short face of projected bay')
    os=[box(5.03,-.17,6.20,1.0),box(7.41,-.30,8.16,1.02)]
    wall(b,side,box(near,base,side_end,z),os,r+step,BRICK,'Return | projecting two-window brick face')
    for i,o in enumerate(os):
        name=f'Return | narrow sash {i+1}';glazed(b,side,o,r+step,2,4,lod,name);brick_trims(b,side,o,r+step,lod,name)
    eaves(b,side,.235,near-.03,z,top,r,over,lod,'Return | recessed eave')
    eaves(b,side,near-.20,side_end+.15,z,top,r+step,over,lod,'Return | projecting eave')
    cube(b,r-.20,r+step,near-.19,near+.07,z,top-.12,SOFFIT,'Return | board at the offset')
    for i,x in enumerate((cl,cr)):
        xf=x+(.041 if i else -.02)
        tube(b,[(xf,-.045,base+.005),(xf,-.045,z-.05),(xf,-.053,z+.02),(xf,-.22,top-.075)],.032,PIPE if i else DRAIN,'Front | drain behind the balcony wing '+str(i+1),lod)
    tube(b,[(r+.042,.07,base+.01),(r+.042,.07,z-.12),(r+.05,.068,z+.01),(r+.21,.06,top-.07)],.039,DRAIN,'Return | corner downpipe',lod)
    # One small chimney is visible above the left eave, with three faces and its rim.
    cx=l+.36;cy=.78;cw=.37;ch=.61
    # A short, independently editable roof margin connects the chimney to the eave.
    # The interior slope beyond this visible strip has no recorded ridge.
    run=1.39
    eave_margin=box(l-.44,-.218,r+.43,run)
    for idx,(xa,xb,delta) in enumerate(((l-.44,cl,0),(cl,cr,-.07),(cr,r+.43,0))):
        b.prism(eave_margin.intersection(box(xa,-.218,xb,run)),top-.021+delta,top+.016+delta,lambda x,y,z:(x,y,z+.088*(y+.218)),EDGE,f'Front | shallow roof edge above bay {idx+1}')
    rim=box(cx,cy,cx+cw,cy+cw).difference(box(cx+.081,cy+.081,cx+cw-.081,cy+cw-.081))
    b.prism(rim,top,top+ch,lambda x,y,z:(x,y,z),BRICK,'Front | open brick chimney')
    rim=box(cx-.033,cy-.033,cx+cw+.033,cy+cw+.033).difference(box(cx+.074,cy+.074,cx+cw-.074,cy+cw-.074))
    b.prism(rim,top+ch,top+ch+.052,lambda x,y,z:(x,y,z),CAP,'Front | chimney crown')
    return b
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('output',type=Path);p.add_argument('--lod',action='store_true');args=p.parse_args()
    textures();print(build(args.lod).save(args.output,META)['sha256'])
