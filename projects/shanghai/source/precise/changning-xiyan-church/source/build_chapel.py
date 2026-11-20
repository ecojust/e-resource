"""Model Xiyan's chapel exterior, 14-lancet copper crown and small riverside apse."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from photo_architecture import Facade

P=json.loads((HERE/'parameters.json').read_bytes())
GLASS=json.loads((HERE/'glass-colour-samples.json').read_bytes())
LEVEL=P['levels_m']
META={'id':P['id'],'name':'息焉堂（前庭、主堂铜顶及临河半圆体）',
      'status':'photo-informed-exterior','scope':'Main funerary chapel on Kele Road, with a pointed forecourt portal, glazed lancet, stepped cross-shaped mass, fourteen-pointed crown and riverside apse. The separate belfry is excluded.',
      'model_scope_zh':'依据2011及2016年外景、教区记述和三期航片制作前庭尖券门窗、主堂收分体与十四券绿铜穹顶，含可见的临河附属半圆体。背面、层高和不可见开口保留估计。北侧独立钟楼、墓地及室内不在本次范围。',
      'viewer_page':'xiyan-church.html','audit_directory':'data/audit/xiyan-church-v1/',
      'coordinate_convention':'Local glTF X points approximately northwest, Y is up and Z faces the northeast forecourt.',
      'source_register':'source/precise/changning-xiyan-church/photo-review.json','map_reference_license':'OpenStreetMap and Overture Maps, ODbL-1.0.','interiors_modeled':False}
COL={'rough ochre stucco':(.72,.638,.365),'light ochre reveals':(.783,.701,.459),'roughcast aggregate':(.758,.676,.398),'roughcast shadow':(.684,.609,.346),'weathered brown stone':(.445,.365,.278),'sandstone highlight':(.575,.487,.365),'chamfer shadow':(.369,.315,.268),'basalt foot':(.265,.259,.227),'grey door':(.318,.314,.292),'raised grey panels':(.392,.385,.35),'door furniture':(.245,.238,.201),'dark lead':(.238,.246,.235),'glazing recess':(.117,.143,.147),'copper pale':(.566,.698,.577),'copper shaded':(.457,.596,.492),'copper rib':(.366,.493,.404),'roof edge':(.296,.304,.271),'roof membrane':(.435,.446,.385),'aged cross':(.346,.357,.299),'apse glass':(.269,.344,.342)}
PALETTE={k:{'color':list(v),'roughness':.62 if k.startswith('copper') else .88,'metallic':.16 if k.startswith('copper') else .0}for k,v in COL.items()}
for i,color in enumerate(GLASS['palette_rgb_srgb']):
    PALETTE[f'forecourt glazing {i+1:02}']={'color':[v/255 for v in color],'roughness':.51,'metallic':.05}

FRONT=-9.50
# Lateral boundary follows the measured polygon; the stepped apse is modelled separately.
MAIN=orient(Polygon([(-8.10,FRONT),(8.34,FRONT),(9.54,9.75),(-6.11,9.77),(-6.48,4.08),(-7.87,-4.84)]),sign=1)
UPPER=box(-4.98,FRONT,5.45,8.24)
AX,AY=P['apse_center_xy_m']
AR=P['apse_radius_m']
CROWN=P['crown_center_xy_m']
COUNT=P['upper_points']
RAD=P['estimated_crown_diameter_m']/2


def pointed(u,low,width,height,rise,segments):
    """Two circular arcs meet at the pointed apex, above a straight lower jamb."""
    half=width/2;spring=low+height-rise
    radius=(rise*rise+half*half)/width;shift=radius-half
    angles=np.linspace(0,math.atan2(rise,shift),segments+1)
    right=[(u-shift+radius*math.cos(a),spring+radius*math.sin(a))for a in angles]
    return Polygon([(u-half,low),(u+half,low),*right,*[(2*u-x,y)for x,y in reversed(right[:-1])]])


def ring(face,opening,inner,outer,d,material,label):
    a=opening.buffer(outer,join_style='mitre')
    b=opening.buffer(inner,join_style='mitre') if inner else opening
    face.prism(a.difference(b),d-.085,d,material,label)


def glazing(face,opening,lod):
    """Separate shallow coloured cells and exposed metal saddlebars, for the photographed window."""
    face.prism(opening,-.220,-.185,'glazing recess','lancet dark bed')
    xmin,low,xmax,top=opening.bounds
    rows=GLASS['rows_from_top'];ny=len(rows);nx=len(rows[0]);gap=.006 if not lod else .009
    for j,row in enumerate(rows):
        upper=top-(top-low)*j/ny;bottom=top-(top-low)*(j+1)/ny
        for i,pigment in enumerate(row):
            x0=xmin+(xmax-xmin)*i/nx;x1=xmin+(xmax-xmin)*(i+1)/nx
            pane=opening.intersection(box(x0+gap,bottom+gap,x1-gap,upper-gap))
            if pane.area>.0001:face.prism(pane,-.178,-.162,f'forecourt glazing {pigment+1:02}','photographed colour groups')
    for z in np.linspace(low+.13,top-.14,13):
        bar=opening.intersection(box(xmin,z-.019,xmax,z+.019));face.prism(bar,-.160,-.119,'dark lead','horizontal saddle bars')
    for x in np.linspace(xmin,xmax,5)[1:-1]:
        bar=opening.intersection(box(x-.013,low,x+.013,top));face.prism(bar,-.160,-.131,'dark lead','vertical lead cames')


def roughcast(face,area,lod,seed):
    """Low irregular ridges in the yellow render, visible in the May/June 2016 photos."""
    xmin,bottom,xmax,top=area.bounds
    rng=np.random.default_rng(seed)
    step=.52 if lod else .29
    for j,z in enumerate(np.arange(bottom+.15,top-.04,step*.64)):
        for x in np.arange(xmin+.12+(j%2)*step*.44,xmax-.04,step):
            u=x+rng.uniform(-.07,.07);v=z+rng.uniform(-.045,.045)
            length=rng.uniform(.042,.105);height=rng.uniform(.017,.038)
            if not area.contains(Point(u,v).buffer(.115,quad_segs=2)):continue
            points=[face.point(u-length,v,.003),face.point(u,v-height*.45,.015),
                    face.point(u+length,v+height*.25,.002),face.point(u-length*.35,v+height,.004)]
            face.builder.add(points,[(0,1,3),(1,2,3)],'roughcast aggregate'if rng.random()>.28 else'roughcast shadow','low irregular render relief')


def entrance(face,lod):
    n=9 if lod else 22
    door=pointed(0,.115,1.56,2.06,.53,n);light=pointed(0,2.72,1.39,3.52,1.08,n)
    full=unary_union([box(-face.length/2,.10,face.length/2,LEVEL['lower_eaves']),box(-4.98-face.center[0],.1,5.45-face.center[0],LEVEL['central_eaves'])])
    face.prism(full.difference(unary_union([door,light])),-.43,0,'rough ochre stucco','forecourt end wall')
    roughcast(face,full.difference(unary_union([door.buffer(.32),light.buffer(.35),box(-1.12,.0,1.12,2.70)])),lod,420)
    # Three sharply stepped rings continue from the glass shoulders to the pointed crown.
    for j,(inside,outside,depth,mat)in enumerate([(0,.060,.055,'chamfer shadow'),(.060,.139,.143,'sandstone highlight'),(.139,.209,.094,'weathered brown stone'),(.209,.280,.183,'sandstone highlight')]):
        ring(face,light,inside,outside,depth,mat,'lancet archivolt courses')
    face.box(0,2.64,2.08,.12,.36,.092,'weathered brown stone','window sill')
    face.box(0,2.56,2.18,.07,.39,.095,'chamfer shadow','drip below glass')
    backing=box(-1.05,.08,1.05,2.54).difference(door);face.prism(backing,-.064,.037,'weathered brown stone','portal spandrels and jambs')
    ring(face,door,0,.087,.097,'chamfer shadow','pointed door reveal')
    face.prism(door,-.34,-.292,'grey door','two closed pointed door leaves')
    for side in (-1,1):
        x=side*.40
        for bot,hi in [(.21,.69),(.78,1.43),(1.51,1.91)]:
            poly=door.buffer(-.048).intersection(box(x-.309,bot,x+.309,hi))
            if poly.area>.01:
                rim=poly.difference(poly.buffer(-.052));face.prism(rim,-.291,-.250,'raised grey panels','recessed door panels')
        face.box(side*.08,.89,.039,.18,.057,-.241,'door furniture','door pulls')
    face.box(0,1.10,.030,1.96,.03,-.268,'chamfer shadow','paired leaf meeting stile')
    glazing(face,light,lod)
    for z,width,depth in [(.035,2.52,.54),(.085,2.31,.35)]:
        face.box(0,z,width,.07,depth,depth/2,'basalt foot','low entrance thresholds')


def plain_front_edges(builder,lod):
    geom=list(MAIN.exterior.coords)
    front=None
    for idx,(a,b)in enumerate(zip(geom,geom[1:])):
        f=Facade(builder,a,b,'Chapel masonry')
        if idx==0:
            front=f;entrance(f,lod);continue
        # The curved riverside apse hides the central span in this owner edge.
        small=pointed(0,1.11,.44,1.46,.37,9 if lod else 17)if idx==3 else None
        f.wall(.10,LEVEL['lower_eaves'],[small]if small is not None else [],.27,'rough ochre stucco')
        if small is not None:
            f.prism(small,-.16,-.11,'apse glass','slender photographed riverside light');ring(f,small,0,.076,.061,'light ochre reveals','side window reveal')
        if idx in (1,2,3,5):
            outer=box(-f.length/2,.28,f.length/2,LEVEL['lower_eaves']-.12)
            if small is not None:outer=outer.difference(small.buffer(.16))
            roughcast(f,outer,lod,481+idx)
        f.box(0,.19,f.length,.19,.23,.025,'basalt foot','lower water table')
    lifted=list(orient(UPPER,sign=1).exterior.coords)
    for a,b in zip(lifted,lifted[1:]):
        f=Facade(builder,a,b,'Raised central nave')
        if max(a[1],b[1])<FRONT+.01:continue
        f.wall(LEVEL['lower_eaves']-.12,LEVEL['central_eaves'],(),.22,'rough ochre stucco')
    # Low roof is absent above the central opening. Its partial wing planes can be inspected separately.
    builder.plan_prism(MAIN.difference(UPPER),LEVEL['lower_eaves']-.045,LEVEL['lower_eaves']+.046,'roof membrane','shoulder roofs')
    for area,z,label in [(MAIN,LEVEL['lower_eaves'],'low wing eaves'),(UPPER,LEVEL['central_eaves'],'central eaves')]:
        edge=area.buffer(.13,join_style='mitre').difference(area.buffer(-.11,join_style='mitre'))
        if area is MAIN:edge=edge.difference(UPPER.buffer(.01)).difference(box(-1.90,FRONT-.3,1.90,FRONT+.4))
        builder.plan_prism(edge,z-.071,z+.072,'roof edge',label)
    builder.plan_prism(UPPER,LEVEL['central_eaves']-.023,LEVEL['central_eaves']+.035,'roof membrane','high nave roof')
    return front


def circular_clerestory(builder,center,radius,low,height,count,theta0,theta1,lod,prefix):
    cx,cy=center
    angles=np.linspace(theta0,theta1,count+1)
    corners=[(cx+radius*math.cos(a),cy+radius*math.sin(a)) for a in angles]
    for index,(a,b) in enumerate(zip(corners,corners[1:])):
        face=Facade(builder,a,b,prefix)
        width=face.length*(.59 if prefix=='Crown' else .54)
        shape=pointed(0,low+.12,width,height-.18,min(.83*width,height*.70),8 if lod else 17)
        face.wall(low,low+height,[shape],.19,'light ochre reveals')
        face.prism(shape,-.30,-.27,'glazing recess'if prefix=='Crown'else 'apse glass',prefix+' recessed pointed lights')
        ring(face,shape,0,.048,.043,'copper rib',prefix+' pointed edging')
        face.box(0,low+.07,face.length,.085,.21,.03,'roof edge',prefix+' circular sill')
        if prefix!='Crown':face.box(0,low+height*.45,.024,height*.55,.035,-.24,'dark lead','small apse saddle bar')


def copper_roof(builder,center,radius,foot,top,count,theta0,theta1,lod,label):
    # Fourteen radial seams correspond to the parish description. The scalloped eave
    # follows each pointed support, seen independently in the two riverside photographs.
    steps=4 if lod else 8;levels=5 if lod else 10
    full=abs(theta1-theta0-2*math.pi)<1e-7
    angles=np.linspace(theta0,theta1,count*steps+1)
    def vertex(i,j):
        a=angles[i];t=j/levels;phi=t*math.pi/2;arc=math.sin(math.pi*(i%steps)/steps)
        horizontal=radius*math.cos(phi)*(1+.026*arc*(1-t))
        z=foot+(top-foot)*math.sin(phi)-.18*(1-arc)*(1-t)**2
        return (center[0]+horizontal*math.cos(a),center[1]+horizontal*math.sin(a),z)
    for band in range(count):
        vertices=[];faces=[]
        for i in range(steps+1):
            for j in range(levels+1):vertices.append(vertex(band*steps+i,j))
        for i in range(steps):
            for j in range(levels):
                a=i*(levels+1)+j;b=a+levels+1
                faces.append((a,b,b+1,a+1))
        builder.add(vertices,faces,'copper pale'if band%3 else'copper shaded',label+' copper sheets')
        seam=[vertex(band*steps,j) for j in range(levels+1)]
        builder.tube(seam,.021 if full else .016,'copper rib',5 if lod else 8,label+' standing seams')
        lip=[vertex(band*steps+i,0)for i in range(steps+1)]
        builder.tube(lip,.034,'copper rib',6,label+' scalloped edge')
        if not lod:
            lap=[vertex(band*steps+i,4)for i in range(steps+1)]
            builder.tube(lap,.011,'copper rib',5,label+' transverse laps')


def apse(builder,lod):
    # Only the exposed riverside half is authored; the other half joins the chapel.
    a0=math.pi/2;a1=3*math.pi/2
    angles=np.linspace(a0,a1,18 if lod else 34)
    curve=[(AX+AR*math.cos(a),AY+AR*math.sin(a))for a in angles]
    d=orient(Polygon([(AX+1.65,AY+AR),*curve,(AX+1.65,AY-AR)]),sign=1)
    builder.plan_prism(d,.10,3.78,'rough ochre stucco','Riverside apse/round wall')
    e=d.buffer(.088,join_style='mitre')
    builder.plan_prism(e,3.74,3.88,'roof edge','Riverside apse/cornice')
    circular_clerestory(builder,(AX,AY),AR-.045,3.87,.76,7,a0,a1,lod,'Apse')
    copper_roof(builder,(AX,AY),AR+.06,4.56,5.97,7,a0,a1,lod,'Riverside apse')


def central_crown(builder,lod):
    cx,cy=CROWN;r=RAD
    square=box(cx-r-.34,cy-r-.34,cx+r+.34,cy+r+.34)
    builder.plan_prism(square,LEVEL['central_eaves'],LEVEL['raised_terrace'],'rough ochre stucco','Crown/square stepped terrace')
    builder.plan_prism(square.buffer(.13,join_style='mitre'),LEVEL['raised_terrace']-.055,LEVEL['raised_terrace']+.064,'roof edge','Crown/terrace cornice')
    circular_clerestory(builder,CROWN,r-.17,LEVEL['raised_terrace']+.045,1.16,COUNT,0,2*math.pi,lod,'Crown')
    copper_roof(builder,CROWN,r,LEVEL['crown_spring']+.14,LEVEL['crown_top'],COUNT,0,2*math.pi,lod,'Main crown')
    builder.lathe((cx,cy),[(9.94,.20),(10.03,.15),(10.10,.09),(10.15,.065)],'copper rib',16,'Cross/finial foot')
    builder.box((cx,cy,10.49),(.062,.075,.92),'aged cross',label='Cross/restored shaft')
    builder.box((cx,cy,10.68),(.52,.075,.055),'aged cross',label='Cross/transverse arm')


def assemble(builder,lod):
    plain_front_edges(builder,lod)
    apse(builder,lod)
    central_crown(builder,lod)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
