"""Street elevation of Ampire & Co., 97 Yuanmingyuan Road, Shanghai."""
from math import pi, sin, cos
from pathlib import Path
import sys
from shapely.geometry import Polygon, box, LineString
from shapely.affinity import translate
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3] / 'source/precise/hongkou-general-post-office/source/common'))
from photo_architecture import Facade, opening

BRICK, WARM, DARK = 'red face brick', 'ochre brick', 'dark face brick'
STONE, PALE, WOOD = 'weathered buff stone', 'pale carved stone', 'chestnut sash'
GLASS, IRON, SHADE, SECTION = 'blue-grey glass', 'patinated metal', 'deep reveal', 'plain section'
PALETTE = {name:dict(color=list(rgb), roughness=roughness, metallic=metallic) for name,rgb,roughness,metallic in [
    (BRICK,(.595,.314,.230),.91,0),(WARM,(.66,.372,.27),.92,0),(DARK,(.521,.272,.205),.93,0),
    (STONE,(.575,.535,.478),.88,0),(PALE,(.68,.63,.56),.86,0),(WOOD,(.23,.153,.126),.67,.02),
    (GLASS,(.265,.323,.349),.33,.13),(IRON,(.239,.212,.172),.61,.22),
    (SHADE,(.105,.105,.107),.93,0),(SECTION,(.44,.371,.33),.96,0)]}
HALF, DEPTH = 10.66,3.76
BAYS = [-8.72,-5.72,-2.77,2.77,5.72,8.72]


def panel(f,x,z,w,h,material,depth=.085,back=-.013,label='stone band'):
    f.prism(box(x-w/2,z-h/2,x+w/2,z+h/2),back,depth,material,label)


def glazing(f,o,cols,rows,lod,label,inset=-.20):
    f.prism(o.buffer(.011,join_style=2),inset-.02,inset,GLASS,label+' glass')
    a,b,c,d=o.bounds
    bars=[o.difference(o.buffer(-.075,join_style=2))]
    for i in range(1,cols):
        x=a+(c-a)*i/cols
        bars.append(o.intersection(box(x-.033,b,x+.033,d)))
    for t in rows:
        z=b+(d-b)*t
        bars.append(o.intersection(box(a,z-.035,c,z+.035)))
    f.prism(unary_union(bars),inset+.007,inset+.066,WOOD,label+' sash')
    if not lod:f.prism(o.buffer(.032,join_style=2).difference(o),-.121,-.045,STONE,'reveal lip')


def brick_faces(f,wall,lod):
    if lod:return
    a,b,c,d=wall.bounds
    for row in range(int((d-b)/.182)):
        z=b+.182*row+.009
        for col in range(-1,int((c-a)/.432)+1):
            rank=(row*13+col*31+row*col*7)%23
            if rank not in (1,4,12):continue
            x=a+.432*col+(.216 if row%2 else 0)
            tile=box(x+.009,z,x+.422,z+.16)
            if wall.covers(tile):
                f.builder.add([f.point(u,v,.003)for u,v in list(tile.exterior.coords)[:-1]],[(0,1,2,3)],WARM if rank==4 else DARK,'brick colour variation')


def hood(f,x,lod):
    for side in (-1,1):
        for i in range(6):
            panel(f,x+side*1.13,5.94+i*.34,.28 if i%2 else .37,.29,PALE,.17,label='stone quoin')
        panel(f,x+side*1.13,7.85,.49,.23,STONE,.23,label='scrolled shoulder')
    for z,w,h,d in [(7.98,2.83,.095,.22),(8.10,2.94,.127,.30),(8.22,2.75,.13,.21)]:
        panel(f,x,z,w,h,STONE,d,label='pediment shelf')
    e=opening(x,8.26,2.26,.89,.87,12 if lod else 32)
    f.prism(e,-.01,.13,STONE,'semicircular pediment')
    rim=e.buffer(.076,join_style=2).difference(e).intersection(box(x-1.5,8.25,x+1.5,9.5))
    f.prism(rim,-.01,.218,PALE,'pediment rim')
    if not lod:
        for i in range(9):
            a=.20+i*(pi-.40)/8
            f.builder.tube([f.point(x+.24*cos(a),8.33+.17*sin(a),.138),f.point(x+.88*cos(a),8.33+.62*sin(a),.142)],.024,STONE,5,'fan relief')


def gable(f,x,lod):
    shape=Polygon([(x-1.62,14.76),(x,16.40),(x+1.62,14.76)])
    f.prism(shape,-.52,.045,BRICK,'triangular upper gable')
    for z,w,v,d,m in [(14.79,1.72,16.53,.225,STONE),(14.82,1.54,16.31,.245,PALE)]:
        line=LineString([(x-w,z),(x,v),(x+w,z)])
        f.prism(line.buffer(.10 if m==STONE else .037,join_style=2,cap_style=2),.01,d,m,'gable rake')
    if not lod:
        for i in (-1,0,1):
            p=x+i*.22
            f.prism(Polygon([(p-.092,15.32),(p,15.43),(p+.092,15.32),(p,15.21)]),.049,.087,WARM,'gable lozenge')


def oriel(b,lod):
    n=8 if lod else 16
    angles=[-pi/2+i*pi/n for i in range(n+1)]
    def pt(a,x,y):return (x*sin(a),-.12-y*cos(a))
    def plan(x,y):return Polygon([pt(a,x,y)for a in angles]+[(x,.03),(-x,.03)])
    for i in range(6):
        s=.18+.82*(i+1)/6
        b.plan_prism(plan(.70*s,.55*s),9.02+i*.076,9.02+(i+1)*.076,STONE,'rounded oriel corbel')
    for z,h,rx,ry,m in [(9.47,.13,.62,.45,STONE),(9.60,.19,.77,.62,PALE),(9.79,.20,.86,.77,STONE),
            (9.99,.085,.86,.77,PALE),(12.11,.15,.86,.75,IRON),(12.27,.23,.91,.82,STONE),(12.51,.11,.86,.79,PALE)]:
        b.plan_prism(plan(rx,ry),z,z+h,m,'oriel projecting ledge')
    for a,c in zip(angles,angles[1:]):
        f=Facade(b,pt(a,.80,.71),pt(c,.80,.71),'central oriel')
        panel(f,0,11.085,f.length+.002,2.03,GLASS,0,-.05,'curved oriel glass')
        for z in (10.1,11.55,11.82,12.05):panel(f,0,z,f.length+.002,.048,WOOD,.03,-.01,'oriel transom')
    for a in angles[::2 if lod else 4]:
        x,y=pt(a,.80,.71);b.box((x,y,11.07),(.075,.088,2.04),WOOD,label='oriel moving sash')


def lettering(f):
    glyph={'A':[[(0,0),(.5,1),(1,0)],[(.21,.43),(.78,.43)]],
           'M':[[(0,0),(0,1),(.5,.42),(1,1),(1,0)]],
           'P':[[(0,0),(0,1),(.79,1),(1,.82),(1,.64),(.79,.50),(0,.50)]],
           'I':[[ (.5,0),(.5,1) ]],
           'R':[[(0,0),(0,1),(.79,1),(1,.82),(1,.64),(.79,.50),(0,.50)],[(.53,.50),(1,0)]],
           'E':[[(1,0),(0,0),(0,1),(1,1)],[(0,.51),(.80,.51)]]}
    for c in (-3.42,3.42):
        for i,char in enumerate('AMPIRE'):
            x=c+(i-2.5)*.325-.074
            for line in glyph[char]:
                shape=LineString([(x+.145*u,4.94+.152*z)for u,z in line]).buffer(.013,cap_style=2,join_style=2)
                f.prism(shape,.067,.081,IRON,'AMPIRE inscription '+char)


def flat_front(f,lod):
    seg=12 if lod else 32
    holes=[]
    for x in BAYS:
        for z,w,h,r,cols,rows in [(1.47,1.54,1.9,0,2,(.75,)),(5.49,1.67,1.95,.21,2,(.67,.80)),
                (9.48,2.06,1.98,.25,3,(.69,.83)),(12.83,1.74,1.44,0,3,(.70,))]:
            o=opening(x,z,w,h,r,seg);holes.append(o);glazing(f,o,cols,rows,lod,'street window')
            panel(f,x,z-.047,w+.20,.093,STONE,.122,label='stone sill')
            if z==1.47:panel(f,x,z+h+.04,w+.17,.17,IRON,.235,label='dark shop cornice')
            if r:
                edge=o.buffer(.111,join_style=2).difference(o).intersection(box(x-w*.65,z+h-r-.012,x+w*.65,z+h+.2))
                f.prism(edge,-.012,.076,BRICK,'brick window arch')
                if z>8:panel(f,x,z+h-.024,.19,.27,PALE,.112,label='keystone')
    entry=opening(0,0,1.92,3.83,.99,seg);holes.append(entry)
    f.prism(entry.buffer(.01),-.87,-.82,SHADE,'entry backstop')
    glazing(f,box(-.81,.04,.81,2.75),2,(.86,),True,'deep entry door',-.77)
    for side in (-1,1):
        f.builder.box((side*.975,.49,1.42),(.05,.73,2.84),BRICK,label='entry inner jamb')
    ring=entry.buffer(.23,join_style=2).difference(entry).intersection(box(-1.42,2.80,1.42,4.12))
    f.prism(ring,-.023,.091,BRICK,'entry voussoirs')
    for a in [.10,.79,1.57,2.35,3.04]:
        e=LineString([(.96*cos(a),2.84+.99*sin(a)),(1.21*cos(a),2.84+1.26*sin(a))])
        f.prism(e.buffer(.102,cap_style=2),-.01,.138,PALE,'radial pale arch stone')
    for z,w,h,r in [(5.48,1.79,1.80,0),(9.69,1.52,2.39,.36),(13.35,1.05,1.85,.46)]:
        o=opening(0,z,w,h,r,seg);holes.append(o);glazing(f,o,2,(.73,),lod,'central window')
    outline=unary_union([box(-HALF,0,HALF,14.84),box(-1.64,14.8,1.64,16.63)])
    brick_faces(f,f.wall(0,16.63,holes,.29,BRICK,outline=outline),lod)
    for x in (-HALF+.17,-1.7,1.7,HALF-.17):
        for z,h,w,d,m in [(2.23,4.46,.43,.105,BRICK),(6.65,4.12,.39,.115,BRICK),
                (9.03,.44,.58,.185,STONE),(12.11,5.74,.36,.14,BRICK),(15.06,.26,.61,.18,STONE)]:
            panel(f,x,z,w,h,m,d,label='projecting pier')
        f.prism(Polygon([(x-.33,15.16),(x,15.61),(x+.33,15.16)]),-.13,.18,STONE,'pier cap')
    for x in (-5.72,5.72):hood(f,x,lod);gable(f,x,lod)
    for z,h,m,d in [(.90,.075,STONE,.066),(1.33,.11,STONE,.084),(4.56,.13,STONE,.14),(4.68,.065,PALE,.13),
            (5.07,.58,STONE,.059),(9.37,.13,STONE,.106),(11.91,.12,STONE,.12),(12.29,.62,STONE,.057),
            (12.65,.09,PALE,.081),(14.68,.20,STONE,.12),(14.83,.11,PALE,.151)]:
        for side in (-1,1):
            lo=1.14 if z<1.4 else 1.91
            hi=HALF-.33
            panel(f,side*(lo+hi)/2,z,hi-lo,h,m,d)
    for x in (-7.07,-4.20,4.20,7.07):
        panel(f,x,12.30,.18,.67,PALE,.094,label='spandrel dividing post')
    for z,w,h,d in [(4.55,3.91,.13,.16),(8.0,3.96,.125,.16),(9.31,3.91,.18,.184),(16.56,3.51,.16,.16),(16.69,3.65,.09,.21)]:
        panel(f,0,z,w,h,STONE,d,label='central tower courses')
    lettering(f);oriel(f.builder,lod)


def flank(b,side,lod):
    # A 2020 oblique close-up shows three radial windows on every storey of
    # the half-round projection. Use unwrapped window openings across facets.
    radius, center_y = 2.67, 1.62
    center_x = side * (HALF + radius)
    count = 10 if lod else 24
    angles = [-pi/2 + pi*j/count for j in range(count+1)]
    points = [(center_x+radius*sin(t),center_y-radius*cos(t))for t in angles]
    wall_length = 2*radius*sin(pi/(2*count))*count
    windows=[]
    for cx in [-wall_length*.292,0,wall_length*.292]:
        for z,h in [(1.47,1.98),(5.43,1.86),(9.43,1.79)]:
            opening_rect=box(cx-.515,z,cx+.515,z+h)
            frame=opening_rect.difference(opening_rect.buffer(-.069,join_style=2))
            frame=unary_union([frame,box(cx-.031,z,cx+.031,z+h),
                box(cx-.51,z+h*.73-.035,cx+.51,z+h*.73+.035)])
            windows.append((opening_rect,frame,cx,z,h))
    for index,(start,end) in enumerate(zip(points,points[1:])):
        face=Facade(b,start,end,'half-round end')
        middle=(index+.5)*face.length-wall_length/2
        segment=box(middle-face.length/2,0,middle+face.length/2,12.32)
        def local(shape):
            return translate(shape.intersection(segment),xoff=-middle)
        holes=[]
        for window,frame,cx,z,h in windows:
            clipped=local(window)
            if clipped.area<=.000001:continue
            holes.append(clipped)
            face.prism(clipped,-.19,-.175,GLASS,'radial window glazing')
            clipped_frame=local(frame)
            if clipped_frame.area>.000001:
                face.prism(clipped_frame,-.157,-.085,WOOD,'radial window sash')
            ledge=local(box(cx-.61,z-.083,cx+.61,z+.012))
            if ledge.area>.000001:
                face.prism(ledge,-.012,.139,STONE,'radial stone sill')
            if z<2:
                hood=local(box(cx-.61,z+h-.02,cx+.61,z+h+.13))
                if hood.area>.000001:face.prism(hood,-.014,.235,IRON,'shop hood on curved wing')
        brick_faces(face,face.wall(0,12.32,holes,.27,BRICK),lod)
        for z,h,mat,d in [(1.34,.10,STONE,.075),(4.46,.17,STONE,.14),
                (8.90,.16,STONE,.16),(9.13,.08,PALE,.13),(12.25,.40,STONE,.09),(12.48,.11,PALE,.13)]:
            panel(face,0,z,face.length+.010,h,mat,d)
    front_span=(points[0][0],points[-1][0])
    ring=Polygon(points+[(front_span[1],DEPTH),(front_span[0],DEPTH)])
    b.plan_prism(ring,12.25,12.32,SECTION,'end terrace near parapet')
    for start,end in zip(points,points[1:]):
        b.tube([(*start,12.76),(*end,12.76)],.025,IRON,5,'round terrace top rail')
    for start in points[::2]:b.tube([(*start,12.49),(*start,12.76)],.024,IRON,5,'terrace baluster')
    inner_x=side*HALF
    boundary=[(inner_x,0),(inner_x,center_y)]
    if side<0:boundary.reverse()
    wall=Facade(b,*boundary,'short return next to round wing')
    wall.wall(0,12.32,[],.20,BRICK)
    return points


def add_ampire(builder,lod):
    flat_front(Facade(builder,(-HALF,0),(HALF,0),'east street wall'),lod)
    left=flank(builder,-1,lod);right=flank(builder,1,lod)
    parts=left+[(-HALF,0),(HALF,0)]+right+[(right[-1][0],DEPTH),(left[0][0],DEPTH)]
    builder.plan_prism(Polygon(parts),0,.045,SECTION,'street slice floor')
    builder.plan_prism(box(-HALF,0,HALF,DEPTH),14.70,14.83,SECTION,'upper roof section')
    for side in (-1,1):
        builder.box((side*(HALF-.07),DEPTH/2,13.51),(.14,DEPTH,2.42),BRICK,label='upper flank')
