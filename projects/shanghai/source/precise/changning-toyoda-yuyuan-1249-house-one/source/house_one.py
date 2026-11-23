"""Exterior fabric and roof of No. 1, following the named 2018 corner photograph."""
from math import cos,sin,pi
from pathlib import Path
import numpy as np
from shapely import set_precision
from shapely.geometry import Polygon, box, LineString
from shapely.ops import unary_union
from house_fabric import Wall,paint
from photo_architecture import opening
import three_arches
S=Path(__file__).parent
BRICK='House one | blue-grey running bond'; TILE='House one | dark red roof tile'
CLAY='House one | radial red brick';ALT='House one | russet brick'; JOINT='House one | buff joint'
STONE='House one | pale carved stone';GREY='House one | grey lower render'
FRAME='House one | crimson joinery';GLASS='House one | shaded courtyard glass';SKY='House one | pale reflected glass'
RAIL='House one | red painted railing';DARK='House one | deep reveal'
WATER='House one | light rainwater goods';RIDGE='House one | ridge clay';EAVES='House one | weathered red fascia'
DECK='House one | grey concrete';CEMENT='House one | weathered terrace render';OCHRE='House one | recessed porch plaster'
DOOR='House one | dark red door'
PALETTE={BRICK:{'texture':str(S/'blue-grey-brick.png'),'color':[1,1,1],'roughness':.95},TILE:{'texture':str(S/'interlocking-roof-tiles.png'),'color':[1,1,1],'roughness':.87},
 CLAY:paint((168,94,75)),ALT:paint((153,84,65)),JOINT:paint((166,143,113)),STONE:paint((192,189,174)),
 GREY:paint((148,148,135)),FRAME:paint((119,58,48),.65),GLASS:paint((75,88,83),.24,.18),SKY:paint((112,127,124),.27,.14),
 RAIL:paint((125,71,60),.65,.1),DARK:paint((53,51,46)),WATER:paint((188,184,163),.69),RIDGE:paint((129,91,74)),EAVES:paint((115,68,54)),
 DECK:paint((154,151,138)),CEMENT:paint((153,153,128)),OCHRE:paint((191,179,151)),DOOR:paint((98,56,47),.64)}
def ring(cx,z,rx,rz,a0=0,a1=pi,n=20):
    return [(cx+rx*cos(a0+(a1-a0)*k/n),z+rz*sin(a0+(a1-a0)*k/n))for k in range(n+1)]
def brick_arch(w,center,spring,rx,rz,thick,label,lod):
    def sect(r1,r2,a,c,n):
        return Polygon(ring(center,spring,rx+r2,rz+r2,a,c,n)+ring(center,spring,rx+r1,rz+r1,c,a,n))
    w.prism(sect(0,thick,0,pi,48),-.04,.038,JOINT,label+' joints')
    count=15 if lod else 27
    for j in range(count):
        a=(j+.035)*pi/count;c=(j+.965)*pi/count
        w.prism(sect(0,thick,a,c,2 if lod else 3),-.032,.053,CLAY if j%4 else ALT,label+' voussoirs')
def turned(b,x,y,profile,mat,label,lod=False):
    n=14 if lod else 24
    a=np.arange(n)*2*pi/n
    verts=[(x+r*cos(v),y+r*sin(v),z)for z,r in profile for v in a]
    fs=[tuple(reversed(range(n))),tuple(range(len(verts)-n,len(verts)))]
    for j in range(len(profile)-1):
        for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
    b.add(verts,fs,mat,label)
def sash(w,c,z0,span,spring,rise,lod,label,cols=3,rails=2,depth=-.23,fan=True):
    contour=opening(c,z0,span,spring+rise-z0,rise,30 if lod else 54)
    inner=contour.buffer(-.062,join_style=2)
    w.prism(contour.difference(inner),depth-.07,depth,FRAME,label+' perimeter')
    w.prism(inner,depth-.10,depth-.079,GLASS,label+' glazing')
    for i in range(1,cols):
        u=c-span/2+span*i/cols
        strip=box(u-.025,z0+.05,u+.025,spring-.035)
        w.prism(strip.intersection(inner),depth-.056,depth-.009,FRAME,label+' vertical')
    for i in range(1,rails+1):
        z=z0+(spring-z0)*i/(rails+1)
        w.rect(c-span/2+.055,z-.018,c+span/2-.055,z+.018,depth-.045,depth-.013,FRAME,label+' crossbar')
    if rise>.05:
        w.rect(c-span/2+.045,spring-.035,c+span/2-.045,spring+.03,depth-.05,depth-.004,FRAME,label+' transom')
        if fan:
            for i in range(1,cols):
                u=c-span/2+span*i/cols
                w.prism(box(u-.018,spring+.03,u+.018,spring+rise).intersection(inner),depth-.05,depth-.008,FRAME,label+' fanlight bar')
def shell_band(w,z,tag):
    for zz,h,back,f,mat in [(z-.16,.10,-.08,.035,ALT),(z-.065,.105,-.10,.086,CLAY),(z+.04,.056,-.08,.127,ALT),(z+.096,.055,-.08,.057,CLAY)]:
        w.rect(0,zz,w.length,zz+h,back,f,mat,tag)
def main_face(b,lod,L):
    x0=L['front_min_x'];w=Wall(b,(x0,0),(0,0));u=lambda x:x-x0
    centers=[u(x)for x in L['front_centres_x']];width=L['front_clear_width'];spring=L['front_arch_spring_z'];rise=L['front_arch_inner_rise'];base=L['front_arcade_base_z']
    centers_abs=L['front_centres_x']
    left=centers[0]-width/2;right=centers[-1]+width/2
    rad=(centers[1]-centers[0])/2
    union=unary_union([box(left,base,right,spring),*[Polygon(ring(c,spring,rad if j else width/2,rise,n=50))for j,c in enumerate(centers)]])
    # The fourth arch meets the broad brick end pier. The separate bay at the
    # end has a rectangular red sash below a bricked-in segmental head.
    xc,bottom,sw,sh=L['front_single'];c1=u(xc);other=box(c1-sw/2,bottom,c1+sw/2,bottom+sh)
    facade=box(0,0,w.length,L['eave_z']).difference(unary_union([union,other]))
    w.prism(set_precision(facade,1e-7),-.34,0,BRICK,'Arcade | grey brick front')
    w.rect(0,.02,w.length,.85,-.07,.028,GREY,'Arcade | lower cement skirt')
    shell_band(w,L['floor_z']-.015,'Arcade | projecting floor courses')
    back_holes=[opening(c,base+.075,width-.07,spring+rise-base-.135,rise-.07,36) for c in centers]
    screen=box(left-.15,base-.04,right+.15,spring+rise+.18).difference(unary_union(back_holes))
    w.prism(set_precision(screen,1e-7),-.43,-.235,BRICK,'Arcade | pierced inner lining')
    b.plan_prism(box(centers_abs[0]-width/2,0,centers_abs[-1]+width/2,.62),base-.10,base,DECK,'Arcade | recessed continuous sill')
    for j,c in enumerate(centers):
        tag=f'Arcade {j+1} |'
        brick_arch(w,c,spring,rad if j else width/2,rise,.25,tag,lod)
        sash(w,c,base+.09,width,spring-.015,rise-.055,lod,tag+' red window',cols=3,rails=2,depth=-.175)
        w.rect(c-width/2,base+.78,c+width/2,base+.87,-.14,-.025,RAIL,tag+' balustrade rail')
        w.rect(c-width/2,base+.026,c+width/2,base+.11,-.14,-.025,RAIL,tag+' toe rail')
        for k in range(1,9):
            uk=c-width/2+width*k/9
            xx,yy,_=w.point(uk,0,-.068)
            turned(b,xx,yy,[(base+.095,.035),(base+.16,.033),(base+.22,.047),(base+.32,.037),(base+.40,.029),(base+.65,.025),(base+.71,.038),(base+.79,.034)],RAIL,tag+' turned balusters',lod)
        if j<3:
            col=(centers_abs[j]+centers_abs[j+1])/2
            prof=[(base,.185),(base+.065,.203),(base+.115,.182),(base+.16,.156),(spring-.32,.132),(spring-.22,.147),(spring-.17,.188),(spring-.115,.189),(spring-.086,.217),(spring-.027,.218)]
            turned(b,col,-.012,prof,STONE,tag+' freestanding round column',lod)
            b.box((col,.008,spring-.006),(.43,.40,.07),STONE,label=tag+' square abacus')
    sash(w,c1,bottom,sw,bottom+sh,0,lod,'End bay | upright red sash',cols=2,rails=2,depth=-.17)
    w.rect(c1-sw/2-.075,bottom-.095,c1+sw/2+.075,bottom-.01,-.20,.095,STONE,'End bay | sill')
    brick_arch(w,c1,bottom+sh+.065,sw*.68,.47,.23,'End bay | blind brick head',lod)
    for k in [-1,1]:
        w.rect(c1+k*sw*.68-.07,bottom-.035,c1+k*sw*.68+.07,bottom+sh+.07,-.055,.04,CLAY,'End bay | red brick jamb')
    for j in range(29):
        zz=1.01+.30*j
        w.rect(w.length-.245,zz,w.length,zz+.289,-.07,.033,CLAY if j%3 else ALT,'Return | bonded vertical corner')
    pipe_x=u(-4.05)
    path=[w.point(pipe_x+.11,10.64,.15),w.point(pipe_x+.11,10.34,.15),w.point(pipe_x,10.23,.16),w.point(pipe_x,5.52,.16),w.point(pipe_x+.14,5.35,.24),w.point(pipe_x+.14,.68,.12)]
    b.tube(path,.062,WATER,12 if lod else 18,'Arcade | rainwater pipe at terminal bay')
    return w
def rect_window(w,x,z,X,Z,label,lod):
    span=X-x;center=(x+X)/2
    sash(w,center,z,span,Z,0,lod,label,cols=2,rails=2,depth=-.112)
    w.rect(x-.065,z-.072,X+.065,z-.008,-.145,.072,STONE,label+' stone sill')
    w.rect(x-.07,Z+.01,X+.07,Z+.135,-.06,.038,CLAY,label+' flat head')
def side_face(b,lod,L):
    w=Wall(b,(0,0),(0,L['rear_y']))
    holes=[Polygon(i['outline_yz'])for i in three_arches.opening_contours(L)]
    holes.extend(box(*a)for a in L['side_upper'])
    louvre=L['side_louvre'];holes.append(box(*louvre))
    # The porch's rear door and the small circular opening are on the wall
    # observed through its main arch in the 2013 photograph.
    door=box(10.18,.31,11.52,3.04);circle=__import__('shapely').geometry.Point(12.20,2.28).buffer(.232,quad_segs=18)
    holes.extend([door,circle])
    shell=box(0,0,w.length,L['side_eave_z']).difference(unary_union(holes));w.prism(set_precision(shell,1e-7),-.33,0,BRICK,'Return | grey brick wall with cut openings')
    w.rect(0,0,7.15,1.28,-.065,.012,GREY,'Return | rendered lower wall')
    w.rect(0,1.28,7.15,1.338,-.05,.028,STONE,'Return | plinth ledge')
    shell_band(w,L['floor_z']-.015,'Return | projecting red band')
    for j,window in enumerate(L['side_upper']):rect_window(w,*window,f'Return {j+1} | upper sash',lod)
    x,z,X,Z=louvre;w.prism(box(*louvre),-.24,-.20,DARK,'Return | ventilation recess')
    for i in range(7):
        zz=z+.055+(Z-z-.11)*i/7;w.rect(x+.04,zz,X-.04,zz+.055,-.132,-.061,FRAME,'Return | red louvre blades')
    w.prism(box(*louvre).difference(box(x+.06,z+.06,X-.06,Z-.06)),-.14,-.008,CLAY,'Return | vent surround')
    w.prism(door,-.16,-.12,DOOR,'Porch | dark recessed door')
    w.prism(box(7.53,.26,13.16,4.27).difference(unary_union([door,circle])),-.035,.04,OCHRE,'Porch | plastered back')
    w.prism(circle,-.24,-.206,DARK,'Porch | round opening in shadow')
    for i in range(2):w.rect(10.27,.44+i*1.26,11.43,1.54+i*1.26,-.123,-.091,DOOR,'Porch | door panels')
    for j in range(30):
        zz=1.015+.30*j
        w.rect(0,zz,.215,zz+.289,-.042,.018,CLAY if j%3 else ALT,'Return | corner bricks')
    # Downpipe with a true offset at the projecting upper string course.
    path=[w.point(.35,9.97,.13),w.point(.35,5.36,.135),w.point(.35,5.16,.30),w.point(.35,5.02,.30),w.point(.35,4.85,.115),w.point(.35,.35,.115)]
    b.tube(path,.070,WATER,12 if lod else 18,'Return | cream rainwater pipe')
    for zz in [1.9,4.1,6.3,8.5]:w.rect(.24,zz-.025,.46,zz+.025,.06,.147,ALT,'Return | pipe saddle')
def porch(b,lod,L):
    cfg=L['porch'];px=cfg['depth_x'];a=cfg['start_y'];c=cfg['end_y'];deck=cfg['deck_z'];top=cfg['parapet_z']
    for k,(A,B) in enumerate([((0,a),(px,a)),((px,a),(px,c)),((px,c),(0,c))]):
        w=Wall(b,A,B);span=w.length
        if k==2:
            w.rect(0,deck-.06,span,deck+.055,-.27,.072,DECK,'Porch | far slab and drip')
            w.rect(0,deck+.055,span,top,-.19,.018,CEMENT,'Porch | parapet return')
            w.rect(0,top-.035,span,top+.09,-.245,.084,DECK,'Porch | return cap')
            continue
        tag=['Porch | short garden return','Porch | long entrance','Porch | rear return'][k]
        width=span-(1.18 if k==1 else .65);spring=3.03 if k==1 else 2.98;rise=1.06 if k==1 else .99;bot=.30
        shape=opening(span/2,bot,width,spring+rise-bot,rise,40 if not lod else 24)
        spandrel=box(0,bot,span,deck).difference(shape)
        w.prism(set_precision(spandrel,1e-7),-.29,0,BRICK,tag+' pierced wall')
        brick_arch(w,span/2,spring,width/2,rise,.245,tag,lod)
        for sgn in (-1,1):
            center=span/2+sgn*(width/2+.078);w.rect(center-.081,bot,center+.081,spring,-.22,.05,CLAY,tag+' jamb')
            w.rect(center-.16,spring-.07,center+.16,spring+.018,-.24,.105,STONE,tag+' impost cap')
        w.rect(0,deck-.06,span,deck+.06,-.26,.075,DECK,tag+' horizontal drip')
        w.rect(0,deck+.055,span,top,-.19,.018,CEMENT,tag+' solid parapet')
        w.rect(0,top-.035,span,top+.09,-.245,.084,DECK,tag+' coping')
    b.plan_prism(box(0,a,px,c),deck-.145,deck,DECK,'Porch | upper terrace slab')
    b.plan_prism(box(0,a,px+.03,c),.05,.30,DECK,'Porch | raised floor')
    for i in range(3):b.plan_prism(box(px+i*.275,a+.38,px+(i+1)*.275,c-.38),0,.27-.085*i,STONE,'Porch | three entrance treads')
    for xx,yy in [(px-.10,a+.1),(px-.1,c-.1)]:
        b.box((xx,yy,1.61),(.35,.36,2.71),CLAY,label='Porch | red corner of square pier')
def roof_slab(b,pts,mat,name,thickness=.135):
    pts=np.array(pts,float)
    if np.cross(pts[1]-pts[0],pts[2]-pts[0])[2]<0:pts=pts[::-1]
    four=len(pts);bottom=pts.copy();bottom[:,2]-=thickness
    vv=np.r_[bottom,pts];faces=[]
    for k in range(1,four-1):
        faces.extend([(0,k+1,k),(four,four+k,four+k+1)])
    faces.extend((i,(i+1)%four,(i+1)%four+four,i+four)for i in range(four));b.add(vv,faces,mat,name)
def roof(b,lod,L):
    x=L['front_min_x'];y=L['rear_y'];e=L['eave_z'];r=L['roof_ridge_z'];cx=L['roof_end_axis'];we=L['roof_gable_width']/2;crest=L['roof_gable_crest'];mid=y*.49
    left=x-.36;xleft=cx-we;right=.42;front=-.48;back=y+.41;side_eave=L['side_eave_z']
    # Cross gable runs back from the tall terminal window; the other ridge
    # runs over the long row of four round arches. Their valleys join.
    valley=(cx,mid,r)
    for pts,key in [([(left,front,e),(xleft,front,e),(xleft,mid,r),(left,mid,r)],'long garden slope'),([(left,mid,r),(xleft,mid,r),(xleft,back,e),(left,back,e)],'outer rear slope'),([(xleft,front,e),(cx,front,crest),valley,(xleft,mid,r)],'near intersecting slope'),([(cx,front,crest),(right,front,side_eave),(right,mid,side_eave),valley],'near end slope'),([(xleft,mid,r),valley,(cx,back,crest-.46),(xleft,back,e)],'returning valley'),([valley,(right,mid,side_eave),(right,back,side_eave),(cx,back,crest-.46)],'rear end slope')]:
        roof_slab(b,pts,TILE,'Roof | '+key,.16)
    end=Wall(b,(xleft,0),(right,0))
    end.prism(Polygon([(0,e-.13),(end.length,e-.13),(end.length,side_eave-.12),(cx-xleft,crest-.18)]),-.27,0,BRICK,'Roof | terminal garden gable')
    for label,p0,p1 in [('garden eave',(left,front,e-.055),(xleft,front,e-.055)),('western eave',(left,front,e-.06),(left,mid,r-.06)),('terminal rake A',(xleft,front,e-.06),(cx,front,crest-.06)),('terminal rake B',(cx,front,crest-.06),(right,front,side_eave-.06)),('porch eave',(right,front,side_eave-.07),(right,back,side_eave-.07)),('long high ridge',(left,mid,r+.035),valley),('terminal ridge',(cx,front,crest+.025),valley),('rear ridge',valley,(cx,back,crest-.425))]:
        b.tube([p0,p1],.10 if 'ridge' in label else .095,RIDGE if 'ridge'in label else EAVES,12 if lod else 18,'Roof | '+label)
def add_building(b,lod,L):
    main_face(b,lod,L);side_face(b,lod,L);porch(b,lod,L)
    x=L['front_min_x'];y=L['rear_y'];e=L['eave_z']
    for tag,a,c in [('unseen lateral return',(x,y),(x,0)),('rear volume',(0,y),(x,y))]:
        w=Wall(b,a,c);w.rect(0,0,w.length,e-.08,-.27,-.015,BRICK,'Shell | '+tag)
    b.plan_prism(box(x,0,0,y),-.13,.015,GREY,'Shell | ground closure')
    roof(b,lod,L)
