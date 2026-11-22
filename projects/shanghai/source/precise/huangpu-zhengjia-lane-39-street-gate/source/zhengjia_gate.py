"""The two concrete piers and asymmetric open positions of the iron gate at 39 Yongjia Road."""
from functools import lru_cache
from pathlib import Path
import json
import sys
import numpy as np
from shapely import affinity
from shapely.geometry import Polygon,box
from zheng_gate_camera import REC

SOURCE=Path(__file__).resolve().parent
sys.path.insert(0,str(SOURCE.parents[1]/'hongkou-general-post-office/source/common'))
from sign_lettering import lettering_shapes

def finish(rgb,rough,metal=0.):
    c=np.array(rgb,dtype=float)/255.
    c=np.where(c<=.04045,c/12.92,((c+.055)/1.055)**2.4)
    return dict(color=c.tolist(),roughness=rough,metallic=metal)

POST='Zhengjia gate | weathered grey cement'
EDGE='Zhengjia gate | projecting dark cap edges'
CAP='Zhengjia gate | moulded concrete cap'
IRON='Zhengjia gate | dark green black painted iron'
WORN='Zhengjia gate | rubbed iron edge'
GREEN='Zhengjia gate | green enamel'
WHITE='Zhengjia gate | faded ivory address paint'
FRAME='Zhengjia gate | folded sign edge'
PALE='Zhengjia gate | ivory east panel'
BOX='Zhengjia gate | grey metal light housing'
SHADE='Zhengjia gate | opal outer cover'
PALETTE={POST:finish((146,147,129),.94),EDGE:finish((104,110,103),.94),CAP:finish((149,153,141),.92),
         IRON:finish((47,55,48),.65,.29),WORN:finish((66,72,63),.57,.35),GREEN:finish((30,85,65),.41,.17),
         WHITE:finish((203,213,191),.52),FRAME:finish((92,91,69),.76,.22),PALE:finish((194,184,138),.84),
         BOX:finish((140,146,140),.69,.26),SHADE:finish((195,197,181),.60)}
INK=['Zhengjia gate | ochre lettering','Zhengjia gate | green lettering','Zhengjia gate | blue lettering','Zhengjia gate | red lettering']
PALETTE.update({name:finish(rgb,.72) for name,rgb in zip(INK,[(151,88,45),(48,117,75),(54,103,146),(143,63,50)])})

def block(b,x0,x1,y0,y1,z0,z1,mat,label):
    b.box([(x0+x1)/2,(y0+y1)/2,(z0+z1)/2],[x1-x0,y1-y0,z1-z0],mat,label=label)

def face(b,shape,y0,y1,mat,label):
    b.prism(shape,-y1,-y0,lambda x,z,d:(x,-d,z),mat,label)

def draw_text(b,text,cx,cz,w,h,front,material,label,lod):
    font=SOURCE/'fonts/ZhengjiaNumber.otf'
    for j,(ch,shape)in enumerate(lettering_shapes(text,w,h,font=font)):
        shape=affinity.translate(shape.simplify(.0009 if lod else .00035,preserve_topology=True),xoff=cx,yoff=cz)
        face(b,shape,front-.0019,front+.0002,material,f'{label} {j+1} {ch}')

def pier(b,x,role,lod):
    east=role=='East'
    # The western post extends behind the green plate. Its street face lies
    # right of the cap centre measured between the two silhouettes.
    if not east:x+=.115
    w=.625 if east else .602;dep=.622 if east else .53;front=.018
    cap=2.915 if east else 2.954
    block(b,x-w/2,x+w/2,front,front+dep,0,cap-.118,POST,role+' rendered square pier')
    def corners(hw,y0,y1,z):
        return [(x-hw,y0,z),(x+hw,y0,z),(x+hw,y1,z),(x-hw,y1,z)]
    levels=[(cap-.137,w/2+.009,front-.009,dep+front+.009),
            (cap-.094,w/2+.031,front-.030,dep+front+.030),
            (cap-.058,w/2+.078,front-.084,dep+front+.084),
            (cap+.012,w/2+.089,front-.100,dep+front+.100),
            (cap+.031,w/2+.078,front-.088,dep+front+.088)]
    for i,(a,c)in enumerate(zip(levels,levels[1:])):
        verts=corners(a[1],a[2],a[3],a[0])+corners(c[1],c[2],c[3],c[0])
        b.add(verts,[(0,3,2,1),(4,5,6,7),*((j,(j+1)%4,(j+1)%4+4,j+4)for j in range(4))],
              EDGE if i in (0,2)else CAP,role+f' square weathering course {i+1}')
    # Both piers have a raised square block above the wider flat band.
    block(b,x-.256,x+.256,.092,.552,cap+.030,cap+.187,CAP,role+' raised cap block')
    if east:
        # The small rectangular fixture moves with the cap in the oblique views.
        # The separate white air conditioner on the distant house remains visible behind it.
        block(b,x-.131,x+.131,.174,.384,cap+.186,cap+.224,BOX,'East cap short mounting base')
        block(b,x-.183,x+.183,.154,.399,cap+.224,cap+.378,BOX,'East small rectangular cap fixture')
        block(b,x-.169,x+.169,.142,.155,cap+.238,cap+.369,SHADE,'East pale fixture cover')
    return cap

def enamel(b,x,lod):
    # Lane 39 plate on the western post. The separate green sign on the flanking
    # brick wall is outside the gate. Tiny house ranges cannot be transcribed.
    row=readings()['west_board'];form=Polygon(row['face_xz_m']);lo,base,hi,top=form.bounds
    w=hi-lo;h=top-base;cx=(lo+hi)/2;cz=(base+top)/2;front=-.012
    face(b,form,front+.002,.018,FRAME,'West post address plate folded backing')
    face(b,form.buffer(-.003,join_style=2),front,front+.003,GREEN,'West green enamel lane number')
    draw_text(b,'39弄',cx-w*.105,cz+.022,w*.42,h*.39,front,WHITE,'West lane number',lod)
    draw_text(b,'永嘉路',cx-.014,cz-.048,w*.51,h*.165,front,WHITE,'West street name',lod)

def panel(b,x,lod):
    # The multicoloured painted sign on the east shaft belongs to the photographed
    # 2015 streetscape. Only the larger discernible words are transcribed.
    board=readings()['east_board'];form=Polygon(board['face_xz_m']);face_y=-.027
    face(b,form,face_y+.006,.019,FRAME,'East vertical sign folded surround')
    face(b,form.buffer(-.010,join_style=2),face_y,face_y+.007,PALE,'East yellowed vertical sign face')
    for row in board['paint']:
        mat=INK[row['material_index']]
        for j,paths in enumerate(row['shape_xz_m']):
            shape=Polygon(paths['outline'],paths['holes'])
            if lod:shape=shape.simplify(.0043,preserve_topology=True)
            face(b,shape,face_y-.0018,face_y+.0001,mat,f"East painted panel line {row['line']} fragment {j+1}")

def local_leaf(b,hinge,sign,angle,label,lod):
    """u=0 on the free stile; u=span lies at the hinge. Metal is centred on v=0."""
    span=2.07
    ang=np.radians(angle);along=np.array([sign*np.cos(ang),-np.sin(ang),0.])
    up=np.array([0.,0.,1.]);perp=np.cross(up,along);h=np.array([*hinge,0.])
    def at(u,z,v=0.):
        return h+(u-span)*along+v*perp+z*up
    def rod(u,z,wid,height,depth,mat,kind):
        b.box(at(u,z),[wid,depth,height],mat,[along,perp,up],label+' '+kind)
    def line(coords,r,kind,mat=IRON,offset=0.):
        b.tube([at(u,z,offset)for u,z in coords],r,mat,sides=6 if lod else 10,label=label+' '+kind)
    def crown(u):
        t=np.clip(u/span,0.,1.)
        return 3.07-.58*t*t*(3.-2.*t)
    def scroll(a,z,rx,rz,direction,kind):
        t=np.linspace(-.15,1.,8 if lod else 17)
        phi=.32+4.98*t
        # Rolled flat ornament terminates inside the curve, leaving the end free.
        size=.29+.71*(t+.15)/1.15
        line([(a+direction*rx*r*np.cos(ti),z+rz*r*np.sin(ti))for ti,r in zip(phi,size)],.0085,kind)
    first=.105
    for name,u in [('free stile',0.),('hinge stile',span)]:
        top=crown(u)+.034
        rod(u,(first+top)/2,.037,top-first,.042,IRON,name)
    # The intermediate web is open. The 2020 parking arm crosses in front of
    # this field and has no place in the architectural ironwork.
    for j,z in enumerate((.130,.302,1.183,1.385)):
        rod(span/2,z,span,.036 if j in (0,2)else .026,.035,IRON,f'horizontal frame {j+1}')
    for j,u in enumerate((.236,.405,.573,.741,.895,1.059,1.223,1.381,1.531,1.694,1.851)):
        top=crown(u)-.016
        rod(u,(.153+top)/2,.018 if j not in (0,10) else .023,top-.153,.025,IRON,f'square upright {j+1:02d}')
    for j,off in enumerate([0.,-.216]):
        line([(u,crown(u)+off)for u in np.linspace(0.,span,14 if lod else 31)],.021 if j==0 else .015,f'curved upper rail {j+1}')
    for j,u in enumerate(np.linspace(.112,span-.113,12)):
        scroll(u,.213,.078,.064,1 if j%2==0 else -1,f'lower rolled strap {j+1:02d}')
        scroll(u,1.285,.066,.073,-1 if j%2==0 else 1,f'middle rolled strap {j+1:02d}')
        scroll(u,crown(u)-.116,.076,.083,1 if j%2==0 else -1,f'upper rolled strap {j+1:02d}')
    for col,u in enumerate((.104,span-.091)):
        for j,z in enumerate(np.arange(.470,crown(u)-.23,.245)):
            if 1.08<z<1.48:continue
            scroll(u,z,.069,.101,1 if (j+col)%2 else -1,f'side border {col+1} scroll {j+1:02d}')
    for j,u in enumerate(np.linspace(.035,span-.03,12)):
        base=crown(u)+.010
        line([(u,base-.012),(u,base+.070)],.008,f'finial stem {j+1}')
        # A tapered leaf point can be read against the light top of the court
        # house. Each is a closed solid with a central arris on both faces.
        wid=.025;hh=.135 if j in (0,11) else .104
        verts=[at(u,base+.043),at(u-wid,base+.066),at(u,base+hh),at(u+wid,base+.066),
               at(u,base+.066,.012),at(u,base+.066,-.012)]
        b.add(verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],IRON,label+f' crest point {j+1}')
    for j,z in enumerate((.42,2.19)):
        # The west piers' surveyed face is offset from the moving barrel.
        # A short fixed pintle plate joins the rotating stile to its masonry.
        root_x=2.210 if sign>0 else -2.095
        center=at(span+.019,z)
        b.tube([[root_x,hinge[1]+.025,z],center],.016,WORN,sides=7 if lod else 11,label=label+f' fixed pintle strap {j+1}')
        b.tube([at(span+.019,z-.063),at(span+.019,z+.063)],.029,WORN,sides=7 if lod else 12,label=label+f' hinge barrel {j+1}')

@lru_cache(maxsize=1)
def readings():
    return json.loads((SOURCE.parent/'measurements/zhengjia-gate-fabric.json').read_bytes())

def add_gate(b,lod=False):
    ctr=REC['posts_axis_distance_m']/2
    pier(b,-ctr,'East',lod);pier(b,ctr,'West',lod)
    enamel(b,ctr+.014,lod);panel(b,-ctr,lod)
    # 2015: east leaf folded against the planted return, west leaf points into the lane.
    local_leaf(b,[-2.055,.24],-1.,94.,'East folded iron leaf',lod)
    local_leaf(b,[2.055,.24],1.,55.75,'West partly open iron leaf',lod)
