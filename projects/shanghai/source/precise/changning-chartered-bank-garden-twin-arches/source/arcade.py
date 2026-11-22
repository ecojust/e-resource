"""Garden arcade of the Chartered Bank manager's house, recorded at 796 Jiangsu Road."""
from pathlib import Path
from math import sin,cos,pi
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
from photo_architecture import opening
STONE='Rough dressed brown stone'; PALE='Honey brown stone'; DARK='Darker joint returns'
MORTAR='Recessed buff lime mortar'; LEDGE='Weathered limestone band'; PLASTER='Lime-rendered parapet'
SHADOW='Shaded underside'; ENAMEL='Blue enamel roundel'; NUMERAL='White numeral'
PALETTE={m:dict(color=c,roughness=.92)for m,c in [(STONE,[1.,1.,1.]),(PALE,[.32,.185,.095]),(DARK,[.151,.086,.048]),(MORTAR,[.52,.40,.27]),(LEDGE,[.51,.463,.375]),(PLASTER,[.66,.62,.535]),(SHADOW,[.291,.248,.184]),(ENAMEL,[.009,.056,.229]),(NUMERAL,[.92,.90,.81])]}
PALETTE[STONE]['texture']=str(Path(__file__).with_name('rough-stone.png'))
WIDTH=3.25; CENTRES=(-1.54,1.54); RADIUS=1.20; OUTER=1.61; SPRING=1.12; CAP=2.83
def extrude(b,geom,front,back,mat,label):
    if geom.is_empty:return
    for s in getattr(geom,'geoms',[geom]):
        if s.geom_type=='Polygon' and s.area>.000015:
            b.prism(s,-back,-front,lambda x,z,k:(x,-k,z),mat,label=label)
def rectangle(b,x0,x1,z0,z1,y0,y1,mat,label):
    b.box(((x0+x1)/2,(y0+y1)/2,(z0+z1)/2),(x1-x0,y1-y0,z1-z0),mat,label=label)
def wedge(cx,low,high,r,s,steps):
    return Polygon([(cx+radius*cos(t),SPRING+radius*sin(t)) for radius,a,c in [(r,low,high),(s,high,low)]for t in [a+(c-a)*i/steps for i in range(steps+1)]])
def model(b,lod=False):
    n=42 if lod else 76
    limits=box(-WIDTH,0,WIDTH,CAP)
    holes=unary_union([opening(cx,-.02,2*RADIUS,SPRING+.02+RADIUS,RADIUS,n)for cx in CENTRES])
    outer=unary_union([opening(cx,-.02,2*OUTER,SPRING+.02+OUTER,OUTER,n)for cx in CENTRES])
    extrude(b,limits.difference(holes),.027,.46,MORTAR,'Mortar core enclosing both open archways')
    field=limits.difference(outer)
    for row in range(7):
        bottom=SPRING-.01+row*.306
        for column in range(-7,8):
            left=column*.632+(row%2)*.252
            stone=box(left+.008,bottom+.009,left+.624,bottom+.297).intersection(field)
            extrude(b,stone,-.018,.035,STONE,'Ashlar at garden spandrels')
            dressed=stone.buffer(-.016,join_style=2)
            extrude(b,dressed,-.029-((row+column)%4)*.003,-.013,STONE,'Slightly raised faces on coursed stones')
    for cx in (*CENTRES,):
        side=box(-WIDTH,0,0 if cx<0 else WIDTH,CAP) if cx<0 else box(0,0,WIDTH,CAP)
        # The central impost supports the inside end of both rings; joints taper towards the crown.
        for i in range(17):
            angle0=pi*i/17;angle1=pi*(i+1)/17
            stone=wedge(cx,angle0+.0045,angle1-.0045,RADIUS,OUTER,(3 if lod else 6)).intersection(side)
            extrude(b,stone,-.032,.409,STONE,'Radial masonry of the left arch' if cx<0 else 'Radial masonry of the right arch')
            raised=stone.buffer(-.014,join_style=2)
            extrude(b,raised,-.043-(i%4)*.002,-.028,STONE,'Dressed face of each voussoir')
        for height in (0.,.303,.617,.906):
            for sg in (-1,1):
                xa,xb=sorted([cx+sg*RADIUS,cx+sg*OUTER])
                block=box(xa+.007,height+.007,xb-.007,min(height+.291,SPRING-.027)).intersection(side)
                extrude(b,block,-.024,.448,STONE,'Bonded blocks below arch springs')
    for x,span in [(-3.005,.50),(0,.705),(3.005,.50)]:
        rectangle(b,x-span/2,x+span/2,SPRING-.072,SPRING+.046,-.075,.478,PALE,'Projecting impost course')
    # A small front reveal to each mortar joint is left visible between neighbouring stones.
    for cx in CENTRES:
        for a in (0,pi):
            sign=1 if a==0 else -1
            for k in range(5):
                z=.06+.218*k
                x=cx+sign*(RADIUS+.018)
                rectangle(b,x-.015,x+.015,z,z+.17,.36,.45,DARK,'Inner jamb beds')
    for level,lo,hi,front,back,mat in [('Lower drip',2.81,2.845,-.082,.50,SHADOW),('Pale lower fillet',2.844,2.883,-.115,.51,LEDGE),('Balcony ledge',2.882,2.978,-.139,.52,LEDGE),('Parapet face',2.977,3.755,-.003,.226,PLASTER),('Parapet coping',3.752,3.802,-.062,.27,LEDGE)]:
        rectangle(b,-WIDTH-.056,WIDTH+.056,lo,hi,front,back,mat,level)
    for z,h,depth in [(3.005,.035,-.038),(3.045,.018,-.025),(3.685,.022,-.032)]:
        rectangle(b,-3.05,3.05,z,z+h,depth,.018,LEDGE,'Parapet fillets above balcony drip and below coping')
    for x in (-3.02,3.02):
        rectangle(b,x-.142,x+.142,2.983,3.75,-.035,.232,PLASTER,'Slightly advanced parapet end pier')
        rectangle(b,x-.171,x+.171,3.712,3.774,-.058,.253,LEDGE,'End pier coping')
    disc=Polygon([(0.304*cos(i*2*pi/n),3.398+.304*sin(i*2*pi/n))for i in range(n)])
    extrude(b,disc,-.047,-.012,ENAMEL,'Blue No. 1 roundel on the recorded elevation')
    glyph=Polygon([(-.069,3.498),(-.012,3.531),(.036,3.531),(.036,3.253),(.080,3.249),(.080,3.233),(-.076,3.233),(-.076,3.251),(-.023,3.255),(-.023,3.494),(-.066,3.477)])
    extrude(b,glyph,-.052,-.048,NUMERAL,'Hand-drawn white numeral one')
    # Each dressed stone has its own measured face plane. Normalised stone-face UVs also map the deep return.
    import numpy as np
    for part in b.parts:
        if part['material']!=STONE:continue
        original=np.asarray(part['vertices']); extent=np.maximum(np.ptp(original,axis=0),.002)
        minimum=original.min(axis=0); vertices=[];triangles=[];uv=[]
        for indices in part['triangles']:
            face=original[list(indices)]
            normal=np.cross(face[1]-face[0],face[2]-face[0])
            omit=int(np.argmax(np.abs(normal)))
            axes=[axis for axis in range(3)if axis!=omit]
            offset=len(vertices);vertices.extend(face.tolist());triangles.append((offset,offset+1,offset+2))
            for point in face:
                u,v=(point[axes]-minimum[axes])/extent[axes]
                uv.append([.015+.97*float(u),.985-.97*float(v)])
        part.update(vertices=vertices,triangles=triangles,texcoords=uv)
