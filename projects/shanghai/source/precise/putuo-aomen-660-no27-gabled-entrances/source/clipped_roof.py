"""Clipped gable, with two pitched flanks, a short hip and tiled ridge."""
import numpy as np
from shapely.geometry import Polygon,box
from shapely.affinity import scale
from garden_gable import x,z,TIMBER

TILES=['Sienna clay roof tile','Smoke dark clay roof tile','Old russet roof tile','Warm fired clay roof tile']
FASCIA='Red brown painted bargeboard'
CAP='Pale weathered roof flashing'
MORTAR='Dark clay bedding'
def course(b,origin,across,up,outline,prefix,lod):
    origin=np.array(origin);across=np.array(across); up=np.array(up)
    normal=np.cross(across,up);normal/=np.linalg.norm(normal)
    sign=1 if normal[2]>=0 else -1
    normal*=sign
    def handed(shape):return shape if sign==1 else scale(shape,xfact=-1.,yfact=1.,origin=(0.,0.))
    def mapper(u,v,depth):return origin+u*sign*across+v*up+depth*normal
    b.prism(handed(outline),-.1,.0,mapper,MORTAR,prefix+'/roof bed')
    x0,y0,x1,y1=outline.bounds
    height=.199;width=.228
    for row in range(int(np.ceil(y1/height))):
        y=row*height
        for col in range(-2,int(np.ceil(x1/width))+2):
            xbase=(col+(row%2)*.5)*width
            surface=outline.intersection(box(xbase+.002,y+.001,xbase+width-.002,y+height+.014))
            if surface.is_empty or surface.area<.00015:continue
            # Head end nestles into the next row. The eaves retain a pronounced lip.
            def tile(u,v,depth):
                return mapper(u,v,depth+.027-.016*(v-y)/height)
            key=TILES[(col*col+2*row+col)%len(TILES)]
            label=prefix+'/course '+str(row+1)
            b.prism(handed(surface),.003,.011,tile,key,label)
            if not lod:
                nib=surface.intersection(box(xbase+width*.81,y+.008,xbase+width*.93,y+height-.018))
                if nib.area>.002:b.prism(handed(nib),.009,.02,tile,key,label+' side rolls')

def add_roof(b,lod):
    front_y=-.205;depth=2.12;hip_depth=.83
    left=np.array([x(106),front_y,z(111)])
    left_clip=np.array([x(205),front_y,z(3)])
    right_clip=np.array([x(306),front_y,z(-2)])
    right=np.array([x(426),front_y,z(84)])
    peak=np.array([x(251),front_y+hip_depth,z(-44)])
    rear=peak.copy();rear[1]=front_y+depth
    for side,eave,shoulder in [('left',left,left_clip),('right',right,right_clip)]:
        # Both flanks have a diagonal front cut from the hip corner to the ridge.
        # At the back of this short roof section the cut face is perpendicular to the ridge.
        projected=peak.copy();projected[1]=front_y
        run=projected-eave; length=np.linalg.norm(run); cross=np.array([0.,1.,0.]);up=run/length
        to_clip=np.dot(shoulder-eave,up)
        shape=Polygon([(0.,0.),(depth,0.),(depth,length),(hip_depth,length),(0.,to_clip)])
        course(b,eave,cross,up,shape,'Clipped gable '+side,lod)
    across=right_clip-left_clip;span=np.linalg.norm(across);across=across/span
    peak_from_left=peak-left_clip;middle=np.dot(peak_from_left,across)
    up=peak_from_left-middle*across;length=np.linalg.norm(up);up/=length
    course(b,left_clip,across,up,Polygon([(0.,0.),(span,0.),(middle,length)]),'Front hip',lod)
    for n,(a,c) in enumerate(zip([left,left_clip,right_clip],[left_clip,right_clip,right])):
        verts=[]
        for dy in [0.,.20]:
            for dz in [-.18,.015]:
                for q in [a,c]:verts.append(tuple(q+[0,dy,dz]))
        b.add(verts,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],FASCIA,'Painted bargeboard/'+str(n+1))
        b.tube([a+[0,0,.035],c+[0,0,.035]],.033,CAP,6 if lod else 10,'Pale edge flashing/'+str(n+1))
    for n,(a,c) in enumerate([(left_clip,peak),(right_clip,peak),(peak,rear)]):
        length=np.linalg.norm(c-a);pieces=max(1,round(length/.315))
        for k in range(pieces):
            t=(k+.015)/pieces;s=(k+1-.015)/pieces
            b.tube([a*(1-t)+c*t+[0,0,.06],a*(1-s)+c*s+[0,0,.06]],.061,TILES[(k+n)%4],6 if lod else 12,'Raised hip and ridge/'+str(n+1)+' clay covers')
    # Close the near soffit back to the wall where it can be seen from the garden.
    for n,(a,c) in enumerate(zip([left,left_clip,right_clip],[left_clip,right_clip,right])):
        verts=[tuple(q+[0,dy,dz]) for dz in [-.185,-.16] for dy in [0,.31] for q in [a,c]]
        b.add(verts,[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],TIMBER,'Front soffit/'+str(n+1))
