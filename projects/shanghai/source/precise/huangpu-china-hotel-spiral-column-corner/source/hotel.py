"""Build the China Hotel's short southwest chamfer and the first bay on each street."""
from pathlib import Path
from math import sin, cos, pi, sqrt
import json
from shapely.geometry import Polygon,box,Point,LineString
from shapely import affinity
from shapely.ops import unary_union
from brick import wall_uv
from repeat import repeat_only_texture

HERE=Path(__file__).parent
REG=json.loads((HERE/'frontage-registration.json').read_bytes())
B='interwoven warm facing brick';P='pale limestone carving';D='recessed brown brick';G='smoky blue window glass';F='dark bronze frames';R='red entrance surround';Y='buff diaper brick';BACK='neutral courtyard section'
PALETTE={B:{'color':[1,1,1],'texture':str(HERE/'brick.png'),'roughness':.91},P:{'color':[.77,.735,.665],'roughness':.83},D:{'color':[.29,.23,.197],'roughness':.9},G:{'color':[.16,.237,.274],'metallic':.16,'roughness':.28},F:{'color':[.14,.122,.1],'metallic':.3,'roughness':.56},R:{'color':[.56,.24,.16],'roughness':.74},Y:{'color':[.62,.52,.38],'roughness':.86},BACK:{'color':[.47,.43,.38],'roughness':.90}}
HALF=REG['front_width_m']/2
WING=3.72

def make_face(which):
    if which=='corner':ox,oy,tx,ty=0.,0.,1.,0.
    else:
        tx,ty=REG['wing_tangents'][which];ox,oy=(-HALF if which=='left' else HALF),0.
        if which=='left':tx,ty=-tx,-ty
    return lambda s,z,d:(ox+tx*s+ty*d,oy+ty*s-tx*d,z)

def prism(b,f,geom,back,front,mat,label):
    if geom.area>1e-8:b.prism(geom,back,front,f,mat,label)

def rectangle(b,f,x0,z0,x1,z1,back,front,mat,name):
    prism(b,f,box(x0,z0,x1,z1),back,front,mat,name)

def arch(x,bottom,width,spring,rise,steps):
    r=width/2
    pts=[(x-r,bottom),(x+r,bottom),(x+r,spring)]
    pts.extend((x+r*cos(pi*i/steps),spring+rise*sin(pi*i/steps))for i in range(1,steps+1))
    return Polygon(pts)

def frame(b,f,shape,width,back,front,mat,label):
    edge=shape.buffer(width,join_style=2).difference(shape).intersection(box(-30,0.,30.,50.))
    prism(b,f,edge,back,front,mat,label)

def glazed(b,f,opening,front,lod,title,midbar=True):
    prism(b,f,opening,front-.04,front,G,title+' glass')
    left,bottom,right,top=opening.bounds
    sash=opening.difference(opening.buffer(-.045,join_style=2))
    sections=[.70] if lod else [.25,.70]
    additions=[box(left,bottom+n*(top-bottom)-.019,right,bottom+n*(top-bottom)+.019)for n in sections]
    if midbar:additions.append(box((left+right)/2-.027,bottom,(left+right)/2+.027,top))
    prism(b,f,opening.intersection(unary_union([sash,*additions])),front+.022,front+.068,F,title+' metal sash')

def spiral_column(b,x,lod):
    z0,z1=5.60,15.62
    slices,levels=(28,44)if lod else(44,76)
    vertices=[]
    for i in range(levels+1):
        f=i/levels;z=z0+(z1-z0)*f
        for k in range(slices):
            theta=2*pi*k/slices
            r=.174+.032*cos(5*theta-2*pi*(z-z0)/.765)
            vertices.append((x+r*cos(theta),-.105+r*sin(theta),z))
    faces=[]
    for i in range(levels):
        for k in range(slices):
            low=i*slices;faces.append((low+k,low+(k+1)%slices,low+slices+(k+1)%slices,low+slices+k))
    faces.extend([tuple(reversed(range(slices))),tuple(range(levels*slices,(levels+1)*slices))])
    b.add(vertices,faces,P,'Helical limestone shafts')
    prof=[(5.43,.24),(5.50,.245),(5.55,.217),(5.61,.20),(5.68,.206),(5.74,.196)]
    b.lathe((x,-.105),prof,P,slices,'Spiral column foot rings')
    prof=[(15.52,.179),(15.68,.21),(15.77,.24),(15.83,.24),(15.88,.269),(15.99,.269)]
    b.lathe((x,-.105),prof,P,slices,'Spiral column capitals')

def frieze(b,f,left,right,lod):
    z=5.20
    rectangle(b,f,left,z-.17,right,z+.33,.004,.15,P,'Pale continuous scroll band')
    for zz,front in [(z-.17,.24),(z+.27,.21)]:
        rectangle(b,f,left,zz,right,zz+.065,.12,front,P,'Frieze bead')
    count=max(1,round((right-left)/.77));step=(right-left)/count
    for n in range(count):
        cx=left+(n+.5)*step;verts=[]
        for k in range(23 if not lod else 14):
            t=k/(22 if not lod else 13);angle=(-1.25+1.82*t)*pi;rad=.16*(1-t*.70)
            verts.append(f(cx+rad*cos(angle)*1.45,z+.076+rad*sin(angle),.181))
        b.tube(verts,.017 if lod else .022,P,5 if lod else 7,'Carved running scrolls')

def upper_ledges(b,f,l,r,lod):
    for z,top,d in [(15.86,16.01,.126),(16.02,16.14,.22),(16.31,16.46,.38),(16.50,16.65,.51),(16.70,16.79,.48),(16.80,17.18,.043),(17.18,17.27,.19)]:
        rectangle(b,f,l,z,r,top,-.38,d,P,'Upper entablature and parapet')
    n=max(1,round((r-l)/.35));pitch=(r-l)/n
    for k in range(n):
        x=l+(k+.5)*pitch
        rectangle(b,f,x-.076,16.12,x+.076,16.33,.04,.29,P,'Eave dentils')

def corner(b,lod):
    f=make_face('corner');l,r=-HALF,HALF
    entry=box(-.84,.025,.84,3.08)
    window1=box(-.57,6.19,.57,8.14)
    window2=box(-.6,10.17,.6,11.63)
    window3=arch(0,13.12,1.18,14.56,.58,18 if not lod else 10)
    block=box(l,0,r,15.97).difference(unary_union([entry,window1,window2,window3]))
    prism(b,f,block,-.96,0,B,'Corner brick wall with four openings')
    frame(b,f,entry,.235,-.19,.112,R,'Red square entrance jambs')
    rectangle(b,f,-1.12,3.04,1.12,3.36,-.09,.18,R,'Red entrance lintel')
    # The published street photo shows a returned, glazed entrance at the corner.
    glazed(b,f,entry,-.75,lod,'Returned ground doorway')
    rectangle(b,f,-.84,0,.84,.075,-.86,.16,P,'Entrance threshold')
    for opening,projection,name in [(window1,-.13,'Lower corner window'),(window2,.28,'Central projecting window'),(window3,.24,'Upper arched window')]:
        glazed(b,f,opening,projection-.20,lod,name)
        frame(b,f,opening,.093,-.19,projection+.015,P,name+' stone surround')
    for z0,z1,projection in [(8.14,8.31,.08),(8.66,9.95,.26),(11.64,12.98,.23),(14.99,15.23,.09)]:
        shape=box(-.74,z0,.74,z1).difference(window3);prism(b,f,shape,-.12,projection,P,'Corner bay stone panels')
    for xx in (-.62,.62):
        triangle=Polygon([(xx-.10,8.66),(xx+.10,8.66),(xx+.10,8.45),(xx-.10,8.45)])
        prism(b,f,triangle,.04,.26,P,'Bay toe courses')
    for sign in (-1,1):spiral_column(b,sign*1.73,lod)
    frieze(b,f,l,r,lod);upper_ledges(b,f,l,r,lod)

def wing(b,side,lod):
    f=make_face(side);l,r=(-WING,0.)if side=='left'else(0.,WING)
    x=(l+r)/2;holes=[]
    base=arch(x,.05,2.13,3.16,1.17,24 if not lod else 12)
    holes.append(base);glazed(b,f,base,-.36,lod,'Street arcade')
    frame(b,f,base,.135,-.11,.13,P,'Street arc voussoir border')
    key=Polygon([(x-.09,4.18),(x+.10,4.18),(x+.16,4.47),(x-.15,4.47)])
    prism(b,f,key,.08,.24,P,'Arcade keystones')
    for xx in (x-.55,x+.55):
        bottom=box(xx-.37,6.32,xx+.37,8.31)
        middle=box(xx-.38,10.12,xx+.38,11.80)
        top=arch(xx,13.10,.77,14.63,.44,15 if not lod else 8)
        for hole,d,name in [(bottom,-.22,'Lower wing'),(middle,-.12,'Wing projecting square bay'),(top,-.16,'Wing paired arch')]:
            holes.append(hole);glazed(b,f,hole,d,lod,name,False)
            frame(b,f,hole,.066,-.22,d+.13,P,name+' light trim')
    brick=box(l,0,r,15.97).difference(unary_union(holes))
    prism(b,f,brick,-.97,0,B,'Wing brick with arcade and six windows')
    for z0,z1,d in [(8.61,9.55,.48),(9.60,10.11,.35),(11.79,12.26,.20),(12.25,13.09,.12)]:
        rectangle(b,f,x-1.15,z0,x+1.15,z1,-.2,d,P,'Projecting paired bay stone apron')
    for dx in (-.74,.74):
        rectangle(b,f,x+dx-.09,8.41,x+dx+.09,8.67,-.1,.31,P,'Paired bay corbels')
    for edge in (l+.38,r-.38):
        for z in (7.55,10.57,13.21,15.04):
            diamond=Polygon([(edge-.28,z),(edge,z+.39),(edge+.28,z),(edge,z-.39)])
            frame(b,f,diamond,.045,.001,.022,Y,'Woven buff diamond outlines')
    for edge in (l+.10,r-.10):rectangle(b,f,edge-.055,5.57,edge+.055,15.96,.003,.036,Y,'Vertical buff strips')
    frieze(b,f,l,r,lod);upper_ledges(b,f,l,r,lod)

def add_building(b,lod):
    repeat_only_texture(b,'brick.png')
    corner(b,lod);wing(b,'left',lod);wing(b,'right',lod)
    for part in b.parts:
        if part['material']==B:part['texcoords']=[wall_uv(*pt)for pt in part['vertices']]
