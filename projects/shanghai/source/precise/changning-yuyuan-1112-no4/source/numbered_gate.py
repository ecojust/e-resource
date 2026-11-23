"""The lane wall, communal notice cabinet, 4 plate and green gate recorded in November 2015."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import box,Polygon,Point

HERE=Path(__file__).absolute().parent
DATA=json.loads((HERE/'gate-registration.json').read_bytes())
INK=json.loads((HERE/'green-four-outlines.json').read_bytes())
GREEN='green enamel number plate'
CREAM='cream enamel lettering'
IRON='green painted gate'
BOARD='notice cabinet patina'
PAPER='matt notice paper'
PALETTE={GREEN:dict(color=[.057,.309,.223],roughness=.42),CREAM:dict(color=[.887,.862,.672],roughness=.57),
         IRON:dict(color=[.118,.206,.175],roughness=.68),BOARD:dict(color=[.197,.177,.137],roughness=.70),
         PAPER:dict(color=[.669,.637,.567],roughness=.94)}

def add(b,m,lod):
    j=DATA['joint_adjustment'];A=np.array(j['plane_origin_xy']);t=np.array(j['tangent_xy']);n=np.array([t[1],-t[0]])
    g=j['camera_2015'];camera=np.array(g['camera_origin_m']);R=np.array(g['world_to_camera_rotation'])
    def mapper(u,z,d):
        pos=A+t*u+n*d
        return (pos[0],pos[1],z)
    def uv(p):
        ray=R.T@np.r_[(np.asarray(p)-g['principal_point_px'])/g['focal_pixels'],1.]
        q=camera+ray*(n@(A-camera[:2]))/(n@ray[:2])
        return [float(t@(q[:2]-A)),float(q[2])]
    def face(op,a,c,mat,label):
        b.prism(op,a,c,mapper,mat,'4-number lane wall/'+label)
    width=j['width_m'];cap=j['cap_top_m'];th=j['cap_thickness_m']
    face(box(0,.02,width,cap-th),-.24,0,m.WALL,'plastered courtyard wall')
    face(box(-.047,cap-th,width+.050,cap),-.29,.058,m.LINTEL,'slightly overhanging concrete coping')
    q=DATA['court_2015']
    for key in ('notice_case','notice_hood','east_post_panel','small_notice','metal_gate'):
        op=Polygon([uv(p)for p in q[key]]);x0,z0,x1,z1=op.bounds
        if key=='notice_case':
            face(op,-.009,.095,BOARD,'glazed communal notice case back')
            inside=op.buffer(-.049,join_style='mitre')
            face(op.difference(inside),.097,.169,BOARD,'notice case projecting perimeter frame')
            face(inside,.099,.110,m.GLASS,'notice glass')
            xm=(x0+x1)/2
            face(inside.intersection(box(xm-.022,z0,xm+.022,z1)),.112,.170,BOARD,'notice centre meeting stile')
            for i,xc in enumerate([.24,.73]):
                x=x0+(x1-x0)*xc;z=z0+(z1-z0)*.37
                face(box(x-.126,z-.085,x+.129,z+.087),.1102,.113,PAPER,'unreadable notice '+str(i+1))
        elif key=='notice_hood':
            face(op,.058,.218,BOARD,'rain hood over notice case')
        elif key=='metal_gate':
            # The 2015 right edge is screened by a nearer wall. Extend the exposed panel only to that edge.
            mid=x0+(x1-x0)*.66
            for i,(left,right) in enumerate([(x0,mid-.011),(mid+.011,x1)]):
                panel=box(left,.06,right,z1)
                face(panel,-.097,-.047,IRON,'exposed green gate leaf '+str(i+1))
                rim=panel.difference(panel.buffer(-.041,join_style='mitre'))
                face(rim,-.05,-.008,IRON,'gate rail '+str(i+1))
                face(box(left+.037,.91,right-.037,.963),-.049,-.008,IRON,'lower horizontal gate strap '+str(i+1))
        else:
            face(op,.001,.018,BOARD if key=='east_post_panel' else PAPER,key)
    green_pts=np.array([uv(p)for p in q['green_four']]);u,z=green_pts.mean(axis=0)
    width=min(.43,max(.25,np.ptp(green_pts[:,0])));height=width*240/350
    left=u-width/2;bottom=z-height/2
    sign=box(left+.010,bottom+.010,left+width-.010,bottom+height-.010).buffer(.010,quad_segs=3)
    face(sign,.001,.015,GREEN,'green enamel 4 plaque')
    for key in ('digit 4','lane inscription'):
        for i,component in enumerate(INK[key]):
            def xy(r):return [(left+x*width,bottom+y*height)for x,y in r]
            mark=Polygon(xy(component['outer']),[xy(r)for r in component['holes']]).buffer(0)
            face(mark,.0152,.0176,CREAM,key+' stroke '+str(i+1))
    if not lod:
        rim=sign.buffer(-.012).boundary.buffer(.0017)
        face(rim,.0151,.017,GREEN,'raised pressed rim')
        for i,(x,y) in enumerate([(.04,.06),(.96,.06),(.04,.94),(.96,.94)]):
            face(Point(left+x*width,bottom+y*height).buffer(.005,quad_segs=3),.016,.020,BOARD,'corner fastener '+str(i+1))
    return b
