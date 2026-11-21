"""Editable model of the photographed compound at 754 Yuyuan Road, Shanghai."""
from pathlib import Path
import json
import math
import sys

import numpy as np
from shapely.geometry import LineString, Polygon, box
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'tools'))
from package_architectural_model import build
from photo_architecture import Facade

P = json.loads((HERE / 'parameters.json').read_bytes())
META = {
    'id': P['id'], 'name':'愚园路754号住宅', 'viewer_page':'yuyuan-road-754.html',
    'audit_directory':'data/audit/yuyuan-road-754-v1/', 'status':'photo-informed-exterior',
    'scope':P['scope'],
    'model_scope_zh':'愚园路754号院内可核实的低房圆拱、方形排风口、灰泥叠弧纹、绿釉筒瓦、两侧绿门和瓦帽门柱，以及退后的两层体量、拱窗和阳台。后翼进深、屋面和被院墙遮住的底层按可见范围估算。保留现有里弄、医院及相邻排屋。',
    'coordinate_convention':'Source X points northwest along the arched frontage, Y inward and Z up. glTF Y up.',
    'map_reference_license':'East Asian Buildings / OpenStreetMap inputs and independent panorama registrations are attributed in the source folder.',
    'interiors_modeled':False,
}
COLORS = {
    'blue grey stucco':(.564,.579,.634),'incised mortar':(.416,.447,.489),
    'pale cement':(.635,.629,.622),'cut coping':(.669,.661,.634),'dark vent':(.214,.211,.206),
    'green barrel tile':(.296,.410,.345),'green tile lip':(.365,.487,.419),
    'pale wall':(.787,.745,.639),'wall incision':(.635,.595,.505),'deep green gate':(.176,.273,.224),
    'umber hinges':(.375,.300,.220),'ivory iron':(.774,.739,.619),'ochre trim':(.660,.536,.323),
    'arch glazing':(.245,.274,.277),'dark casement':(.255,.257,.242),'roof deck':(.514,.509,.480),
    'number plate':(.772,.590,.226),'letter enamel':(.173,.160,.118),'stone plaque':(.578,.559,.503),
}
PALETTE = {k:{'color':list(c),'roughness':.39 if 'tile' in k or k=='arch glazing' else .77} for k,c in COLORS.items()}
LOW_W=4.32; LOW_D=4.95; LOW_H=4.94
X0=-LOW_W/2; X1=LOW_W/2
MIDDLE=(-5.12,4.95,1.84,11.58)
UPPER=(-5.52,11.58,1.84,15.12)
FRONT_POSTS=[(-4.48,-1.61),(-2.28,-1.38),(1.39,-1.48),(3.62,-1.02)]


def opening(center, width, base, crown):
    radius=width/2
    spring=crown-radius
    rim=[(center+radius*math.cos(t),spring+radius*math.sin(t)) for t in np.linspace(0,math.pi,19)]
    return Polygon([(center-radius,base),(center+radius,base),*rim])


def glazing(face, shape, subdivisions=2):
    face.prism(shape,-.15,-.135,'arch glazing','recessed glass')
    frame=shape.difference(shape.buffer(-.043,join_style='mitre'))
    x0,z0,x1,z1=shape.bounds
    members=[frame]
    for i in range(1,subdivisions):
        u=x0+(x1-x0)*i/subdivisions
        members.append(shape.intersection(box(u-.018,z0,u+.018,z1)))
    for h in [z1-(x1-x0)/2,(z0+z1)*.5]:
        members.append(shape.intersection(box(x0,h-.018,x1,h+.018)))
    face.prism(unary_union(members),-.135,-.068,'dark casement','mullions and arch spring')
    face.prism(shape.buffer(.035,join_style='mitre').difference(shape),-.017,.024,'ochre trim','arched reveal')


def scallops(face, poly, lod, spacing=.67, step=.31, pale=False):
    """Cut staggered rising arcs into the face skin. The shaded bottom is visible in the grooves."""
    xmin,zmin,xmax,zmax=poly.bounds
    if lod:
        face.prism(poly,-.026,0,'pale wall' if pale else 'blue grey stucco','massed render')
        return
    trims=[];n=7
    for row in range(math.floor(zmin/step)-1,math.ceil(zmax/step)+1):
        z=row*step; offset=(row%2)*spacing/2
        for col in range(math.floor(xmin/spacing)-1,math.ceil(xmax/spacing)+1):
            x=(col+.5)*spacing+offset
            points=[(x+t*spacing*.96,z+step*.69*math.sqrt(max(0,1-(t-.5)**2*4))) for t in np.linspace(0,1,n)]
            trims.append(LineString(points).buffer(.008,cap_style='flat',join_style='mitre'))
    cut=unary_union(trims).intersection(poly)
    face.prism(poly,-.026,-.011,'wall incision' if pale else 'incised mortar','incised finish / base')
    face.prism(poly.difference(cut),-.011,.0001,'pale wall' if pale else 'blue grey stucco','fish-scale stucco tooling')


def barrel_row(face,height,lod,spacing=.208,outward=.245,drop=.095,upper=0.0):
    """An upper half cylinder over each pan, with a hollow lip at the projecting edge."""
    count=max(1,round(face.length/(spacing*(1.58 if lod else 1))));pitch=face.length/count;rad=min(.127,pitch*.48)
    steps=3 if lod else 6
    verts=[];quad=[];edge=[]
    for i in range(count):
        u=-face.length/2+(i+.5)*pitch
        start=len(verts)
        for distance,top,radius in [(-.033,height+upper,rad),(outward,height-drop,rad),(outward,height-drop,rad-.019),(-.033,height+upper,rad-.019)]:
            for theta in np.linspace(math.pi,0,steps+1):
                verts.append(face.point(u+radius*math.cos(theta),top+radius*math.sin(theta),distance))
        for row in range(4):
            q=quad if row!=1 else edge
            for j in range(steps):
                a=start+row*(steps+1)+j;b=start+((row+1)%4)*(steps+1)+j
                q.append((a,a+1,b+1,b))
        for j in (0,steps):
            quad.append(tuple(start+k*(steps+1)+j for k in range(4)))
    face.builder.add(verts,quad,'green barrel tile',face.label+'/barrel tile')
    face.builder.add(verts,edge,'green tile lip',face.label+'/exposed hollow lips')
    face.box(0,height-drop+.008,face.length,.038,outward+.028,outward*.45,'green barrel tile','tile underpan')


def wall(face,bottom,top,holes,lod,pattern=False,body='blue grey stucco'):
    shell=box(-face.length/2,bottom,face.length/2,top)
    if holes:shell=shell.difference(unary_union(holes))
    if pattern:
        face.prism(shell,-.16,-.027,body,'masonry backing')
        scallops(face,shell,lod)
    else:
        face.prism(shell,-.16,0,body,'masonry wall')


def roof_shell(b,rect,h,name,lod,patterns=(),apertures=None):
    a,bb,c,d=rect
    edges=[((a,bb),(c,bb)),((c,bb),(c,d)),((c,d),(a,d)),((a,d),(a,bb))]
    for index,(start,end) in enumerate(edges):
        face=Facade(b,start,end,name+'/'+['front','north','rear','south'][index])
        holes=(apertures or {}).get(index,[])
        wall(face,.07,h,holes,lod,index in patterns)
        for aperture in holes:glazing(face,aperture,3 if aperture.bounds[2]-aperture.bounds[0]>1.05 else 2)
        if index in patterns:barrel_row(face,h-.15,lod)
        face.box(0,h+.008,face.length,.078,.206,-.026,'cut coping','low parapet cap')
    b.plan_prism(box(a,bb,c,d),h-.26,h-.19,'roof deck',name+'/inferred recessed roof')
    b.plan_prism(box(a,bb,c,d),-.015,.11,'pale cement',name+'/base')


def metal_scroll(face,lod):
    for x in np.linspace(-1.44,1.44,13 if not lod else 9):
        face.box(x,1.91,.022,1.10,.035,.146,'ivory iron','vertical iron grille')
    for z in [1.37,2.43]:face.box(0,z,2.98,.030,.042,.148,'ivory iron','upper and lower rails')
    def wire(coords,label):
        face.builder.tube([face.point(u,z,.15)for u,z in coords],.014 if lod else .011,'ivory iron',5 if lod else 7,face.label+'/'+label)
    for side in [-1,1]:
        wire([(side*u,z)for u,z in [(0,2.92),(.12,2.78),(.39,2.66),(.51,2.48),(.69,2.41)]],'pitched central crown')
        for center,base,radius in [(.19,2.59,.12),(.53,2.48,.074),(1.03,2.49,.087),(1.29,2.47,.074)]:
            theta=np.linspace(.25*math.pi,2.30*math.pi,9 if lod else 18)
            rs=np.linspace(radius,radius*.22,len(theta))
            wire([(side*(center+rr*math.cos(t)),base+rr*math.sin(t)) for t,rr in zip(theta,rs)],'curled return')


def front_room(b,lod):
    front=Facade(b,(X0,0),(X1,0),'East arched front')
    arched=opening(0,1.13,1.26,3.51);vent=box(-.245,4.42,.245,4.91)
    wall(front,.07,LOW_H,[arched,vent],lod,True);glazing(front,arched,3)
    front.prism(vent,-.18,-.17,'dark vent','square opening at parapet')
    frame=box(-.45,4.20,.45,5.04).difference(vent)
    front.prism(frame,-.015,.096,'pale cement','raised vent frame')
    if not lod:
        for j in range(4):front.box(0,4.48+j*.116,.465,.022,.031,-.125,'dark casement','vent grille')
    for left,right in [(X0,-.446),(.446,X1)]:
        sub=Facade(b,(left,0),(right,0),'East eaves')
        barrel_row(sub,4.57,lod)
    metal_scroll(front,lod)
    b.plan_prism(box(X0,-.235,X1,.07),1.23,1.35,'pale cement','East room / grated window sill')
    for i,(a,c)in enumerate([((X1,0),(X1,LOW_D)),((X1,LOW_D),(X0,LOW_D)),((X0,LOW_D),(X0,0))]):
        f=Facade(b,a,c,'East room / '+['north wall','rear','south return'][i])
        wall(f,.06,LOW_H,[],lod,i!=1)
        if i!=1:barrel_row(f,4.57,lod)
    b.plan_prism(box(X0,0,X1,LOW_D),LOW_H-.28,LOW_H-.19,'roof deck','East room / sheltered flat deck')
    b.plan_prism(box(X0+.025,.025,X1-.025,LOW_D-.025).boundary.buffer(.10,cap_style='flat',join_style='mitre'),LOW_H-.04,LOW_H+.036,'cut coping','East room / continuous parapet coping')
    b.plan_prism(box(X0,0,X1,LOW_D),-.015,.099,'pale cement','East room / base')


def gallery(b,lod):
    # Three rounded, upper-level openings behind the short stone balustrade are visible together.
    x=UPPER[2]; y0,y1=10.10,13.98
    b.plan_prism(box(x-.18,y0,x+1.11,y1),3.90,4.16,'pale cement','Gallery / cantilevered floor')
    points=[((x,y0),(x+1.11,y0)),((x+1.11,y0),(x+1.11,y1)),((x+1.11,y1),(x,y1))]
    for i,(a,c) in enumerate(points):
        f=Facade(b,a,c,'Gallery / rail '+str(i+1))
        n=max(2,round(f.length/.32));pitch=f.length/n
        holes=[box(-f.length/2+(j+.5)*pitch-.065,4.31,-f.length/2+(j+.5)*pitch+.065,4.92) for j in range(n)]
        wall(f,4.14,5.10,holes,lod,False,'pale cement');f.box(0,5.11,f.length+.045,.095,.22,0,'cut coping','rail cap')


def side_shelter(b,lod):
    # Separate shallow roof and ochre inner arch on the southern, plaque-facing return.
    a,c=-4.97,-2.10
    roof=Facade(b,(a,4.92),(c,4.92),'Southern lean-to')
    door=opening(-.30,.88,.12,2.74)
    wall(roof,.06,3.47,[door],lod,True);roof.prism(door,-.115,-.10,'ochre trim','recessed entrance')
    for x in (a,c):b.box((x,5.51,1.71),(.14,1.22,3.35),'blue grey stucco',label='Lean-to/return')
    b.plan_prism(box(a,4.91,c,6.02),3.39,3.48,'green barrel tile','Lean-to/fascia')
    barrel_row(roof,3.89,lod,.215,.75,.46)


def court(b,lod):
    # The two green gates flank the central cream wall with its own tiled cap.
    def pillar(x,y,index):
        b.box((x,y,1.26),(.34,.34,2.52),'pale wall',label=f'Gate {index}/rendered shaft')
        for k,(r,z) in enumerate([(.23,2.48),(.224,2.54),(.175,2.65),(.115,2.76)]):
            b.box((x,y,z),(r*2,r*2,.080),'green barrel tile' if k else 'cut coping',label=f'Gate {index}/pyramidal tile cap')
        for k,(a,c)in enumerate([((x-.19,y-.19),(x+.19,y-.19)),((x+.19,y-.19),(x+.19,y+.19)),((x+.19,y+.19),(x-.19,y+.19)),((x-.19,y+.19),(x-.19,y-.19))]):
            f=Facade(b,a,c,f'Gate {index}/return '+str(k));barrel_row(f,2.74,lod,.13,.12,.22)
        f=Facade(b,(x-.169,y-.17),(x+.169,y-.17),f'Gate {index}/incised pier');scallops(f,box(-.167,.12,.167,2.46),lod,.61,.36,True)
    for index,p in enumerate(FRONT_POSTS):pillar(*p,index+1)
    p0,p1,p2,p3=FRONT_POSTS
    for i,(a,c) in enumerate([(p0,p1),(p2,p3)]):
        f=Facade(b,a,c,'Deep green courtyard gate '+str(i+1));w=f.length-.32
        f.box(0,1.18,w,2.35,.074,-.023,'deep green gate','painted gate leaves')
        f.box(0,1.17,.018,2.28,.022,.030,'umber hinges','vertical join')
        f.box(-.11,1.13,.025,.16,.048,.053,'umber hinges','handle')
        if i==0:
            f.box(0,2.05,.29,.20,.035,.032,'number plate','754 address panel')
            for u,digit in [(-.072,7),(0,5),(.072,4)]:
                patterns={7:'abf',5:'acdfg',4:'bcfg'}
                seg={'a':((-.021,.044),(.021,.044)),'b':((.021,.044),(.021,.004)),'c':((.021,-.004),(.021,-.043)),'d':((-.021,-.044),(.021,-.044)),'f':((-.021,.044),(-.021,0)),'g':((-.021,0),(.021,0))}
                bits='abc' if digit==7 else patterns[digit]
                for code in bits:
                    t1,t2=seg[code];part=LineString([(u+t1[0],2.055+t1[1]),(u+t2[0],2.055+t2[1])]).buffer(.005,cap_style='flat')
                    f.prism(part,.053,.059,'letter enamel','street number '+str(digit))
    for i,(a,c) in enumerate([(p1,p2),((-5.37,1.05),p0),(p3,(3.64,7.36))]):
        f=Facade(b,a,c,'Enclosure '+str(i+1));wall(f,.005,2.30,[],lod,False,'pale wall')
        if i==0:
            scallops(f,box(-f.length/2,.19,f.length/2,2.08),lod,.76,.34,True)
            barrel_row(f,2.26,lod,.19,.18,.10)
        else:
            f.box(0,2.31,f.length,.10,.22,0,'cut coping','wall cap')
        if i==1:
            f.box(f.length*.29,1.75,.67,.45,.055,.047,'stone plaque','rectangular historical-building plaque')


def assemble(builder,lod=False):
    front_room(builder,lod)
    mid_holes=[opening(-1.69,.71,.66,2.65),opening(-.39,.71,.66,2.65)]
    roof_shell(builder,MIDDLE,5.79,'Stepped return',lod,(1,3),{1:mid_holes})
    u0,v0,u1,v1=UPPER
    holes=[opening(x,w,4.65,h)for x,w,h in [(-1.92,.68,6.39),(-.58,.84,6.79),(.92,.73,6.62)]]
    side=[opening(x,.60,4.75,6.68)for x in [-1.00,.06,1.02]]
    roof_shell(builder,UPPER,8.37,'Upper wing',lod,(0,1,3),{0:holes,1:side})
    side_shelter(builder,lod);gallery(builder,lod);court(builder,lod)
    assert all(len(p['label'].encode())<=63 for p in builder.parts), 'Editable object name exceeds Blender limit' 


if __name__=='__main__':
    from final_preview import package
    package(build,HERE,META,PALETTE,assemble)
