"""Window wall and two projecting transparent hoods registered to restoration photograph 2."""
from pathlib import Path
import json
import numpy as np
from shapely.geometry import box, Polygon
from shapely.ops import unary_union

WALL = 'Xiangyang 313 | light yellow rendered window wall'
FRAME = 'Xiangyang 313 | dark painted window joinery'
GLASS = 'Xiangyang 313 | case 2 neutral reflected glass'
SHADE = 'Xiangyang 313 | shadow in upper eastern light'
BRIGHT = 'Xiangyang 313 | pale eastern reflection'
DEEP = 'Xiangyang 313 | shaded inside reveal'
SILL = 'Xiangyang 313 | pale projecting sill'
HOOD = 'Xiangyang 313 | translucent cyan canopy'
TINT = 'Xiangyang 313 | upper light below cyan canopy'
DARK = 'Xiangyang 313 | dark hood edging and pipe'
RACK = 'Xiangyang 313 | shelf and pale metal rails'
PALETTE = {
    WALL:{'color':[.85,.745,.53], 'roughness':.90},
    FRAME:{'color':[.060,.058,.069], 'roughness':.65},
    GLASS:{'color':[.195,.205,.207], 'metallic':.12, 'roughness':.32},
    SHADE:{'color':[.037,.041,.041], 'metallic':.08, 'roughness':.37},
    BRIGHT:{'color':[.542,.561,.526], 'metallic':.09, 'roughness':.41},
    DEEP:{'color':[.025,.029,.031], 'roughness':.90},
    SILL:{'color':[.69,.68,.635], 'roughness':.85},
    HOOD:{'color':[.011,.46,.56], 'alpha':.52, 'roughness':.24, 'metallic':.06},
    TINT:{'color':[.036,.18,.22], 'roughness':.30, 'metallic':.10},
    DARK:{'color':[.041,.044,.044], 'roughness':.53, 'metallic':.31},
    RACK:{'color':[.55,.51,.43], 'roughness':.65, 'metallic':.26},
}
D = json.loads((Path(__file__).parent.parent/'measurements/case2-window-registration.json').read_bytes())
FACES = [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]

def face(b,shape,back,front,material,name):
    b.prism(shape,back,front,lambda x,z,out: (x,-out,z),material,'view 2 | '+name)

def rect(b,left,right,lo,hi,back,front,material,name):
    if right>left and hi>lo:
        face(b,box(left,lo,right,hi),back,front,material,name)

def lintel(b,left,right,z,name):
    rect(b,left-.055,right+.055,z-.063,z,-.011,.087,SILL,name+' projecting white sill')

def fixed_sash(b,name,bounds,rows,columns=(.5,),tinted=False):
    l,lo,r,hi=bounds
    w,h=r-l,hi-lo
    outer=box(l+.006,lo+.006,r-.006,hi-.006)
    rim=.047
    interior=box(l+rim,lo+rim,r-rim,hi-rim)
    # Subtract the central frame from glazing, keeping the rear revealed jamb visible.
    bars=[outer.difference(interior)]
    for x in columns:
        bars.append(box(l+x*w-.019,lo+rim,l+x*w+.019,hi-rim))
    for pct in rows:
        z=lo+h*pct
        bars.append(box(l+rim,z-.016,r-rim,z+.016))
    structure=unary_union(bars)
    face(b,structure,-.125,-.075,FRAME,name+' painted sash and transoms')
    for pane in getattr(interior.difference(structure),'geoms',[interior.difference(structure)]):
        if pane.is_empty:continue
        m=GLASS
        if tinted and pane.centroid.y>lo+.67*h:
            m=TINT
        elif name=='upper-east':
            m=SHADE if pane.centroid.x<(l+r)/2 else BRIGHT
        face(b,pane,-.147,-.128,m,name+' separate pane')

def beam(b,a,c,w,d,material,name):
    a,c=np.array(a,float),np.array(c,float);v=c-a
    length=np.linalg.norm(v)
    if length<1e-4:return
    axis=v/length
    up=np.array([0.,0.,1.]) if abs(axis[2])<.9 else np.array([0.,1.,0.])
    side=np.cross(up,axis);side/=np.linalg.norm(side)
    b.box((a+c)/2,(length,w,d),material,[axis,side,np.cross(axis,side)],'view 2 | '+name)

def lid(b,left,right,rear,tip,zrear,ztip,thick,material,name):
    # Front right to back right traverses the XY footprint counterclockwise.
    lower=[(left,tip,ztip-thick),(right,tip,ztip-thick),(right,rear,zrear-thick),(left,rear,zrear-thick)]
    upper=[(x,y,z+thick)for x,y,z in lower]
    b.add(lower+upper,FACES,material,'view 2 | '+name)

def glass_hood(b,name,g):
    left,right,z=g['left'],g['right'],g['rear_z'];y=-g['depth'];tip=z-g['fall']
    front=-.016
    lid(b,left+.015,right-.015,front,y+.017,z,tip,.013,HOOD,name+' cyan transmitting sheet')
    for u in [left,right,left+(right-left)/3,left+2*(right-left)/3]:
        beam(b,[u,front,z-.016],[u,y,tip-.016],.029,.031,DARK,name+' outward structural bar')
    for dep,level in [(front,z),(y,tip)]:
        beam(b,[left,dep,level-.015],[right,dep,level-.015],.035,.035,DARK,name+' cross edge')
    for u in [left+.045,right-.045]:
        beam(b,[u,-.012,z-.29],[u,y+.018,tip-.035],.029,.029,DARK,name+' diagonal support')
        rect(b,u-.036,u+.036,z-.335,z-.245,-.006,.027,DARK,name+' wall shoe')

def open_leaf(b):
    g=D['outward_leaf'];hinge=np.array(g['hinge_xy']);end=np.array(g['free_xy'])
    lo,hi=g['hinge_bottom_z'],g['hinge_top_z'];direction=end-hinge
    normal=np.array([direction[1],-direction[0]]);normal/=np.linalg.norm(normal)
    length=np.linalg.norm(direction); along=direction/length
    def mapper(u,z,rel):
        x,y=hinge+along*u+normal*rel
        return (x,y,z)
    outer=box(0,lo,length,hi)
    clear=box(.032,lo+.04,length-.032,hi-.04)
    bars=unary_union([outer.difference(clear),*[box(.032,hi-(hi-lo)*f-.015,length-.032,hi-(hi-lo)*f+.015)for f in [.26,.52,.77]]])
    b.prism(bars,-.022,.022,mapper,FRAME,'view 2 | open leaf stiles and three rails')
    for pane in clear.difference(bars).geoms:
        b.prism(pane,-.005,.005,mapper,GLASS,'view 2 | separate glazing of open leaf')
    for f in [.16,.82]:
        x,y=hinge;z=lo+(hi-lo)*f
        b.tube([(x,y,z-.035),(x,y,z+.035)],.019,DARK,8,'view 2 | hinge barrel')

def raised_shelf(b,lod):
    g=D['plant_shelf']
    l,r,y,z=g['left'],g['right'],-g['depth'],g['rear_z']
    lid(b,l,r,-.014,y,z,z,.040,RACK,'projecting metal shelf platform')
    top=z+g['rail_height']
    for hh in [z+.018,(z+top)/2,top]:
        beam(b,[l,y,hh],[r,y,hh],.023,.026,RACK,'front rail')
    for i in range(4):
        x=l+(r-l)*i/3
        beam(b,[x,y,z+.015],[x,y,top],.024,.025,RACK,'front rail upright')
    for x in (l+.04,r-.04):
        beam(b,[x,-.018,z-.26],[x,y+.025,z-.046],.035,.042,DARK,'shelf wall bracket')
        beam(b,[x,-.012,top],[x,y,top],.023,.023,RACK,'shelf return rail')
    if not lod:
        for t in [.23,.48,.72]:
            x=l+(r-l)*t
            beam(b,[x,-.016,z-.042],[x,y+.014,z-.042],.028,.036,DARK,'shelf underside runner')

def add_canopy_front(b,lod=False):
    for k,v in PALETTE.items():b.palette.setdefault(k,v)
    l,base,r,hi=D['wall_xz'];openings=D['openings']
    front=box(l,base,r,hi)
    holes=[]
    for key,(x0,z0,x1,z1) in openings.items():
        # The bottom three lights vanish behind foliage. Leave their lower
        # continuation as a study cut rather than building a conjectural sill.
        bottom=min(base-.02,z0) if key.startswith('lower-') else z0
        holes.append(box(x0,bottom,x1,z1))
    face(b,front.difference(unary_union(holes)),-.26,0,WALL,'perforated yellow wall')
    for name in ['upper-west','upper-centre','upper-east']:
        q=openings[name];l,z,r,h=q
        if name=='upper-west':fixed_sash(b,name,q,(.19,.38,.56,.73))
        elif name=='upper-centre':fixed_sash(b,name,q,(.38,.67),tinted=True)
        else:
            fixed_sash(b,name,q,(.68,),tinted=True)
            for f in [.20,.40]:
                rect(b,(l+r)/2+.023,r-.047,z+f*(h-z)-.015,z+f*(h-z)+.015,-.12,-.072,FRAME,name+' right lower rail')
        lintel(b,l,r,z,name)
    q=openings['middle-open'];l,z,r,h=q
    opening=box(*q)
    face(b,opening,-.49,-.45,DEEP,'shadow at open casement')
    rim=opening.difference(box(l+.032,z+.032,r-.032,h-.032))
    face(b,rim,-.14,-.062,FRAME,'jamb of open casement')
    lintel(b,l,r,z,'open window')
    open_leaf(b)
    q=openings['middle-narrow'];l,z,r,h=q
    fixed_sash(b,'narrow adjacent light',q,(.22,.47,.72),columns=())
    lintel(b,l,r,z,'narrow adjacent light')
    for name in ['lower-west','lower-centre','lower-east']:
        l,z,r,h=openings[name];bottom=max(base,z)
        if h<=bottom:continue
        rect(b,l,r,bottom,h,-.16,-.14,DEEP,name+' partial light in tree-screened section')
        for x in [l,r-.038]:rect(b,x,x+.038,bottom,h,-.13,-.075,FRAME,name+' jamb')
        rect(b,l,r,h-.045,h,-.13,-.074,FRAME,name+' head')
        if name=='lower-west':rect(b,l,r,bottom+(h-bottom)*.58,bottom+(h-bottom)*.58+.026,-.13,-.08,FRAME,name+' rail')
    for name,g in D['canopies'].items():glass_hood(b,name,g)
    raised_shelf(b,lod)
    for key,title in [('pipe_xyz','downpipe'),('left_pipe_arm','left head arm'),('right_pipe_arm','right head arm')]:
        b.tube(D[key],.050 if key=='pipe_xyz' else .038,DARK,8 if lod else 12,'view 2 | '+title)
