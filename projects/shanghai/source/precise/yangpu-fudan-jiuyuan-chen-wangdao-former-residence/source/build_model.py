"""Garden-facing section of Chen Wangdao's former residence in Fudan's Jiuyuan."""
import argparse,json,sys
from pathlib import Path
import numpy as np
from shapely.geometry import box as rect,Polygon
from shapely.ops import unary_union
from finishes import PALETTE,PLASTER,TILE,SAND,STEEL,GLASS,GLASS2,SHADE,DRAIN
HERE=Path(__file__).resolve().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
sys.path.insert(0,str(PROJECT/'tools'))
import package_architectural_model
sys.path.insert(0,str(PROJECT/'source/precise/hongkou-tanggu-road-apartment-dated-crown/source'))
from crown_builder import CrownBuilder
ID='yangpu-fudan-jiuyuan-chen-wangdao-former-residence'
META=dict(id=ID,name='复旦玖园陈望道旧居花园立面',address='国福路51号，国顺路650弄复旦第九宿舍内',heritage_group='5G018（宿舍群）',scope='花园侧两层弧窗、中央悬挑阳台、退台窗和瓦檐。沿可见房屋截面收束。',period='1930年代建，按2018年修缮后、2019年实照表现',viewer_page='fudan-jiuyuan-chen-wangdao-former-residence.html',geometry_license='MIT',texture_license='Original project-generated roughcast and green roofing, MIT',license_url='https://opensource.org/license/mit',photo_author='Fayhoo, 2019, CC BY-SA 3.0',photo_source='https://commons.wikimedia.org/wiki/File:Residence_of_Chen_Wangdao.jpg',photos_embedded=False,third_party_models_embedded=False,copyright='Original geometry and procedural textures, MIT. Fayhoo photograph referenced under CC BY-SA 3.0.')
M=json.loads((HERE.parent/'measurements/garden-front-registration.json').read_bytes())['fields']
C=json.loads((HERE.parent/'measurements/garden-bay-two-stations.json').read_bytes())
def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=label)
def face(b,shape,front,back,mat,label):
    b.prism(shape,-back,-front,lambda u,z,d:(u,-d,z),mat,label)
def window(b,a,c,z0,z1,columns,rows,label,door=False):
    a,c=np.asarray(a,float),np.asarray(c,float);length=np.linalg.norm(c-a);t=(c-a)/length;i=np.array([-t[1],t[0]])
    def part(s0,s1,h0,h1,f,r,m,title):
        mid=a+t*((s0+s1)/2)+i*((f+r)/2)
        basis=np.array([[*t,0],[*i,0],[0,0,1]])
        b.box([*mid,(h0+h1)/2],[s1-s0,r-f,h1-h0],m,basis=basis,label=f'{label} | {title}')
    split=[z0+(z1-z0)*h for h in rows]
    for col in range(columns):
        l=length*col/columns;r=length*(col+1)/columns
        for row,(bot,top) in enumerate(zip(split,split[1:])):
            glass=GLASS if (col+2*row)%3!=1 else GLASS2
            part(l+.012,r-.012,bot+.014,top-.014,.116,.138,glass,f'glass {col+1}.{row+1}')
    for j in range(columns+1):
        s=length*j/columns;thick=.044 if j in (0,columns) else .037
        part(max(0,s-thick/2),min(length,s+thick/2),z0,z1,.047,.123,STEEL,f'stile {j+1}')
    for j,z in enumerate(split):
        w=.049 if j in (0,len(split)-1)else .032
        part(0,length,max(z0,z-w/2),min(z1,z+w/2),.04,.118,STEEL,f'rail {j+1}')
    if door:
        part(.032,length-.032,z0+.018,z0+.40,.056,.108,STEEL,'kick panel')
def coped_box(b,x0,x1,y0,y1,z,thickness,label):
    block(b,x0,x1,y0,y1,z,z+thickness,SAND,label)
def sill(b,x0,x1,y,z,label):
    block(b,x0-.04,x1+.04,y-.075,y+.105,z-.151,z+.014,SAND,label)
def roof(b,x0,x1,y0,y1,z,zback,label):
    # A short roof section above this wing, cut behind the photograph-visible front slope.
    rise=zback-z
    b.prism(Polygon([(y0,z-.11),(y1,zback-.11),(y1,zback),(y0,z)]),x0,x1,lambda u,v,d:(d,u,v),TILE,label)
def hipped_roof(b,x0,x1,y0,depth,z,rise,hip,label):
    # Two visible hip ends flank the shallow ridge, behind the garden eaves.
    a=np.array([x0,y0,z]);c=np.array([x1,y0,z]);d=np.array([x1,y0+depth+.20,z+rise-.12]);e=np.array([x0,y0+depth+.20,z+rise-.12])
    left=np.array([x0+hip,y0+depth,z+rise]);right=np.array([x1-hip,y0+depth,z+rise])
    def panel(vertices,title):
        n=len(vertices);vertices=np.array(vertices);points=np.vstack([vertices-[0,0,.085],vertices])
        faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
        faces.extend([(j,(j+1)%n,(j+1)%n+n,j+n)for j in range(n)]);b.add(points,faces,TILE,label+' '+title)
    panel([a,c,right,left],'garden pitch');panel([a,left,e],'left hip');panel([c,d,right],'right hip');panel([e,left,right,d],'rear strip')
    for u,v,title in [(a,left,'left roll'),(c,right,'right roll'),(left,right,'ridge roll')]:
        b.tube([u+[0,0,.024],v+[0,0,.024]],.046,TILE,8,label+' '+title)
def band(b,x0,x1,y,z,label):
    block(b,x0,x1,y-.10,y+.02,z-.12,z,SAND,label+' cap')
    block(b,x0,x1,y-.035,y+.035,z-.35,z-.12,PLASTER,label+' frieze')
    # Small blind semicircular recesses read in the plaster below the eaves.
    count=max(3,round((x1-x0)/.21));w=(x1-x0)/count
    for j in range(count):
        cx=x0+(j+.5)*w;r=.30*w
        arch=[(cx+r*np.cos(t),z-.29+r*np.sin(t))for t in np.linspace(0,np.pi,10)]
        arch.extend([(cx-r,z-.32),(cx+r,z-.32)])
        face(b,Polygon(arch),y-.043,y-.026,SAND,label+f' arch {j+1}')
def facade(b):
    x0,x1=M['wall_l'],M['wall_r'];h=M['ceiling'];u0,u1=M['upper_left'],M['upper_right'];z0,z1=M['upper_low'],M['upper_high']
    g=unary_union([rect(0,0,M['dw'],2.75),rect(M['dw'],M['sill'],M['cr'],2.75)])
    shape=rect(x0,0,x1,h).difference(unary_union([g,rect(u0,z0,u1,z1)]))
    face(b,shape,0,.32,PLASTER,'Middle | main pierced wall')
    window(b,(0,0),(M['dw'],0),0,2.75,2,[0,.44,.70,.85,1],'Door',True)
    window(b,(M['dw'],0),(M['cr'],0),M['sill'],2.75,4,[0,.21,.68,.81,1],'Hall')
    window(b,(u0,0),(u1,0),z0,z1,6,[0,.30,.54,.78,1],'Upper')
    sill(b,M['dw'],M['cr'],0,M['sill'],'Middle | base sill')
    left,right=M["bal_l"],M["bal_r"]
    # Outer surface is the calibrated lip; the open deck reaches the wall.
    front=M['bal_y']
    block(b,left,right,front,.17,M['bal_under'],M['bal_under']+.13,PLASTER,'Balcony | cantilever underside')
    block(b,left,right,front,front+.14,M['bal_under']+.13,M['bal_top']-.075,PLASTER,'Balcony | front parapet')
    for x in (left,right-.13):block(b,x,x+.13,front,.08,M['bal_under']+.13,M['bal_top']-.075,PLASTER,'Balcony | return')
    coped_box(b,left-.02,right+.02,front-.032,front+.15,M['bal_top']-.075,.075,'Balcony | coping')
    band(b,x0-.05,x1+.02,0,h,'Middle | cornice')
    hipped_roof(b,x0-.10,x1+.09,-.09,1.35,h+.05,1.04,1.18,'Middle | green hipped roof')
    # The left single-storey wall has two true open rectangular vents under its coping.
    y=M['wing_y'];x=M['left_wall'];top=M['wing_top'];l,r=M['wing_win_l'],M['wing_win_r'];low,hi=M['wing_low'],M['wing_hi']
    vpos=[(x+.68,x+1.52),(x+2.12,x+2.97)];holes=[rect(l,low,r,hi)]
    for v0,v1 in vpos:holes.append(rect(v0,top-.56,v1,top-.32))
    face(b,rect(x,0,x0+.08,top).difference(unary_union(holes)),y,y+.34,PLASTER,'West | pierced wing')
    window(b,(l,y),(r,y),low,hi,4,[0,.29,.56,.82,1],'West')
    for j,(v0,v1) in enumerate(vpos):
        for i in range(1,5):
            wx=v0+(v1-v0)*i/5;block(b,wx-.028,wx+.028,y+.04,y+.17,top-.56,top-.32,SAND,f'Vent | divider {j+1}.{i}')
        block(b,v0,v1,y+.31,y+.34,top-.56,top-.32,SHADE,'Vent | inner shade')
    sill(b,l,r,y,low,'West | sill');roof(b,x-.08,x0+.10,y-.09,y+.45,top,top+.12,'West | parapet tile')
    recessed=y+1.68;wleft=x+.49;wins=[x+1.85,x0+.02,top-.08,top+.93]
    face(b,rect(wleft,0,x0+.16,top+1.94).difference(rect(*[wins[0],wins[2],wins[1],wins[3]])),recessed,recessed+.28,PLASTER,'West | setback wing')
    window(b,(wins[0],recessed),(wins[1],recessed),wins[2],wins[3],4,[0,.53,.80,1],'Setback')
    band(b,wleft-.06,x0+.1,recessed,top+1.94,'West | upper cornice')
    hipped_roof(b,wleft-.10,x0+.30,recessed-.10,1.34,top+2.0,.98,1.26,'West | green hipped roof')
    # End and floor patches close the visible wing sections.
    block(b,x,x+.22,y,y+2.5,0,top,PLASTER,'West | outer return')
    block(b,wleft,wleft+.20,recessed,recessed+1.50,top,top+1.91,PLASTER,'West | high return')
    block(b,x0,x0+.22,0,recessed+.14,0,h,PLASTER,'Middle | west return')
    block(b,x0,x1,0,1.11,h-.14,h,PLASTER,'Middle | roof bearing')
    b.tube([(x0+.20,-.065,.02),(x0+.20,-.065,h-.16)],.038,DRAIN,10,'Middle | downpipe')
def arc_point(angle,r):
    cx,cy=C['bay_centre'];return np.array([cx+r*np.sin(angle),cy-r*np.cos(angle)])
def arcwall(b,l,r,bottom,top,rout,rin,mat,label,nstep):
    angles=np.linspace(l,r,max(2,int(np.ceil((r-l)*nstep))+1))
    ring=np.vstack(([arc_point(t,rout)for t in angles],[arc_point(t,rin)for t in reversed(angles)]))
    b.plan_prism(Polygon(ring),bottom,top,mat,label)
def curved_front(b,lod):
    r=C['radius'];bands=C['bands'];n=10 if lod else 22;bounds=(-1.50,1.48);top=8.58
    ground=[(a[0]+d[0])/2 for a,d in zip(bands['ground-head']['jamb_angles_and_error'],bands['ground-sill']['jamb_angles_and_error'])]
    upper=[(a[0]+d[0])/2 for a,d in zip(bands['upper-head']['jamb_angles_and_error'],bands['upper-sill']['jamb_angles_and_error'])]
    intervals=[(bands['ground-sill']['height'],bands['ground-head']['height'],ground,'Bay G'),(bands['upper-sill']['height'],bands['upper-head']['height'],upper,'Bay U')]
    last=0.
    for low,high,edges,title in intervals:
        arcwall(b,*bounds,last,low,r,r-.23,PLASTER,title+' | curved spandrel',n)
        for k,(a,c) in enumerate(zip([bounds[0],edges[1],edges[3],edges[5]],[edges[0],edges[2],edges[4],bounds[1]])):
            arcwall(b,a,c,low,high,r,r-.23,PLASTER,title+f' | solid pier {k+1}',n)
        for k,(a,c) in enumerate(zip(edges[::2],edges[1::2])):
            segments=3 if k==1 else 1
            angles=np.linspace(a,c,segments+1)
            for j,(e,f) in enumerate(zip(angles,angles[1:])):
                cols=2 if k==1 or (k==0 and title=='Bay G') else 1
                window(b,arc_point(e,r-.038),arc_point(f,r-.038),low,high,cols,[0,.22,.46,.66,.82,1],title+f' {k+1}.{j+1}')
        arcwall(b,*bounds,low-.170,low+.052,r+.080,r-.25,SAND,title+' | projecting sill',n)
        last=high
    arcwall(b,*bounds,last,top,r,r-.24,PLASTER,'Bay roof | round parapet',n)
    arcwall(b,*bounds,top,top+.10,r+.06,r-.28,SAND,'Bay roof | coping',n)
    # A recessed flat deck is bounded by the photographed parapet and the high front wall.
    angles=np.linspace(*bounds,2*n+1)
    b.plan_prism(Polygon([arc_point(t,r-.10) for t in angles]),top-.36,top-.25,SAND,'Bay roof | deck cut')
    lp=arc_point(bounds[0],r);rp=arc_point(bounds[1],r)
    for side,pt in [('L',lp),('R',rp)]:
        block(b,pt[0]-.09,pt[0]+.09,pt[1]-.02,2.10,0,top,PLASTER,f'Bay roof | {side} return')
def crown(b):
    # The parapet masks most of the tower window, its exposed upper rail appears in both garden photographs.
    lx,rx=3.81,8.53;y=1.8;h=11.17
    face(b,rect(lx,0,rx,h).difference(rect(4.49,8.84,7.52,10.0)),y,y+.24,PLASTER,'Tower | setback window wall')
    window(b,(4.49,y),(7.52,y),8.84,10.0,5,[0,.44,.80,1],'Tower')
    block(b,lx,lx+.20,y,y+1.30,0,h,PLASTER,'Tower | left return')
    block(b,rx-.2,rx,y,y+1.30,0,h,PLASTER,'Tower | right return')
    band(b,lx-.04,rx+.04,y,h,'Tower | arched frieze')
    roof(b,lx-.11,rx+.11,y-.12,y+.85,h+.02,h+.24,'Tower | tile eave')
    block(b,8.38,8.93,1.98,2.68,h-.15,12.61,PLASTER,'Tower | chimney')
    block(b,8.35,8.97,1.95,2.72,12.52,12.65,SAND,'Tower | chimney cap')
    block(b,2.03,lx+.08,2.5,3.55,0,9.58,PLASTER,'Tower | intermediate setback')
    band(b,2.02,lx+.09,2.5,9.58,'Tower | intermediate cornice')
    roof(b,1.94,lx+.22,2.38,3.49,9.60,9.83,'Tower | intermediate roof')
def build(lod=False):
    b=CrownBuilder(PALETTE);facade(b);curved_front(b,lod);crown(b)
    block(b,-1.56,4.34,-.98,.26,-.13,0,SAND,'Ground | threshold landing')
    block(b,-1.63,4.42,-1.40,.26,-.23,-.13,SAND,'Ground | garden step')
    return b
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('output',type=Path);ap.add_argument('--lod',action='store_true')
    a=ap.parse_args();b=build(a.lod);q=b.save(a.output,META);print(len(b.parts),q['triangles'],q['sha256'])
