"""Reconstruct the photographed west porch, pointed window and gable of Xinen Church."""
from math import acos, cos, sin
from pathlib import Path
from shapely import affinity
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes

PORCH_HALF = 3.66
GABLE_PLANE = 6.36
EAVE = 8.81
APEX = 16.09
FONT = Path(__file__).with_name('fonts')/'XinenInscription.otf'
PALETTE = {
    'blue grey brick': {'color':[.325,.324,.327],'roughness':.91},
    'brick shading': {'color':[.288,.289,.292],'roughness':.93},
    'fine bed joint': {'color':[.391,.391,.381],'roughness':.93},
    'granite porch': {'color':[.522,.501,.457],'roughness':.86},
    'granite dressing': {'color':[.619,.596,.542],'roughness':.83},
    'weathered fascia': {'color':[.427,.404,.359],'roughness':.92},
    'incised lettering': {'color':[.191,.176,.154],'roughness':.86},
    'deep reveals': {'color':[.239,.233,.220],'roughness':.96},
    'iron frame': {'color':[.145,.15,.153],'roughness':.58,'metallic':.22},
    'grey glazing': {'color':[.169,.204,.221],'roughness':.35,'metallic':.12},
    'green grey glazing': {'color':[.203,.233,.228],'roughness':.38,'metallic':.10},
    'dark letter screen': {'color':[.104,.109,.108],'roughness':.76},
    'crimson characters': {'color':[.554,.083,.077],'roughness':.56},
    'cross red': {'color':[.469,.101,.111],'roughness':.64},
    'grey shingle': {'color':[.232,.241,.246],'roughness':.88},
    'roof course': {'color':[.305,.311,.312],'roughness':.85},
    'light base': {'color':[.69,.681,.644],'roughness':.9},
    'paving': {'color':[.409,.399,.380],'roughness':.9},
}

def lancet(half,base,spring,apex,segments):
    """Two arcs of equal radius meet in the photographed pointed head."""
    rise=apex-spring
    radius=(half*half+rise*rise)/(2*half)
    center=half-radius
    span=acos(-center/radius)
    right=[(center+radius*cos(span*i/segments),spring+radius*sin(span*i/segments)) for i in range(segments+1)]
    return Polygon([(-half,base),(half,base),*right,*[(-x,z)for x,z in reversed(right[:-1])]])

def lettering(face,text,x,z,width,height,material,label,lod,depth):
    glyphs=[]
    for char,poly in lettering_shapes(text,width,height,font=FONT):
        glyphs.append(affinity.translate(poly.simplify(.003 if lod else .001,preserve_topology=True),xoff=x,yoff=z))
    face.prism(unary_union(glyphs),depth,depth+.009,material,label)

def brick_face(face,shape,lod):
    face.prism(shape,-.32,.002,'blue grey brick','west wall body and opening returns')
    z=.22
    pitch=.26 if lod else .13
    row=0
    while z<APEX:
        strip=shape.intersection(box(-6.35,z,6.35,z+(.011 if lod else .008)))
        if strip.area>.001:face.prism(strip,.003,.010,'fine bed joint',f'west brick beds {row:03}')
        if not lod and row%2==0:
            joints=[]
            x=-6.3+(.15 if row%4 else 0)
            while x<6.2:
                joints.append(box(x,z-pitch,x+.008,z));x+=.30
            mortar=shape.intersection(unary_union(joints))
            if mortar.area>.001:face.prism(mortar,.003,.009,'brick shading',f'west brick ends {row:03}')
        row+=1;z+=pitch

def pointed_window(face,lod):
    steps=12 if lod else 32
    outside=lancet(2.99,6.51,7.66,11.10,steps)
    light=lancet(2.60,6.57,7.61,10.68,steps)
    border=outside.difference(light)
    face.prism(border,-.19,.120,'granite dressing','pointed granite surround')
    face.prism(outside.boundary.buffer(.025,cap_style=2,join_style=2),.116,.153,'weathered fascia','hood outside arris')
    frame=light.difference(light.buffer(-.065,join_style=2))
    mullions=unary_union([box(x-.120,6.46,x+.120,10.71)for x in (-1.03,1.11)]).intersection(light)
    face.prism(mullions,-.025,.135,'granite dressing','two independent granite mullions')
    bars=[box(x-.022,6.49,x+.022,10.71)for x in (-1.90,-.48,.37,1.93)]
    bars.extend(box(-2.64,z-.019,2.64,z+.019)for z in (7.53,8.44,9.34))
    grille=frame.union(unary_union(bars).intersection(light)).difference(mullions)
    face.prism(grille,-.090,-.033,'iron frame','lancet bronze glazing bars')
    pane=light.difference(frame.union(mullions).union(grille))
    for j,cell in enumerate(sorted(pane.geoms if hasattr(pane,'geoms')else [pane],key=lambda x:x.centroid.x)):
        face.prism(cell,-.161,-.124,'green grey glazing' if j%5==1 else 'grey glazing',f'lancet glazing pane {j:02}')
    # Radial voussoir joints stop at the inside arris, preserving the cut window.
    for k,t in enumerate((.21,.47,.74) if lod else (.13,.29,.45,.62,.78,.91)):
        for side in (-1,1):
            # Use the actual curve point nearest each chosen height.
            z=7.66+t*(11.1-7.66)
            cut=outside.boundary.intersection(LineString([(-3.05,z),(3.05,z)]))
            options=[a for a in getattr(cut,'geoms',[cut])if a.geom_type=='Point'and a.x*side>0]
            if not options:continue
            edge=options[0];inner=(edge.x-.56*side,z-.34*t)
            joint=LineString([(edge.x,edge.y),inner]).buffer(.013 if lod else .011,cap_style=2).intersection(border)
            face.prism(joint,.125,.139,'weathered fascia',f'voussoir joint {side} {k}')
    return outside

def gable(builder,lod):
    face=Facade(builder,(-6.17,GABLE_PLANE),(6.17,GABLE_PLANE),'west gable')
    outer=Polygon([(-6.17,0),(6.17,0),(6.17,8.56),(5.29,EAVE),(0,APEX),(-5.29,EAVE),(-6.17,8.56)])
    lanc=pointed_window(face,lod)
    # The open porch hides the centre of the lower church front. Keep its visible wall and plain junction.
    west=outer.difference(lanc)
    brick_face(face,west,lod)
    face.box(0,.25,12.34,.50,.10,.045,'light base','west undercroft pale plinth')
    for side in (-1,1):
        u=5.29*side
        poly=LineString([(u,EAVE),(0,APEX)]).buffer(.104,cap_style=2,join_style=2)
        face.prism(poly,-.23,.172,'granite dressing',f'pitched coping {side}')
        face.box(5.74*side,8.58,.94,.20,.48,.080,'granite dressing',f'eave shoulder {side}')
        face.box(5.78*side,7.82,.72,1.26,.41,.045,'granite porch',f'shoulder pilaster cap {side}')
        left,right=(side*6.17,GABLE_PLANE),(side*6.17,GABLE_PLANE+1.12)
        if side<0:left,right=right,left
        end=Facade(builder,left,right,f'gable wall return {side}')
        end.prism(box(-.56,.02,.56,8.51),-.15,0,'blue grey brick','short wall')
        v=[(0,GABLE_PLANE+.16,APEX-.15),(0,GABLE_PLANE+1.12,APEX-.15),
           (u,GABLE_PLANE+1.12,EAVE-.10),(u,GABLE_PLANE+.16,EAVE-.10)]
        if side>0:v.reverse()
        builder.add(v,[(0,1,2),(0,2,3)],'grey shingle',f'visible roof return {side}')
        for k in range(1,15 if lod else 30):
            a=k/(15 if lod else 30);x=u*a;z=APEX-.15+(EAVE-APEX+.05)*a
            builder.tube([(x,GABLE_PLANE+.16,z+.008),(x,GABLE_PLANE+1.12,z+.008)],.011,'roof course',5,f'short roof course {side} {k}')
    face.box(0,17.14,.286,2.16,.24,-.02,'cross red','ridge cross upright')
    face.box(0,17.44,1.51,.29,.26,-.015,'cross red','ridge cross arms')

def portico(builder,lod):
    h=PORCH_HALF;dep=GABLE_PLANE;face=Facade(builder,(-h,0),(h,0),'three-light street screen')
    centers=[-1.68,0,1.70]
    holes=unary_union([box(x-.49,2.24,x+.49,3.75)for x in centers]);lowall=box(-h,.08,h,4.11).difference(holes)
    face.prism(lowall,-.36,0,'granite porch','front three openings with reveals')
    for row,z in enumerate((.54,1.14,1.70,2.22,2.74,3.27,3.77)):
        sb=lowall.intersection(box(-h,z,h,z+.014));face.prism(sb,.008,.013,'weathered fascia',f'front masonry bed {row}')
    face.box(0,.305,2*h,.43,.10,.035,'light base','screen pale plinth')
    for i,(x,ch)in enumerate(zip(centers,'新恩堂')):
        face.prism(box(x-.49,2.24,x+.49,3.75),-.32,-.307,'dark letter screen',f'recessed screen {i+1}')
        lettering(face,ch,x,2.99,.68,.69,'crimson characters',f'screen {i+1} {ch}',lod,-.30)
        face.box(x,2.225,1.11,.145,.41,-.025,'granite dressing',f'opening sill {i+1}')
        face.box(x,3.82,1.20,.14,.41,-.017,'granite dressing',f'opening lintel {i+1}')
    face.prism(box(-h,4.09,h,5.20),-.35,.025,'weathered fascia','front English tablet bed')
    face.box(0,4.19,2*h+.08,.115,.45,-.02,'granite dressing','tablet lower string')
    face.box(0,5.24,2*h+.13,.13,.45,-.04,'granite dressing','tablet upper drip')
    lettering(face,'SHANGHAI FREE CHRISTIAN CHURCH',0,4.863,5.52,.30,'incised lettering','documented English name',lod,.033)
    lettering(face,'EVANGELICAL',0,4.49,2.38,.30,'incised lettering','documented second inscription',lod,.033)
    for side in (-1,1):
        start,end=(side*h,0),(side*h,dep)
        if side<0:start,end=end,start
        f=Facade(builder,start,end,'south entry' if side>0 else 'north entry')
        hole=opening(0,-.01,4.20,3.85,arch=.97,segments=12 if lod else 30)
        wall=box(-dep/2,.02,dep/2,5.17).difference(hole)
        f.prism(wall,-.34,0,'granite porch','open side arch with supports')
        rim=hole.buffer(.135,join_style=2).difference(hole).intersection(box(-dep/2,.02,dep/2,4.12))
        f.prism(rim,-.10,.039,'granite dressing','side arch voussoir band')
        f.box(0,4.68,dep,1.01,.097,.009,'weathered fascia','side fascia')
        f.box(0,5.24,dep,.13,.40,-.035,'granite dressing','side coping')
    builder.plan_prism(box(-h,0,h,dep),.015,.075,'paving','entrance paving')
    builder.plan_prism(box(-h+.08,.12,h-.08,dep-.025),5.03,5.172,'grey shingle','flat porch roof')

def add_church(builder,lod=False):
    gable(builder,lod)
    portico(builder,lod)
