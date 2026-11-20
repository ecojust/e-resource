"""Reconstruct the 2009–17 courtyard elevation of Saint Joseph's Church at 36 South Sichuan Road."""
import json
import math
import sys
from pathlib import Path

import numpy as np
from shapely.affinity import rotate, scale, translate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[3]/'tools'))
from package_architectural_model import build
from photo_architecture import Facade, opening

P=json.loads((HERE/'parameters.json').read_bytes())
W=P['front_length_m']; HALF=W/2; D=P['modeled_depth_m']; L=P['levels_m']
META={'id':P['id'],'name':'若瑟堂（四川南路36号东立面与钟塔）','status':'photo-informed-partial-building',
      'scope':'East courtyard front in the 2009–2017 photographs, three doors, four saint niches, pierced rose and bell tower. The nave is retained from the city.',
      'model_scope_zh':'建模范围为院内东立面及钟塔。三道门、四座雕像龛、圆花窗、两座双联盲拱与赤褐色百叶依2009及2017年外景。雕像衣饰、侧背、标高和钟楼深度含推定，堂身及院内学校另行核查。',
      'viewer_page':'st-joseph-east-front.html','audit_directory':'data/audit/st-joseph-east-front-v1/',
      'coordinate_convention':'Local glTF X follows the front to the NNW at 339.90 degrees, Y is up, and Z faces the courtyard at 69.90 degrees true.',
      'source_register':'source/precise/huangpu-st-joseph-church-east-front/sources.json','map_reference_license':'OpenStreetMap and Overture Maps, ODbL-1.0.','interiors_modeled':False}
COL={'limewash':(.83,.78,.655),'weathered trim':(.665,.627,.534),'recess':(.472,.438,.371),'carved figure':(.375,.355,.302),'door oak':(.322,.146,.102),'raised oak':(.395,.183,.124),'door bronze':(.38,.28,.17),'lead':(.24,.161,.15),'glass ruby':(.54,.19,.174),'glass green':(.17,.367,.215),'glass amber':(.60,.449,.142),'glass violet':(.382,.187,.247),'glass milk':(.75,.72,.59),'glass blue':(.18,.246,.38),'terracotta tracery':(.69,.435,.357),'slate':(.233,.246,.231),'gray seam':(.304,.307,.279),'louver red':(.35,.184,.139),'louver shadow':(.15,.131,.114),'rail iron':(.234,.231,.206),'chapel roof':(.338,.275,.217)}
PALETTE={k:{'color':list(v),'roughness':.50 if k.startswith('glass') or k=='rail iron' else .85,'metallic':.2 if k in ('rail iron','door bronze') else 0.}for k,v in COL.items()}


def disk(x,z,r,n):return Point(x,z).buffer(r,quad_segs=n)

def ring(face,shape,w,d,material='weathered trim'):
    raised=shape.buffer(w,join_style='mitre').difference(shape)
    if raised.bounds[1]<0:
        x0,_,x1,h=raised.bounds
        raised=raised.intersection(box(x0-.01,0,x1+.01,h+.01))
    face.prism(raised,d-.088,d,material,'moulded border')

def pointed(x,z,w,h,n):
    spring=z+h-w*.77; radius=((w*.77)**2+(w/2)**2)/w; shift=radius-w/2
    angles=np.linspace(0,math.atan2(w*.77,shift),n+1)
    right=[(x-shift+radius*math.cos(a),spring+radius*math.sin(a))for a in angles]
    return Polygon([(x-w/2,z),(x+w/2,z),*right,*[(2*x-i,j)for i,j in reversed(right[:-1])]])

def bead(face,points,width,depth,material='weathered trim'):
    face.prism(LineString(points).buffer(width/2,cap_style='flat',join_style='mitre'),depth-.11,depth,material,'edge profile')

def door(face,x,w,h,d,lod):
    rad=w/2; n=8 if lod else 18; base=.055; spring=base+h-rad
    q=opening(x,base,w,h,arch=rad,segments=n*2)
    face.prism(q,-.35+d,-.29+d,'door oak','closed door leaves')
    ring(face,q,.15,d+.095);ring(face,q.buffer(.155),.075,d+.046,'limewash')
    fan=q.intersection(box(x-w,spring,x+w,h+base+.1));face.prism(fan,-.282+d,-.241+d,'glass milk','transom glass')
    face.box(x,spring,w+.065,.12,.145,d-.169,'raised oak','transom rail')
    face.box(x,spring/2,.063,spring-.07,.062,d-.215,'door bronze','meeting stile')
    for half in (-1,1):
        length=(w-.18)/2;split=x+half*w/4
        for column in (0,1):
            xx=split+(column-.5)*length/2
            for level in range(3):
                hh=(spring-.45)/3;bot=.17+level*hh
                panel=box(xx-length*.199,bot,xx+length*.199,bot+hh*.83)
                face.prism(panel,-.294+d,-.215+d,'raised oak','panelled walnut leaf')
                if not lod:ring(face,panel.buffer(-.035),.022,d-.188,'door oak')
        face.box(x+half*.102,1.01,.052,.22,.095,d-.15,'door bronze','door pull')
    for k in range(-2,3):
        dx=k*w*.145; top=spring+math.sqrt(max(0,rad**2-dx**2))
        face.line((x+dx,spring+.02,d-.19),(x+dx,top,d-.19),.029,'raised oak',5,'fanlight vertical')
    if not lod:
        for side in (-1,1):
            for i in range(3):
                dz=(i+.55)*rad/3.6;y=spring+dz;hal=math.sqrt(rad**2-dz**2)
                face.line((x+side*.04,y,d-.198),(x+side*hal,y,d-.198),.021,'raised oak',5,'transom lattice')
    return q

def statue(builder,x,y,z,lod):
    label='Portal niches/approximate carved figures';n=7 if lod else 12
    body=[(z,.22),(z+.10,.31),(z+.39,.24),(z+.84,.18),(z+1.19,.23),(z+1.34,.17),(z+1.42,.083)]
    builder.lathe((x,y),body,'carved figure',n,label)
    builder.lathe((x,y-.018),[(z+1.36,.035),(z+1.4,.118),(z+1.53,.157),(z+1.65,.14),(z+1.72,.07),(z+1.735,.012)],'carved figure',n,label)
    for side in (-1,1):
        builder.tube([(x+side*.175,y,z+1.26),(x+side*.234,y-.07,z+.94),(x+side*.04,y-.167,z+.994)],.072,'carved figure',6,label)
        if not lod:builder.tube([(x+side*.055,y-.195,z+1.22),(x+side*.14,y-.182,z+.68),(x+side*.19,y-.178,z+.15)],.023,'weathered trim',5,label)

def niche(face,x,base,lod):
    n=8 if lod else 17;h=3.04;wid=1.08
    opening_shape=pointed(x,base,wid,h,n)
    face.prism(opening_shape,-.53,-.45,'recess','niche inner wall')
    border=box(x-.725,base-.20,x+.725,base+h-.56).union(Polygon([(x-.725,base+h-.56),(x+.725,base+h-.56),(x,base+h+.10)]))
    face.prism(border.difference(opening_shape),-.52,.170,'limewash','statue tabernacle')
    ring(face,opening_shape,.09,.228);bead(face,[(x-.80,base+h-.58),(x,base+h+.22),(x+.80,base+h-.58)],.14,.28)
    face.box(x,base-.12,1.54,.16,.80,.025,'weathered trim','tapering niche sill')
    loc=face.point(x,base+.05,-.12);statue(face.builder,loc[0],loc[1],loc[2],lod)
    return opening_shape

def rose(face,x,z,r,lod):
    n=9 if lod else 21;window=disk(x,z,r,n);face.prism(window,-.48,-.40,'lead','rose backing')
    cells=[]; ring_distance=r*.721;big_r=r*.245
    outer=['glass green','glass violet','glass ruby','glass amber','glass green','glass milk','glass ruby','glass amber']
    inner=['glass ruby','glass amber','glass green','glass ruby','glass ruby','glass amber','glass green','glass violet']
    for j in range(8):
        a=math.tau*j/8;cx=x+math.sin(a)*ring_distance;cz=z+math.cos(a)*ring_distance
        petal=disk(cx,cz,big_r,n).intersection(window.buffer(-r*.016));cells.append(petal)
        face.prism(petal,-.398,-.36,outer[j],'eight outer rose panes')
        a+=math.pi/8; axis=np.array([math.sin(a),math.cos(a)]);norm=np.array([math.cos(a),-math.sin(a)]);origin=np.array([x,z]);ctr=origin+axis*r*.405
        cap=[ctr+axis*r*.166*math.cos(t)+norm*r*.151*math.sin(t)for t in np.linspace(-math.pi/2,math.pi/2,2*n+1)]
        pp=Polygon([origin+axis*r*.188-norm*r*.068,*cap,origin+axis*r*.188+norm*r*.068]);cells.append(pp);face.prism(pp,-.398,-.35,inner[j],'eight inward rose petals')
    core=disk(x,z,r*.137,n);cells.append(core);face.prism(core,-.398,-.345,'glass blue','small central rose medallion')
    tracery=window.difference(unary_union(cells));face.prism(tracery,-.351,-.253,'terracotta tracery','reconstructed rose tracery')
    ring(face,window,.145,.09);ring(face,window.buffer(.15),.218,.18,'limewash')
    return window

def blind_arcade(face,c,lod):
    n=7 if lod else 15;bot=11.08;top=15.45;wide=2.45
    outer=opening(c,bot,wide,top-bot,arch=wide/2,segments=n*2)
    pairs=[opening(c+v*.492,bot+.12,.80,2.67,arch=.40,segments=n*2)for v in (-1,1)]
    eye=disk(c,14.50,.379,n);face.prism(outer,-.47,-.40,'recess','bifora back plane')
    face.prism(outer.difference(unary_union([*pairs,eye])),-.365,.085,'limewash','two semicircular blind lights')
    ring(face,outer,.100,.127);ring(face,eye,.09,.134,'weathered trim')
    face.prism(eye,-.392,-.355,'terracotta tracery','small circular light')
    for i in range(8):
        a=math.tau*i/8;face.line((c,14.5,-.336),(c+.34*math.cos(a),14.50+.34*math.sin(a),-.336),.028,'weathered trim',5,'radial tracery')
    for q in pairs:ring(face,q,.055,.120)
    return outer


def quattrofoil(x,z,r,n):
    cells=[disk(x+math.cos(a)*r*.44,z+math.sin(a)*r*.44,r*.56,n)for a in [0,math.pi/2,math.pi,3*math.pi/2]]
    return rotate(unary_union(cells),45,origin=(x,z))

def sloping_roof(builder,left,right,h0,h1,front,back):
    roof=Facade(builder,(left,front),(right,front),'Lateral chapel roof')
    w=right-left;tile=Polygon([(-w/2,h0-.16),(w/2,h1-.16),(w/2,h1),(-w/2,h0)])
    roof.prism(tile,-(back-front),0,'chapel roof','section of side roof')

def lower_body(builder,lod):
    n=8 if lod else 18
    center=Facade(builder,(-HALF,.25),(HALF,.25),'Central portal and bell front')
    wing=Facade(builder,(-HALF,.74),(HALF,.74),'Lateral chapel fronts')
    tower=4.2;deck=L['tower_deck'];shoulder=L['side_coping'];rise=L['gable_at_tower']
    outer=box(-tower,0,tower,deck-.19);holes=[]
    middle=door(center,0,3.19,7.55,0,lod);holes.append(middle)
    for sign in (-1,1):
        c=sign*3.92
        q=niche(center,c,5.35,lod);holes.append(q)
        center.box(c,2.51,1.10,4.98,.62,.160,'limewash','tower jamb lower pier')
        # Each portal-side buttress steps back in profile between the door and rose levels.
        for z0,hh,width,proj in [(1.45,2.88,1.23,.61),(3.92,1.62,1.08,.46),(9.33,1.08,1.01,.36),(12.55,3.93,.97,.33),(17.58,3.78,.83,.30)]:
            center.box(c,z0,width,hh,proj+.21,(proj-.21)/2,'limewash','projecting stone buttress')
        for side in (-1,1):
            if not lod:
                loc=center.point(c+side*.48,5.20,.25)
                builder.lathe((loc[0],loc[1]),[(5.20,.061),(5.24,.095),(5.35,.066),(8.12,.055),(8.22,.090),(8.36,.06)],'weathered trim',8,'Portal niches/slender engaged shafts')
        for z,width,h in [(3.18,1.26,.14),(3.38,1.16,.10),(4.68,1.34,.19),(4.88,1.22,.10),(9.67,1.24,.20),(10.07,1.43,.19),(10.32,1.39,.24),(14.8,1.15,.20),(15.08,1.23,.13),(19.48,.91,.16)]:
            center.box(c,z,width,h,.48,.112,'weathered trim','pier belt course')
        center.box(c,12.51,.89,4.06,.40,.12,'limewash','upper pier')
        center.box(c,17.41,.78,4.43,.40,.09,'limewash','upper square pilaster')
        holes.append(blind_arcade(center,sign*1.31,lod))
    # Recess the rose through the continuous wall and add its round voussoir arch.
    r=1.59;z=17.13;holes.append(rose(center,0,z,r,lod))
    arc=LineString([(2.13*math.cos(a),17.33+2.13*math.sin(a))for a in np.linspace(0,math.pi,2*n+1)])
    center.prism(arc.buffer(.14,cap_style='flat'),.005,.21,'weathered trim','outer round hood above rose')
    center.wall(0,deck,holes,material='limewash',thickness=.54,outline=outer)
    # Raised central triangular gable and continuous, rounded inner doorway (2017 courtyard photo).
    apex=10.12;eave=7.48;half=2.61
    canopy=Polygon([(-half,.04),(half,.04),(half,eave),(0,apex),(-half,eave)])
    center.prism(canopy.difference(middle.buffer(.20,join_style='mitre')),-.02,.22,'limewash','gable around centre door')
    bead(center,[(-half-.14,eave-.08),(0,apex+.17),(half+.14,eave-.08)],.19,.36)
    for sign in (-1,1):
        center.box(sign*2.42,3.62,.29,7.17,.47,.146,'weathered trim','gable jamb')
    for z0,w,h,m in [(10.35,2*tower+.35,.17,'weathered trim'),(10.61,2*tower+.63,.29,'limewash'),(19.99,2*tower+.30,.20,'weathered trim'),(20.25,2*tower+.54,.27,'limewash'),(20.46,2*tower+.73,.18,'weathered trim')]:center.box(0,z0,w,h,.52,.07,m,'tower string course')
    for sign in (-1,1):
        x=sign*7.36;holes=[door(wing,x,1.82,4.09,0,lod),niche(wing,x,5.19,lod)]
        small=quattrofoil(sign*7.16,11.82,.52,n);holes.append(small)
        wing.prism(small,-.37,-.29,'recess','quatrefoil recessed field');ring(wing,small,.112,.115)
        left,right=sorted([sign*(tower-.24),sign*HALF]);inner=sign*(tower-.24);out=sign*HALF
        edge=out-sign*1.17
        body=Polygon([(inner,0),(out,0),(out,shoulder),(edge,shoulder),(inner,rise)])
        wing.wall(0,rise,holes,material='limewash',thickness=.47,outline=body)
        bead(wing,[(inner,rise+.055),(edge,shoulder+.055),(out,shoulder+.055)],.21,.16)
        for z0,width,h,d in [(3.1,1.0,.12,.17),(9.97,1,.14,.12),(10.23,1,.25,.18),(10.50,1,.13,.16)]:
            wing.box((inner+out)/2,z0,(right-left)*width,h,.57,d,'weathered trim','chapel string course')
        pier=sign*(HALF-.39);wing.box(pier,4.96,.65,9.9,.49,.10,'limewash','outer engaged pier');wing.box(pier,10.03,.88,.22,.74,.16,'weathered trim','outer capital')
        wing.box(pier,11.26,.61,1.24,.41,.07,'limewash','raised gable terminal');wing.box(pier,11.94,.85,.16,.60,.09,'weathered trim','terminal coping')
        co=sorted([(inner,rise-.20),(edge,shoulder-.21),(out,shoulder-.21)])
        for (x0,h0),(x1,h1) in zip(co,co[1:]):sloping_roof(builder,x0,x1,h0,h1,1.25,D)
        side=Facade(builder,(out,.74),(out,D),'Side cut' if sign>0 else 'South return') if sign>0 else Facade(builder,(out,D),(out,.74),'North return')
        side.wall(0,shoulder-.23,material='limewash',thickness=.24)
        # Continuous closure is confined to the documented frontage section.
        back=Facade(builder,(right,D),(left,D),'West cut');bn=back.length/2
        back.wall(0,rise,material='limewash',thickness=.16,outline=Polygon([(-bn,0),(bn,0),*[(bn-(xp-left),zp)for xp,zp in co]]))
    for sign in (-1,1):
        x=sign*tower
        side=Facade(builder,(x,.25),(x,D),'Tower side') if sign>0 else Facade(builder,(x,D),(x,.25),'Tower side')
        edge=-sign*side.length/2
        # The frontmost return recesses behind the statue niche next to the corner.
        slot=box(min(edge,edge+sign*.73)-.002,5.12,max(edge,edge+sign*.73)+.002,8.64)
        side.wall(0,deck-.14,holes=[slot],material='limewash',thickness=.32)
    back=Facade(builder,(tower,D),(-tower,D),'Tower section plane');back.wall(0,deck-.14,material='limewash',thickness=.23)
    builder.plan_prism(box(-tower-.22,.13,tower+.22,D+.08),deck-.22,deck+.025,'weathered trim','Bell platform')
    builder.plan_prism(box(-HALF,.74,HALF,D),0,.075,'weathered trim','Building ground plate')
    builder.plan_prism(box(-tower,.25,tower,.76),0,.075,'weathered trim','Tower threshold')


def polygon_points(x,y,r,n,start):
    return [np.array([x+r*math.cos(start+math.tau*k/n),y+r*math.sin(start+math.tau*k/n)])for k in range(n)]

def spire(builder,x,y,z,r,top,material,lod,label,n=8):
    levels=[(z,r*.925),(z+.10,r),(z+(top-z)*.20,r*.86),(z+(top-z)*.65,r*.37),(top,r*.035)]
    points=[[*p,h] for h,rad in levels for p in polygon_points(x,y,rad,n,math.pi/n)]
    faces=[tuple(reversed(range(n)))]
    for j in range(len(levels)-1):
        for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
    faces.append(tuple((len(levels)-1)*n+k for k in range(n)));builder.add(points,faces,material,label+'/tapering roofs')
    for k in range(n):builder.tube([points[j*n+k]for j in range(len(levels))],r*.021 if r>.90 else .019,'gray seam',5 if lod else 7,label+'/ribs')

def pinnacles(builder,x,y,z,lod):
    label='Belfry/flanking pinnacles';rad=.85;start=math.pi/4;s=polygon_points(x,y,rad,4,start)
    builder.plan_prism(Polygon(s),z,z+.86,'limewash',label+'/stone plinth')
    for a,b in zip(s,s[1:]+s[:1]):
        fc=Facade(builder,a,b,label);q=pointed(0,z+.92,.52,2.49,7 if lod else 12)
        fc.wall(z+.78,z+3.81,[q],.119,material='slate');ring(fc,q,.043,.065,'gray seam')
    spire(builder,x,y,z+3.64,.90,z+9.28,'slate',lod,label,4)
    builder.lathe((x,y),[(z+9.2,.052),(z+9.42,.042),(z+9.57,.011)],'rail iron',6,label+'/finial')

def lantern(builder,lod):
    cy=3.0;deck=L['tower_deck'];base=deck+.07;r=2.12
    # The 2017 bell base has a red shuttered drum. Its neighbours stand open.
    pts=polygon_points(0,cy,r,8,math.pi/8);bottom=base+.13;high=L['spire_base']
    for aa,bb in zip(pts,pts[1:]+pts[:1]):
        side=Facade(builder,aa,bb,'Bell chamber');w=side.length
        panel=opening(0,bottom+.25,w*.73,high-bottom-.73,arch=w*.34,segments=12 if lod else 22)
        side.wall(bottom,high,[panel],.14,'louver red');side.prism(panel,-.28,-.21,'louver shadow','inside the louvres');ring(side,panel,.074,.07,'louver red')
        for zz in np.linspace(bottom+.39,high-.57,12 if lod else 24):
            blade=box(-w,zz-.033,w,zz+.035).intersection(panel);side.prism(blade,-.10,.023,'louver red','sloped red louver blades')
    builder.plan_prism(Polygon(polygon_points(0,cy,r+.12,8,math.pi/8)),high-.16,high+.06,'slate','Belfry/eaves')
    spire(builder,0,cy,high,r+.12,L['spire_ball'],'slate',lod,'Belfry/central spire')
    # Narrow hooded lancets rise part way up the faces of the central spire.
    for j in range(8):
        a=math.tau*j/8;normal=np.array([math.cos(a),math.sin(a)]);tangent=np.array([-normal[1],normal[0]]);v=np.array([0,cy])+normal*(r*.929)
        face=Facade(builder,v-tangent*.39,v+tangent*.39,'Spire lucarnes')
        hood=pointed(0,high+.14,.68,2.65,6 if lod else 10);void=pointed(0,high+.27,.39,1.18,5 if lod else 9)
        face.prism(hood.difference(void),-.17,.06,'slate','lead-covered lucarne');face.prism(void,-.21,-.16,'louver shadow','lucarne recess')
    # The two outer pinnacles and slender connectors can be counted in the front photographs.
    for s in (-1,1):
        pinnacles(builder,s*3.54,1.54,deck+.015,lod)
        for z0 in [deck+2.33,deck+2.48]:builder.tube([(s*1.58,1.97,z0),(s*2.55,1.73,z0+.19),(s*3.51,1.54,z0+.17)],.077,'rail iron',6,'Belfry/bridged side frames')
    # Current ironwork is a thin, regularly spaced vertical railing, unlike the 1908 crossed parapet.
    for start,end in [((-4.03,.21),(4.03,.21)),((-4.03,.21),(-4.03,D)),((4.03,.21),(4.03,D))]:
        a,b=np.array(start),np.array(end);count=max(4,round(np.linalg.norm(b-a)/(.34 if lod else .23)))
        for z0 in [base+.08,base+.87]:builder.tube([[*a,z0],[*b,z0]],.039,'rail iron',6,'Belfry/railing')
        for t in np.linspace(0,1,count+1):
            c=a*(1-t)+b*t;builder.tube([[*c,base+.04],[*c,base+.88]],.022,'rail iron',5,'Belfry/railing')
    ball=L['spire_ball'];top=L['cross_tip']
    builder.lathe((0,cy),[(ball-.11,.06),(ball+.035,.138),(ball+.18,.075),(ball+.23,.042)],'door bronze',9,'Spire/finial globe')
    builder.tube([(0,cy,ball+.15),(0,cy,top)],.044,'rail iron',8,'Spire/crucifix')
    builder.tube([(-.65,cy,top-.46),(.65,cy,top-.46)],.043,'rail iron',8,'Spire/crucifix')
    if not lod:
        for side in (-1,1):
            for x0 in [.30,.52]:builder.tube([(side*x0,cy,top-.53),(side*x0,cy,top-.39)],.018,'rail iron',6,'Spire/cross accents')


def assemble(model,lod):
    lower_body(model,lod)
    lantern(model,lod)


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
