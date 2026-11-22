"""Build the curved masonry and two continuous pale bands visible in the district photograph."""
from math import ceil,cos,floor,pi,sin
from pathlib import Path
import numpy as np
from PIL import Image

HERE=Path(__file__).resolve().parent
ID='changning-yuyuan-749-no65-red-brick-corner'
BRICK='Running-bond russet brickwork'
STONE='Warm limestone-coloured stucco'
SHADE='Recessed concrete drip'
BASE='Buff cement plinth'
GLASS='Dark blue-green glass'
FRAME='Dark painted window frame'
JAMB='Brick reveal'
HEADER='Red soldier headers'
CAP='Pale coping'
ROOF='Weathered ochre render'
DRAIN='Aged brown drainpipe'
METAL='Slender parapet ironwork'
PALETTE={name:dict(color=colour,roughness=rough) for name,colour,rough in [
 (BRICK,[.99,.99,.99],.94),(STONE,[.86,.78,.61],.96),(SHADE,[.39,.33,.27],.93),
 (BASE,[.51,.43,.32],.98),(GLASS,[.035,.061,.061],.37),(FRAME,[.070,.052,.041],.76),
 (JAMB,[.41,.147,.087],.95),(HEADER,[.55,.195,.113],.91),(CAP,[.83,.76,.60],.93),
 (ROOF,[.65,.43,.26],.96),(DRAIN,[.13,.106,.073],.81),(METAL,[.135,.142,.132],.69)]}
R=1.72
HALF=pi*R/4
LEFT=-3.51
RIGHT=2.08
H=7.92
COURSE=.081
STRETCH=.246
WINDOWS=[(-.254,.172,1.188,1.915),(-2.852,-2.329,1.357,2.101),(-2.660,-1.773,3.397,4.211),(-2.353,-1.859,5.631,6.383)]
BELTS=[(2.734,3.540),(6.887,7.710)]
PLINTH=.522
DRAIN_S=-.876
CROWN_LIFT=.838

def texture():
    target=HERE/'red-running-bond.png'
    if not target.exists():
        # Map every tile to its photographed running-bond course on the unwrapped wall.
        width,height=760,1024
        yy,xx=np.mgrid[:height,:width]
        coord=(RIGHT-LEFT)*xx/(width-1)
        level=H*(1-yy/(height-1))
        row=np.floor(level/COURSE).astype(int)
        moved=coord+(row%2)*STRETCH/2
        column=np.floor(moved/STRETCH).astype(int)
        seed=np.random.default_rng(452)
        shades=seed.normal(0,8,(110,28))
        shade=shades[row,column]+seed.normal(0,3.1,(height,width))
        dx=np.minimum(moved%STRETCH,STRETCH-moved%STRETCH)
        dy=np.minimum(level%COURSE,COURSE-level%COURSE)
        mortar=1-np.clip(np.minimum(dx/.0045,dy/.0038),0,1)
        clay=np.stack((175+shade,77+shade*.68,49+shade*.48),axis=-1)
        joint=np.array([203,153,125])[None,None,:]+seed.normal(0,2,(height,width,1))
        image=clay*(1-mortar[:,:,None])+joint*mortar[:,:,None]
        Image.fromarray(np.uint8(np.clip(image,0,255))).quantize(96).save(target)
    PALETTE[BRICK]['texture']=str(target)

def pos(s,z,d=0):
    # d is the distance outward from the face; s follows the circle and its two tangents.
    arc=max(-HALF,min(HALF,s));a=arc/R
    dx=s-arc
    return ((R+d)*sin(a)+dx*cos(a),R-(R+d)*cos(a)+dx*sin(a),z)

def make_patch(s0,s1,z0,z1,d0,d1,step):
    # GLB coordinates are derived by the shared builder from these east/depth/up coordinates.
    segments=max(1,ceil((s1-s0)/step)) if s0<HALF and s1>-HALF else 1
    ss=sorted(set([s0,s1]+[x for x in [-HALF,HALF] if s0<x<s1]+[s0+(s1-s0)*i/segments for i in range(1,segments)]))
    v=[];f=[];uv=[]
    for s in ss:
        for z,d in [(z0,d0),(z1,d0),(z0,d1),(z1,d1)]:
            v.append(pos(s,z,d));uv.append([(s-LEFT)/(RIGHT-LEFT),1-z/H])
    for i in range(len(ss)-1):
        q=i*4
        f.extend([[q,q+4,q+5,q+1],[q+2,q+3,q+7,q+6],[q+1,q+5,q+7,q+3],[q,q+2,q+6,q+4]])
    q=len(v)-4;f.extend([[0,1,3,2],[q,q+2,q+3,q+1]])
    return v,f,uv

def patch(b,s0,s1,z0,z1,front,back,material,label,step):
    v,f,uv=make_patch(s0,s1,z0,z1,front,back,step)
    b.add(v,f,material,label)
    if material==BRICK:b.parts[-1]['texcoords']=uv

def stone_band(b,low,high,i,step):
    cuts=[(low-.047,low,.100,SHADE),(low,low+.070,.133,STONE),
          (low+.070,high-.068,.104,STONE),(high-.068,high-.022,.153,CAP),
          (high-.022,high+.018,.126,CAP)]
    for j,(za,zb,out,material) in enumerate(cuts):
        for l,r,name in [(LEFT,-HALF,'west return'),(-HALF,HALF,'curved nose'),(HALF,RIGHT,'short return')]:
            if i==0 and name=='west return':
                # The pale band crosses below the left sash sill, not across the glazing.
                a,c,sill,_=WINDOWS[2]
                label='Lower belt '+name+' '+str(j)
                for west,east in [(l,a-.062),(c+.062,r)]:
                    if east>west:patch(b,west,east,za,zb,out,-.012,material,label,step)
                if za<sill-.056:
                    patch(b,a-.062,c+.062,za,min(zb,sill-.056),out,-.012,material,label,step)
            else:patch(b,l,r,za,zb,out,-.012,material,('Lower' if i==0 else 'Upper')+' belt '+name+' '+str(j),step)

def band_wall(b,far):
    step=.23 if far else .105
    xcuts=sorted(set([LEFT,-HALF,0,HALF,RIGHT]+[x for a,c,_,_ in WINDOWS for x in (a,c)]))
    zcuts=sorted(set([.46,H]+[z for _,_,v,h in WINDOWS for z in (v,h)]))
    for a,c in zip(xcuts,xcuts[1:]):
        for za,zb in zip(zcuts,zcuts[1:]):
            if any(l<=(a+c)/2<=r and lo<=(za+zb)/2<=hi for l,r,lo,hi in WINDOWS):continue
            patch(b,a,c,za,zb,.0,-.190,BRICK,'Curved and tangent masonry',step)
    if not far:
        # Groups of eight courses keep the raw geometry editable while preserving each recessed joint.
        for block in range(0,int(H/COURSE)+1,8):
            vs=[];fs=[];uv=[]
            for course in range(block,min(block+8,int(H/COURSE)+1)):
                bottom=course*COURSE+.003;top=(course+1)*COURSE-.003
                if bottom<PLINTH or top>BELTS[-1][0] or any(lo-.06<bottom<hi+.025 for lo,hi in BELTS):continue
                for j in range(-2,int((RIGHT-LEFT)/STRETCH)+2):
                    a=LEFT+(j-.5*(course%2))*STRETCH+.0035;c=a+STRETCH-.007
                    a=max(LEFT+.002,a);c=min(RIGHT-.002,c)
                    if c-a<.025 or any(a<r+.003 and c>l-.003 and bottom<hi+.003 and top>lo-.003 for l,r,lo,hi in WINDOWS):continue
                    # Only the outer skin and short returns of each detailed brick are needed.
                    v,f,uvs=make_patch(a,c,bottom,top,.005,-.0003,.10)
                    offset=len(vs);vs.extend(v);uv.extend(uvs);fs.extend([[offset+k for k in face] for face in f if face!=f[1]])
            if vs:
                b.add(vs,fs,BRICK,'Rounded brick courses '+str(block+1));b.parts[-1]['texcoords']=uv
    patch(b,LEFT,RIGHT,0,PLINTH,.023,-.195,BASE,'Continuous curved cement plinth',step)
    for i,(lo,hi) in enumerate(BELTS):stone_band(b,lo,hi,i,step)

def windows(b,step):
    for i,(l,r,lo,hi) in enumerate(WINDOWS):
        name=['Curved-wall ground light','Left ground-floor light','Left intermediate window','Left upper window'][i]
        patch(b,l,r,lo,hi,-.136,-.16,GLASS,name+' glass',step)
        for a,c in [(l,l+.023),(r-.023,r)]:patch(b,a,c,lo,hi,-.102,-.14,FRAME,name+' jamb',step)
        for za,zb in [(lo,lo+.029),(hi-.031,hi)]:patch(b,l,r,za,zb,-.102,-.14,FRAME,name+' rail',step)
        if i>=2:
            patch(b,l,r,lo+(hi-lo)*.66,lo+(hi-lo)*.66+.034,-.10,-.14,FRAME,name+' transom',step)
        if i==0:
            for j in range(11):
                a=l-.06+j*(r-l+.12)/11;c=l-.06+(j+1)*(r-l+.12)/11-.003
                patch(b,a,c,hi+.006,hi+.153,.017,-.025,HEADER,'Radial soldier lintel',step)
                patch(b,a,c,lo-.125,lo-.017,.085,-.04,HEADER,'Out-projecting brick sill',step)
            patch(b,l-.061,r+.061,lo-.015,lo+.008,.092,-.03,CAP,'Thin cap on narrow sill',step)
        else:
            width=.062 if i==2 else .035
            for a,c in [(l-width,l),(r,r+width)]:patch(b,a,c,lo-.038,hi+.069,.034,-.032,BASE,name+' masonry surround',step)
            patch(b,l-width,r+width,hi,hi+.070,.056,-.024,CAP,name+' lintel',step)
            patch(b,l-width,r+width,lo-.056,lo,.073,-.028,CAP,name+' projecting sill',step)

def roof_point(s,z,depth):
    # The set-back roof pavilion has a sharp plan corner while the bay beneath continues around the curve.
    # A miter intersects the two offset roof faces on their common ridge.
    # Mapping both endpoints to that ridge gives continuous inner and outer skins.
    return (s*cos(pi/4),.15+abs(s)*sin(pi/4)-depth/cos(pi/4),z)

def roof_panel(b,l,r,lo,hi,front,back,mat,label):
    pts=[roof_point(s,z,d) for s in [l,r] for z,d in [(lo,front),(hi,front),(lo,back),(hi,back)]]
    b.add(pts,[[0,4,5,1],[2,3,7,6],[1,5,7,3],[0,2,6,4],[0,1,3,2],[4,6,7,5]],mat,label)

def rooftop(b,far):
    for side,(l,r) in enumerate([(-3.82,0),(0,2.30)]):
        xl=[l,r] if side else [l,-2.75,-1.97,r]
        for a,c in zip(xl,xl[1:]):
            for lo,hi in [(7.64,8.98),(8.98,9.40),(9.40,8.87+CROWN_LIFT)]:
                if side==0 and a==-2.75 and lo==8.98:
                    roof_panel(b,a,c,lo,hi,-.105,-.13,GLASS,'Recessed roof-slot glass')
                    roof_panel(b,(a+c)/2-.016,(a+c)/2+.016,lo,hi,-.018,-.13,FRAME,'Roof slot centre mullion')
                else:roof_panel(b,a,c,lo,hi,0,-.17,ROOF,'Set-back rooftop return '+str(side))
        for lo,hi,d,mat,label in [(8.86,8.94,.223,SHADE,'Angular roof soffit'),(8.94,9.016,.260,CAP,'Roof coping'),(9.016,9.043,.23,BASE,'Flat roof edge')]:
            roof_panel(b,l,r,lo+CROWN_LIFT,hi+CROWN_LIFT,d,-.25,mat,label+' '+str(side))
        for j in range(5 if side==0 else 4):
            t=j/(4 if side==0 else 3);s=l+(r-l)*t
            roof_panel(b,s-.009,s+.009,9.03+CROWN_LIFT,9.32+CROWN_LIFT,.208,.188,METAL,'Parapet iron uprights '+str(side))
        roof_panel(b,l,r,9.302+CROWN_LIFT,9.324+CROWN_LIFT,.213,.187,METAL,'Sloping perspective parapet rail '+str(side))

def pipe(b,s,levels,material,label,r=.029):
    vs=[];faces=[]
    for z,offset in levels:
        x,y,_=pos(s,z,offset)
        for i in range(12):vs.append((x+r*cos(i*pi/6),y+r*sin(i*pi/6),z))
    for j in range(len(levels)-1):
        start=j*12
        for i in range(12):faces.append([start+i,start+(i+1)%12,start+(i+1)%12+12,start+i+12])
    b.add(vs,faces,material,label)

def add_building(b,far=False):
    texture();band_wall(b,far);step=.17 if far else .091
    windows(b,step);rooftop(b,far)
    low,high=BELTS[0]
    profile=[(.02,.08),(low-.14,.08),(low-.028,.193),(high+.04,.193),(high+.16,.08),(BELTS[1][0]-.01,.08)]
    pipe(b,DRAIN_S,profile,DRAIN,'Downpipe alongside rounded bay')
    for z in (.72,2.37,4.43,6.63):pipe(b,DRAIN_S,[(z,.08),(z+.038,.08)],FRAME,'Downpipe fixing collars',.041)
