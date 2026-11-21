"""The eight bank window bays and projecting central staircase on Beijing East Road."""
import math
from shapely.geometry import LineString,Polygon,Point,box
from shapely.ops import unary_union
from photo_architecture import Facade,opening
from finish import WALL,GRANITE,TRIM,BED,BASE,IRON,SASH,GLASS
from carved_stone import hung_console,carved_band,raised_arch,stair_sculpture

def arch_ring(face,hole,width,material=GRANITE,projection=.13,label='arch surround'):
    surround=hole.buffer(width,join_style='mitre').difference(hole)
    face.prism(surround,-.045,projection,material,label)

def rail(face,x,z,w,lod,balcony=True):
    # Real open shadow and a return rail distinguish a projecting balcony from a blind panel.
    projection=.92 if balcony else .21
    if balcony:
        face.box(x,z-.12,w+.39,.22,projection+.38,projection/2-.10,TRIM,'balcony slab')
        for side in (-1,1):
            u=x+side*w*.32
            pts=[(u-.13,z-.22),(u+.13,z-.22),(u+.085,z-.68),(u-.08,z-.69)]
            face.prism(Polygon(pts),.15,.50,GRANITE,'paired balcony consoles')
            face.line((x+side*w/2,z+.84,.07),(x+side*w/2,z+.84,projection),.039,IRON,6,'balcony side rails')
            face.line((x+side*w/2,z+.12,projection),(x+side*w/2,z+.84,projection),.035,IRON,6,'balcony side rails')
    for h in (.13,.81,.90):
        face.box(x,z+h,w,.041 if h<.89 else .06,.07,projection,IRON,'wrought iron horizontal bars')
    n=9 if lod else 15
    for i in range(n):
        u=x-w/2+w*i/(n-1)
        face.box(u,z+.47,.026,.69,.040,projection,IRON,'wrought iron uprights')
    if not lod:
        for i in range(4):
            u=x-w/2+(i+.5)*w/4
            curve=[face.point(u+.15*math.cos(t),z+.46+.18*math.sin(t),projection+.025)for t in [j*math.tau/12 for j in range(13)]]
            face.builder.tube(curve,.017,IRON,5,'iron balcony rings')

def street_arch(face,x,width,lod):
    hole=opening(x,.96,width,3.87,width*.46,12 if lod else 24)
    face.window(hole,columns=3 if width>1.4 else 2,rows=3,frame=SASH,glass=GLASS,trim=False,label='bank steel window')
    arch_ring(face,hole,.16,TRIM)
    a,b,c,d=hole.bounds
    spring=d-width*.46
    for fraction in (.16,.34,.50,.66,.84):
        theta=math.pi*fraction
        u=x+(width/2+.10)*math.cos(theta);z=spring+(width*.46+.10)*math.sin(theta)
        face.line((u,z,.145),(u+.12*math.cos(theta),z+.12*math.sin(theta),.145),.018,BED,5,'voussoir joints')
    key=Polygon([(x-.102,d+.09),(x+.102,d+.09),(x+.17,d+.48),(x-.17,d+.48)])
    face.prism(key,.08,.22,GRANITE,'keystones')
    return hole

def window_bay(face,upper_face,x,upper_x,narrow,lod,levels):
    holes=[street_arch(face,x,1.22 if narrow else 1.95,lod)]
    face=upper_face
    x=upper_x
    width=1.14 if narrow else 1.98
    for i,(bottom,top) in enumerate(levels):
        # The inner bays have doors behind iron on the two main balcony levels.
        arched=(i==2)
        aperture=opening(x,bottom,width,top-bottom,.29 if arched else 0,12 if lod else 22)
        holes.append(aperture)
        face.window(aperture,columns=2 if narrow else 3,rows=3,frame=SASH,glass=GLASS,trim=False,label='upper steel window')
        face.box(x,top+.17,width+.36,.20,.33,.065,GRANITE,'window hood')
        if arched:raised_arch(face,x,top+.025,width+.23,.20,lod)
        if not narrow and i in (1,2):rail(face,x,bottom-.025,width+.15,lod)
        elif not narrow and i==3:rail(face,x,bottom-.01,width+.02,lod,False)
    return holes

def pilaster(face,x,z0,z1,lod):
    face.box(x,(z1+z0)/2,.38,z1-z0,.26,.06,TRIM,'channelled stone pilaster')
    for side in (-1,1):
        face.box(x+side*.135,(z0+z1)/2,.040,z1-z0,.038,.202,GRANITE,'pilaster edge flutes')
    for z,w,h,p in [(z0+.08,.55,.16,.34),(z1-.24,.53,.14,.34),(z1-.10,.66,.15,.41),(z1,.77,.11,.47)]:
        face.box(x,z,w,h,p,p/2-.065,TRIM,'pilaster capitals')
    if not lod:
        for sign in (-1,1):
            poly=Polygon([(x+sign*.018,z1-.63),(x+sign*.16,z1-.51),(x+sign*.23,z1-.28),(x+sign*.045,z1-.39)])
            face.prism(poly,.22,.30,GRANITE,'leaf at upper capital')

def run_mouldings(face,start,end,levels):
    for z,h,depth in levels:
        face.box((start+end)/2,z,end-start,h,depth+.15,(depth-.15)/2,TRIM,'horizontal stone courses')

def front_run(face,start,end,positions,lod,levels,height,setback=0.):
    upper=Facade(face.builder,face.point(-face.length/2,0,-setback)[:2],
                 face.point(face.length/2,0,-setback)[:2],face.label+' upper')
    lower_holes=[];upper_holes=[]
    for x,upper_x,narrow in positions:
        rows=window_bay(face,upper,x,upper_x,narrow,lod,levels)
        lower_holes.append(rows[0]);upper_holes.extend(rows[1:])
    ground=box(start,0,end,6.05)
    face.prism(ground.difference(unary_union(lower_holes)),-1.36,-.01,WALL,'ground wall with arches')
    upper.prism(box(start,6.05,end,height).difference(unary_union(upper_holes)),-1.36,-.01,WALL,'set back office wall')
    if setback>0:
        face.box((start+end)/2,5.99,end-start,.16,setback+1.36,-(setback+1.36)/2,GRANITE,'terrace floor')
        # Return the two ends of the recessed upper facade to the solid projection.
        for u in (start,end):
            face.box(u,(height+6.05)/2,.12,height-6.05,setback,-setback/2,WALL,'terrace end return')
    solid=ground.difference(unary_union([a.buffer(.18,join_style='mitre')for a in lower_holes]))
    for z in (.46,.90,1.41,1.92,2.43,2.94,3.45,3.96,4.47,4.98,5.49):
        face.prism(box(start,z-.014,end,z+.014).intersection(solid),-.012,.012,BED,'ground ashlar joints')
    face.box((start+end)/2,.19,end-start,.38,.43,.055,BASE,'ground plinth')
    run_mouldings(face,start,end,[(5.72,.21,.23),(5.91,.11,.40),(6.04,.12,.45),(7.06,.12,.30)])
    run_mouldings(upper,start,end,[(18.12,.12,.22),(18.29,.19,.34),(18.46,.16,.46),
        (22.15,.16,.28),(22.31,.17,.45),(22.48,.13,.53),(height-.10,.20,.22)])
    count=max(1,round((end-start)/.48))
    for j in range(count):
        pos=start+(j+.5)*(end-start)/count
        upper.box(pos,18.13,.145,.21,.37,.085,GRANITE,'middle cornice dentils')
    for (_,x,_),(_,next_x,_) in zip(positions,positions[1:]):
        pilaster(upper,(x+next_x)/2,6.99,18.01,lod)
        hung_console(upper,(x+next_x)/2,17.62,1.31,lod)
        hung_console(upper,(x+next_x)/2,21.81,.66,lod)
        upper.box((x+next_x)/2,20.47,.40,3.55,.21,.045,TRIM,'attic bay piers')
    carved_band(upper,start,end,18.01,lod)
    for _,x,_ in positions:
        upper.box(x,23.04,2.58,.59,.13,.012,WALL,'parapet panels')
        for side in (-1,1):upper.box(x+1.31*side,23.03,.17,.81,.33,.068,GRANITE,'parapet panel divisions')
    # Along the terrace a continuous parapet alternates solid piers with open panels.
    apertures=[]
    for x,_,narrow in positions:
        if narrow:continue
        gap=1.82
        apertures.append(box(x-gap/2,6.22,x+gap/2,6.95))
        for i in range(7):
            u=x-gap/2+i*gap/6
            face.box(u,6.58,.10,.77,.17,.17,GRANITE,'stone balusters')
    face.prism(box(start,6.05,end,7.08).difference(unary_union(apertures)),-.18,.20,GRANITE,'terrace balustrade panels')

def staircase(face,x,lod,portal_builder):
    width=4.36
    low,high=x-width/2,x+width/2
    # Projection of the original stair stack; its landing windows differ from the regular floors.
    sill=[(8.93,11.75,1.83,0),(13.76,16.19,1.71,.28),(23.05,27.16,1.46,.65)]
    cuts=[opening(x,b,w,t-b,a,14 if lod else 30)for b,t,w,a in sill]
    oculus=Point(x,18.36).buffer(.61,quad_segs=8 if lod else 16)
    cuts.append(oculus)
    bounds=Polygon([(low,0),(high,0),(high,28.53),(x,29.77),(low,28.53)])
    portal=box(x-2.10,-.02,x+2.10,6.48)
    face.prism(bounds.difference(unary_union([portal,*cuts])),-1.36,.29,WALL,'projecting stair shaft')
    # Window reveals have a continuous 0.29 m cheek in front of the regular street plane.
    stair=Facade(face.builder,face.point(x-1,0,.31)[:2],face.point(x+1,0,.31)[:2],'staircase')
    for b,t,w,a in sill:
        aperture=opening(0,b,w,t-b,a,14 if lod else 30)
        stair.window(aperture,columns=2,rows=4,trim=False,glass=GLASS,frame=SASH,label='landing steel glazing')
        arch_ring(stair,aperture,.16,GRANITE,.17,'stair window surround')
    round_hole=Point(0,18.36).buffer(.61,quad_segs=8 if lod else 16)
    stair.prism(round_hole,-.33,-.25,GLASS,'oculus glass')
    arch_ring(stair,round_hole,.18,TRIM,.17,'oculus surround')
    for t in (0,math.pi/2):
        stair.line((-.59*math.cos(t),18.36-.59*math.sin(t),-.12),(.59*math.cos(t),18.36+.59*math.sin(t),-.12),.032,SASH,6,'oculus cross')
    for s in (-1,1):
        for i in range(24):
            stair.box(s*(width/2-.18),7.31+i*.47,.36,.425,.37,.061,TRIM,'quoin courses')
        pilaster(stair,s*(width/2-.25),21.34,28.10,lod)
        small=opening(s*1.63,24.41,.43,.89,.19,12)
        stair.prism(small,.015,.17,GRANITE,'flanking blind niche')
        arch_ring(stair,small,.11,TRIM,.24,'niche hood')
    for z,rise,span in [(6.08,.64,4.42),(19.63,1.01,5.03)]:
        for dz,thick,depth in [(0,.182,.37),(.155,.125,.56)]:
            coords=[((i/20-.5)*span,z+dz+rise*math.sin(i*math.pi/20))for i in range(21)]
            stair.prism(LineString(coords).buffer(thick/2,cap_style='flat'),.10,depth,TRIM,'bowed stair cornice')
    for dx,z in [(0,29.70),(.15,29.84)]:
        cornice=LineString([(-2.29,28.50+dx),(0,z),(2.29,28.50+dx)]).buffer(.105,cap_style='flat',join_style='mitre')
        stair.prism(cornice,.09,.49,TRIM,'stair tower pediment')
    stair_sculpture(stair,lod)
    portal_builder(face,x,lod)
