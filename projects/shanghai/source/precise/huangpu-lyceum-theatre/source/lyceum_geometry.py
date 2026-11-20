"""The 57 Maoming Road theatre, with the three-storey entrance photographed in 2012 and 2019."""
import math
from pathlib import Path

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
from photo_architecture import Facade, opening
from sign_lettering import lettering_shapes

BRICK='brown glazed face brick'; JOINT='recessed grey joints'; STONE='warm artificial stone'; PALE='pale projecting stone'
BASE='grey entrance masonry'; GLASS='smoked blue glass'; IRON='patinated black iron'; GOLD='gilded metal lettering'
ROOF='charcoal roofing'; METAL='blue grey sheet metal'; DOOR='bronze and glazed door'; SOFFIT='marquee underside'
PALETTE={
    BRICK:{'color':[.32,.211,.181],'roughness':.73},JOINT:{'color':[.372,.295,.262],'roughness':.92},
    STONE:{'color':[.68,.63,.52],'roughness':.84},PALE:{'color':[.79,.73,.62],'roughness':.8},
    BASE:{'color':[.52,.47,.39],'roughness':.81},GLASS:{'color':[.104,.135,.147],'roughness':.28,'metallic':.16},
    IRON:{'color':[.083,.082,.07],'roughness':.50,'metallic':.45},GOLD:{'color':[.70,.48,.18],'roughness':.32,'metallic':.52},
    ROOF:{'color':[.36,.32,.28],'roughness':.86},METAL:{'color':[.40,.48,.55],'roughness':.56,'metallic':.38},
    DOOR:{'color':[.16,.14,.115],'roughness':.38,'metallic':.34},SOFFIT:{'color':[.28,.25,.22],'roughness':.67}}
FONT=Path(__file__).with_name('fonts')/'LyceumSignSubset.otf'
# Local +X along the chamfer, from the northwestern end towards the southeastern end.
LEFT=(-10.47,-22.90);RIGHT=(8.34,-22.90);WEST=(-26.93,-2.85);NORTH=(-4.05,27.56);EAST=(28.16,4.59)
LS=(-14.95,-17.46);RS=(12.63,-17.14)
SITE=Polygon([LEFT,RIGHT,EAST,NORTH,WEST])
VESTIBULE=Polygon([LEFT,RIGHT,RS,(9.2,-11.0),(-11.6,-10.95),LS])

def masonry(f,cut,lod):
    if lod:return
    x=f.length/2
    # Warm, closely spaced running bond remains visible between the three arch surrounds.
    joints=[]
    for i,z in enumerate(np.arange(6.12,18.20,.23)):
        joints.append(box(-x,z-.008,x,z+.008))
        for u in np.arange(-x+(i%2)*.27,x,.54):
            joints.append(box(u-.009,z,u+.009,z+.23))
    mask=cut.intersection(unary_union(joints))
    if not mask.is_empty:f.prism(mask,.001,.009,JOINT,'running bond')

def pane(f,poly,lod,door=False,arched=False):
    x0,z0,x1,z1=poly.bounds;u=(x0+x1)/2;z=(z0+z1)/2;w=x1-x0;h=z1-z0
    f.prism(poly.buffer(.012),-.38,-.33,DOOR if door else GLASS,'inset doors' if door else 'recessed glass')
    bars=[box(u-.035,z0,u+.035,z1),box(x0,z0+.69*h-.04,x1,z0+.69*h+.04)]
    if not lod:
        bars.extend([box(u-w*.25-.016,z0,u-w*.25+.016,z1),box(u+w*.25-.016,z0,u+w*.25+.016,z1)])
    if door:bars.extend([box(x0,z0+.45*h-.045,x1,z0+.45*h+.045),box(x0,z0,x1,z0+.27)])
    f.prism(poly.intersection(unary_union(bars)),-.31,-.26,IRON,'sash and transom')
    if arched:
        radius=w/2;cz=z1-radius
        for sign in [-1,1]:
            f.line((u,cz,-.25),(u+sign*radius*.69,cz+radius*.71,-.25),.021 if not lod else .028,IRON,6,'arched fanlight spokes')
        if not lod:
            a=np.linspace(0,math.pi,19)
            f.builder.tube([f.point(u+radius*.57*math.cos(t),cz+radius*.57*math.sin(t),-.247)for t in a],.025,IRON,6,f.label+'/fanlight arc')

def corners(f,height=18.10):
    for sign in [-1,1]:
        for i,z in enumerate(np.arange(6.06,height,.81)):
            width=.64 if i%2 else 1.07
            f.box(sign*(f.length/2-width/2),z+.38,width,.77,.17,.045,PALE,'alternating corner quoins')

def cornice(f,lod):
    for z,h,d in [(17.92,.15,.28),(18.14,.28,.39),(18.44,.17,.50),(18.76,.25,.59),(18.97,.18,.44)]:
        f.beam(z,h,d,PALE,label='stepped cornice')
    n=max(3,round(f.length/.51))
    for i in range(n):
        f.box((i+.5-n/2)*f.length/n,18.48,.19 if not lod else .22,.22,.32,.24,STONE,'cornice dentils')

def balustrade(f,u,z,w,lod):
    f.box(u,z+.15,w,.24,.32,.17,PALE,'balcony sill')
    f.box(u,z+.98,w,.13,.23,.16,STONE,'balcony handrail')
    count=6 if lod else 8
    for i in range(count):
        x=u+(i+.5-count/2)*w/count
        profile=[(0,.085),(.13,.11),(.27,.083),(.42,.093),(.54,.113),(.69,.068)]
        for (z0,r0),(z1,r1) in zip(profile,profile[1:]):
            f.builder.tube([f.point(x,z+.23+z0,.16),f.point(x,z+.23+z1,.16)],(r0+r1)/2,STONE,6,f.label+'/turned balusters')

def entrance(b,lod):
    f=Facade(b,LEFT,RIGHT,'Chamfered entrance')
    doors=[];arches=[];top=[]
    for u in [-4.14,0,4.14]:
        q=box(u-1.36,.05,u+1.36,4.25);doors.append(q);pane(f,q,lod,door=True)
        q=opening(u,7.48,3.05,5.06,1.525,14 if lod else 32);arches.append(q);pane(f,q,lod,arched=True)
        outer=q.buffer(.40,join_style=2,quad_segs=5 if lod else 12).difference(q).intersection(box(u-2.08,7.43,u+2.08,13.04))
        f.prism(outer,-.11,.17,PALE,'three stone archivolts')
        f.box(u,12.83,.43,.55,.30,.14,STONE,'keystone')
        balustrade(f,u,7.48,3.18,lod)
    for u in [-2.76,0,2.76]:
        q=box(u-1.19,14.46,u+1.19,17.13);top.append(q);pane(f,q,lod)
        f.prism(q.buffer(.145,join_style=2).difference(q),-.07,.13,PALE,'rectangular upper window frame')
    f.wall(0,5.69,doors,.50,BASE)
    facade=f.wall(5.69,18.62,arches+top,.50,BRICK)
    masonry(f,facade.intersection(box(-f.length/2,6.05,f.length/2,18.2)),lod)
    corners(f);cornice(f,lod)
    f.beam(7.32,.26,.28,PALE,label='three-window stringcourse')
    f.box(0,14.07,8.58,.82,1.11,.38,STONE,'projecting upper balcony')
    for u in [-3.22,-2.43,2.43,3.22]:
        f.box(u,13.51,.35,.76,.79,.23,PALE,'paired stone balcony brackets')
    f.box(0,17.39,8.46,.27,.40,.12,PALE,'upper window head')
    f.box(0,4.83,17.62,.40,2.42,.95,IRON,'dark projecting entrance marquee')
    f.box(0,4.62,17.24,.11,2.15,.91,SOFFIT,'marquee underside')
    for u in [-5.95,-3.02,0,3.02,5.95]:
        f.box(u,5.71,.085,1.76,.10,1.64,IRON,'sign supports')
    for index,char in enumerate('兰心大戏院'):
        glyph=next(iter(lettering_shapes(char,1.46,1.38,font=FONT)))[1]
        glyph=affinity.translate(glyph,xoff=(index-2)*3.0,yoff=5.84)
        f.prism(glyph,1.64,1.78,GOLD,'gilded sign '+char)
    for u in [-7.38,7.38]:
        f.box(u,2.37,.92,3.82,.11,.055,STONE,'stone display surround')
        f.box(u,2.4,.69,3.19,.08,.14,GLASS,'glazed playbill case')

def sidewall(f,lod,high=False,street=True):
    height=18.60 if high else 10.07
    bays=max(1,round(f.length/(4.25 if street else 6.0)))
    lower=[];upper=[]
    for i in range(bays):
        u=(i+.5-bays/2)*f.length/bays;w=min(2.06,f.length/bays*.61)
        if street:
            q=box(u-w*.48,1.16,u+w*.48,3.84);lower.append(q);pane(f,q,lod)
        q=box(u-w/2,6.97,u+w/2,9.28 if not high else 11.61);upper.append(q);pane(f,q,lod)
        if high:
            q=box(u-w*.47,14.52,u+w*.47,17.05);upper.append(q);pane(f,q,lod)
        for q in upper[-(2 if high else 1):]:
            f.prism(q.buffer(.13,join_style=2).difference(q),-.055,.11,PALE,'side window surrounds')
    f.wall(0,5.66,lower,.38,BASE)
    f.wall(5.66,height,upper,.38,BRICK)
    f.beam(5.60,.19,.17,PALE,label='storey line')
    if high:cornice(f,lod)
    else:f.beam(height,.23,.24,STONE,label='wing parapet')

def vault(b,lod):
    center=-2.85;half=6.18;y0,y1=-11.74,6.14;spring=13.52;rise=3.34
    b.plan_prism(box(center-half,y0,center+half,y1),10.02,spring,BRICK,'Hall/clerestory drum')
    count=12 if lod else 32
    angles=np.linspace(0,math.pi,count+1)
    def pt(t,y):return (center+half*math.cos(t),y,spring+rise*math.sin(t))
    for t0,t1 in zip(angles,angles[1:]):
        vertices=[pt(t0,y0),pt(t0,y1),pt(t1,y1),pt(t1,y0)]
        b.add(vertices,[(0,1,2),(0,2,3)],METAL,'Hall/barrel roof')
    for y in np.linspace(y0+.18,y1-.18,7 if lod else 14):
        b.tube([pt(t,y)for t in angles],.044,METAL,6,'Hall/transverse roof ribs')
    for y in [y0,y1]:
        b.add([(center,y,spring)]+[pt(t,y)for t in angles],[(0,i+1,i+2)for i in range(count)],BRICK,'Hall/end tympanum')

def add_building(b,lod):
    entrance(b,lod)
    for a,c,label in [(RIGHT,RS,'South right return'),(LS,LEFT,'North left return')]:
        sidewall(Facade(b,a,c,label),lod,True)
    for a,c,label,street in [(RS,EAST,'Changle Road wing',True),(EAST,NORTH,'East party wall',False),(NORTH,WEST,'Rear wall',False),(WEST,LS,'Maoming Road wing',True)]:
        sidewall(Facade(b,a,c,label),lod,False,street)
    b.plan_prism(SITE,0,.14,BASE,'Theatre/ground footprint')
    b.plan_prism(SITE.difference(VESTIBULE),9.90,10.13,ROOF,'Two-storey wings/roof')
    ring=list(VESTIBULE.exterior.coords)
    for i,(a,c) in enumerate(zip(ring,ring[1:])):
        if i in (0,1,len(ring)-2):continue
        f=Facade(b,a,c,'Vestibule upper returns/'+str(i));f.wall(9.97,18.73,[],.38,BRICK);cornice(f,lod)
    b.plan_prism(VESTIBULE,18.61,18.97,ROOF,'Vestibule/flat entrance roof')
    vault(b,lod)
    fly=box(-13.18,5.08,8.21,16.42).intersection(SITE.buffer(-.64))
    b.plan_prism(fly,10.04,22.30,BRICK,'Stagehouse/masonry body')
    b.plan_prism(fly,22.28,22.60,ROOF,'Stagehouse/roof')
    rim=fly.difference(fly.buffer(-.30))
    b.plan_prism(rim,22.59,22.95,STONE,'Stagehouse/raised parapet')
    b.plan_prism(box(-8.52,10.51,2.31,13.45).intersection(fly.buffer(-.55)),22.57,23.33,ROOF,'Stagehouse/raised roof panel')
