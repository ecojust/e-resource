"""The scored render, actual openings, splayed entrance and projecting lane-side shaft."""
from math import cos, sin, pi
from shapely import set_precision, constrained_delaunay_triangles
from shapely.geometry import Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from material_names import PLASTER, TEXTURES
from old3_windows import finish, add_window, add_twisted_column

BED='Old No 3 | grey groove shadow'
RIM='Old No 3 | pale cement moulding'
REVEAL='Old No 3 | shaded doorway return'
PLINTH='Old No 3 | cement base and projecting sills'
PIPE='Old No 3 | weathered grey downpipe'
GAS='Old No 3 | ochre painted service pipe'
BRACKET='Old No 3 | dark pipe straps'
PALETTE={PLASTER:dict(texture=str(TEXTURES[PLASTER]),color=[1,1,1],roughness=.94),
         BED:finish((120,120,115),.94), RIM:finish((185,184,176),.89),
         REVEAL:finish((149,149,144),.94), PLINTH:finish((157,158,151),.92),
         PIPE:finish((126,129,123),.71,.13), GAS:finish((167,136,66),.65,.11),
         BRACKET:finish((91,89,84),.71,.15)}
# Front face horizontal joints in metres above the garden entrance sill, from the two rectified photographs.
COURSES=[0.,.35,.792,1.233,1.667,2.117,2.558,3.008,3.467,3.923,4.375,4.825,5.275,5.725,6.183,6.642,7.067,7.57]

def point(face,t,d,z,l):
    if face=='front':return t,d,z
    if face=='lane':return d,t,z
    if face=='rear':return t,l['depth']-d,z
    return l['width']-d,t,z

def solid(b,face,l,p,a,c,material,name):
    if p.is_empty or p.area<2.e-7:return
    geometry=set_precision(p,1e-7)
    scale=-1 if face in ('front','east') else 1
    lo,hi=sorted((scale*a,scale*c))
    b.prism(geometry,lo,hi,lambda t,z,v:point(face,t,scale*v,z,l),material,name)

def section(c,half,lo,spring,head,n):
    return Polygon([(c-half,lo),(c+half,lo),
        *((c+half*cos(pi*j/n),spring+(head-spring)*sin(pi*j/n))for j in range(n+1))])

def outline(o,n):
    c=o['center'];r=o['width']/2;z=o['sill'];h=o['head']
    if o['kind'] in ('door','arch'):return section(c,r,z,o['spring'],h,n)
    return box(c-r,z,c+r,h)

def doorway(b,l,o,lod):
    """Four ordered arch sections follow the rectified entry, including the deep inner soffit."""
    c=o['center'];spring=o['spring'];top=o['head'];r=o['width']/2
    n=18 if lod else 48
    def semi(z0,rx,rz):return [(c+rx*cos(pi*j/n),z0+rz*sin(pi*j/n)) for j in range(n+1)]
    def shell(rings,label,mat):
        vertices=[];faces=[];s=n+1
        for rx,rz,d in rings:
            vertices.extend((u,d,z)for u,z in semi(spring,rx,rz))
        for j in range(len(rings)):
            k=(j+1)%len(rings)
            for i in range(n):
                faces.append((j*s+i,j*s+i+1,k*s+i+1,k*s+i))
        # The moulding profile is concave. Triangulate each spring end on its own plane.
        cross_section=[(rx,d)for rx,rz,d in rings]
        cap=Polygon(cross_section)
        index={pt:j for j,pt in enumerate(cross_section)}
        for triangle in constrained_delaunay_triangles(cap).geoms:
            coords=orient(triangle,sign=1. if cap.exterior.is_ccw else -1.).exterior.coords
            js=[index[pt]for pt in list(coords)[:3]]
            faces.append(tuple(j*s for j in js))
            faces.append(tuple(j*s+n for j in reversed(js)))
        # Keep all strip solids outward-wound for both increasing and decreasing section profiles.
        import numpy as np
        pp=np.array(vertices)
        volume=sum(np.dot(pp[f[0]],np.cross(pp[f[i]],pp[f[i+1]]))for f in faces for i in range(1,len(f)-1))
        b.add(vertices,faces if volume>0 else [tuple(reversed(f))for f in faces],mat,label)
    rise=top-spring
    shell([(r+.010,rise+.010,.239),(r+.16,rise+.168,.10),(r+.258,rise+.272,-.006),
           (r+.30,rise+.316,-.034),(r+.31,rise+.326,.282),(r+.010,rise+.010,.282)],
           'Entrance arch splayed inner soffit',REVEAL)
    surround=[(r+.27,rise+.277,-.038),(r+.28,rise+.29,-.085),(r+.31,rise+.32,-.115),
              (r+.335,rise+.344,-.136),(r+.355,rise+.364,-.120),(r+.37,rise+.381,-.111),
              (r+.39,rise+.4,-.122),(r+.405,rise+.416,-.135),(r+.426,rise+.445,-.116),
              (r+.445,rise+.466,-.08),(r+.46,rise+.48,-.058),(r+.467,rise+.485,.012),
              (r+.27,rise+.277,.012)]
    shell(surround,'Entrance archivolt and concentric mouldings',RIM)
    for sign in [-1,1]:
        def strip(ri,ro):return sorted([c+sign*ri,c+sign*ro])
        # Inner jamb returns splay from the plane of the wall into the timber door.
        inner=c+sign*(r+.008);outer=c+sign*(r+.27)
        plan=Polygon([(inner,.232),(outer,-.014),(outer,.286),(inner,.286)])
        b.plan_prism(plan,.012,spring,REVEAL,'Entrance splayed jamb '+str(sign))
        a,e=strip(r+.27,r+.47)
        # Four receding courses beneath each springing block are readable in both 2015 views.
        for j,(z0,z1,r1,ext)in enumerate([(1.54,1.62,.055,.12),(1.62,1.71,.038,.16),(1.71,1.82,.023,.19),
                (1.82,1.94,.014,.22),(1.94,2.07,.004,.24),(2.07,2.19,-.004,.27),(2.19,2.25,-.022,.31),
                (2.25,2.30,-.04,.35),(2.30,2.35,-.060,.38),(2.35,2.39,-.07,.40)]):
            x0,x1=strip(r+.26+r1,r+.26+ext)
            solid(b,'front',l,box(x0,z0,x1,z1),-.035-ext*.42,.01,RIM,'Entry spring corbel '+str(sign)+' '+str(j+1))

def scored_face(b,face,l,records,lod):
    span=l['width'] if face in ('front','rear')else l['depth']
    n=16 if lod else 32
    holes=[]
    for o in records['openings']:
        if o['kind']=='door':
            holes.append(section(o['center'],o['width']/2+.27,-.012,o['spring'],o['head']+.29,n))
        else:holes.append(outline(o,n))
    pairs={}
    for o in records['openings']:
        if o.get('sill_group') and o['kind']=='arch':
            pairs.setdefault(o['sill_group'],[]).append(o)
    for windows in pairs.values():
        if len(windows)==2:
            a,c=sorted(windows,key=lambda o:o['center'])
            holes.append(box(a['center'],max(a['sill'],c['sill']),
                             c['center'],min(a['spring'],c['spring'])))
    void=unary_union(holes)
    wall=box(.024,0,span-.024,l['eaves']).difference(void)
    skin_start,skin_end=(.018,span-.018) if face in ('lane','east') else (0.,span)
    solid(b,face,l,wall,.014,.38 if face in ('lane','rear') else .267,BED,face+' wall and opening reveals')
    # The photographed scoring turns the corners. The foliage-hidden east side has the same envelope only.
    if face=='east':
        solid(b,face,l,box(skin_start,0,skin_end,l['eaves']),0,.018,PLASTER,'East wall plain obscured envelope')
        return
    levels=COURSES
    if face in ('lane','rear'):
        survey=l['joint_courses'][face+'_04']
        levels=[0.,*sorted(z for z in survey['levels_m'] if z>.08)]
        pitch=survey['median_pitch_m']
        while levels[-1]+pitch<l['eaves']-.14:
            levels.append(levels[-1]+pitch)
        levels.append(l['eaves'])
    for k,(z0,z1)in enumerate(zip(levels,levels[1:])):
        pitch=1.025
        # The top row starts with a short block. Opposite rows use half that full-joint spacing.
        x=.588-(.507 if k%2 else 0)
        while x>0:x-=pitch
        while x<span:
            a=max(x+.006,skin_start);c=min(x+pitch-.006,skin_end)
            if c>a:
                stone=box(a,z0+.004,c,z1-.004).difference(void)
                solid(b,face,l,stone,0,.0175,PLASTER,face+' scored course '+str(k+1))
            x+=pitch
    groups={}
    for i,o in enumerate(records['openings']):
        data=dict(o);data['id']=face+' opening '+str(i+1)
        if o['kind']=='door':
            data['sash_depth']=.244
            doorway(b,l,o,lod)
        elif o['kind'] in ('arch','rect'):
            gap=o.get('sill_group',str(i));groups.setdefault(gap,[]).append(o)
        add_window(b,face,data,l,lod)
    for j,entries in enumerate(groups.values(),1):
        z=sum(o['sill']for o in entries)/len(entries)
        a=min(o['center']-o['width']/2 for o in entries)-.09
        c=max(o['center']+o['width']/2 for o in entries)+.09
        solid(b,face,l,box(a,z-.125,c,z-.060),-.095,.015,PLINTH,face+' sill bed '+str(j))
        solid(b,face,l,box(a-.029,z-.074,c+.029,z-.013),-.145,.02,RIM,face+' sill lip '+str(j))
    for j,col in enumerate(records['columns'],1):
        add_twisted_column(b,face,{**col,'id':face+' shaft '+str(j)},l,lod)

def chimney(b,l,lod):
    # The tall plain shaft intersects the eave. Both lane views show the joint and cap.
    left=-.595;a=2.58;c=4.56;h=10.48
    b.box(((left+.09)/2,(a+c)/2,h/2),(.09-left,c-a,h),BED,label='Lane masonry shaft core')
    for j,z in enumerate([*COURSES,8.02,8.47,8.92,9.37,9.82]):
        z1=([*COURSES,8.02,8.47,8.92,9.37,9.82,h])[j+1]
        width=c-a-.008;lo=z+.005;hi=z1-.005
        b.box((left-.007,(a+c)/2,(lo+hi)/2),(.022,width,hi-lo),PLASTER,label='Shaft lane facing courses')
        for y in (a,c):
            b.box((left/2,y,(lo+hi)/2),(-left,.016,hi-lo),PLASTER,label='Shaft return courses')
    b.box((-.25,(a+c)/2,h+.026),(.774,c-a+.09,.073),PLINTH,label='Shaft weathering cap')

def balcony_and_services(b,l,lod):
    # Nose, soffit and wall return are separated by the dark joint visible below the iron feet.
    for a,c,depth,lo,hi,mat,label in [(1.065,4.59,.929,3.78,3.945,PLINTH,'Balcony structural soffit'),
            (1.04,4.61,.97,3.945,4.012,RIM,'Balcony projecting pale nosing')]:
        b.box(((a+c)/2,-depth/2+.01,(lo+hi)/2),(c-a,depth+.02,hi-lo),mat,label=label)
    side=8 if lod else 12
    b.tube([(l['width']-.04,-.065,.13),(l['width']-.04,-.065,7.31),
            (l['width']-.09,-.25,7.51),(l['width']-.09,-.36,7.63)],.052,PIPE,side,'Courtyard corner downpipe')
    b.tube([(-.078,l['depth']-.018,.04),(-.078,l['depth']-.018,7.29),
            (-.18,l['depth']-.018,7.52),(-.32,l['depth']-.018,7.64)],.057,PIPE,side,'Rear corner downpipe')
    b.tube([(.02,-.064,3.42),(4.69,-.064,3.42),(4.69,-.064,3.80),
            (8.34,-.064,3.80),(8.34,-.064,.43)],.021,GAS,side,'Courtyard service pipe stepped rise')
    for x,z in [(4.64,3.42),(5.15,3.80),(7.79,3.80)]:
        b.box((x,-.056,z),(.032,.119,.072),BRACKET,label='Courtyard pipe clamp')
    b.box((l['width']/2,l['depth']/2,.035),(l['width']-.34,l['depth']-.34,.07),PLINTH,label='Ground floor slab')
