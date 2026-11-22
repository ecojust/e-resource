"""Lower wing roof over the loggia and its abutment against the high buff gable."""
import numpy as np
from shapely.geometry import Polygon
from photo_architecture import Facade
from lawn import Q,EYE,plane_world,pitched,roof_z
from cypress_roof import PALE,RED,JOINT,RIDGE
from cypress_dormer import FIRED,DARK,WOOD,GLASS_RIGHT

def on_face(plane,pixels):
    xy=np.asarray(pixels);rays=np.c_[xy,np.ones(len(xy))]@np.linalg.inv(Q[:,:3]).T
    xyz=EYE+(np.dot(plane.center-EYE,plane.n)/(rays@plane.n))[:,None]*rays
    return Polygon(np.column_stack([(xyz-plane.center)@plane.t,xyz[:,2]]))

def add_porch_roof(b,lod):
    main_eave,main_ridge=pitched([[542.9,238.8],[581.,150.7]])
    face=Facade(b,main_eave,main_ridge,'High gable above loggia')
    wall=on_face(face,[[542.6,239.5],[581.,150.7],[598.,192.6],[594.,195.2],[550.1,247.8]])
    opening=on_face(face,[[569.2,191.2],[574.6,194.8],[574.4,214.2],[569.2,209.8]])
    face.prism(wall.difference(opening),-.11,-.002,FIRED,'exposed gable and small opening')
    face.prism(opening.buffer(.005,join_style=2),-.074,-.064,GLASS_RIGHT,'small gable light')
    face.prism(opening.buffer(.024,join_style=2).difference(opening.buffer(-.022,join_style=2)),-.067,.025,WOOD,'gable light jamb')
    px=[[550.4,246.1],[662.0,240.7],[662.6,192.2],[593.1,194.9]]
    a,c=plane_world(px[:2],1,-1.14);d,e=plane_world(px[2:],1,1.71)
    def stripe(t):
        return ((1-t)*a+t*e,(1-t)*c+t*d)
    q=np.array([a,c,d,e]);normal=np.cross(c-a,e-a);normal/=np.linalg.norm(normal)
    if normal[2]<0:normal=-normal
    slabs=[*(q-.087*normal),*(q-.011*normal)]
    b.add(slabs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],JOINT,'Loggia roof/closed lower bed')
    # The right edge is cropped at the end of the second visible arch.
    count=15
    for row in range(count):
        p0,p1=stripe(row/count);p2,p3=stripe((row+.977)/count)
        tiles=round((np.linalg.norm(p1-p0)+np.linalg.norm(p3-p2))/.50)
        v=[];faces=[];shadow=[];sf=[]
        for j in range(tiles):
            cross=[.0,.23,.64,.983] if lod else[.0,.09,.23,.44,.7,.86,.983]
            ht=[.008,.047,.009,.013]if lod else[.008,.024,.052,.020,.007,.012,.015]
            off=len(v)
            for start,end,lift in [(p0,p1,.013),(p2,p3,.001)]:
                for t,h in zip(cross,ht):
                    u=(j+t)/tiles;v.append((1-u)*start+u*end+normal*(h+lift))
            n=len(cross)
            for k in range(n-1):
                faces.append((off+k,off+k+1,off+k+1+n,off+k+n))
                i=len(shadow);p,q=v[off+k],v[off+k+1];shadow.extend((p,q,q-normal*.025,p-normal*.025));sf.append((i,i+3,i+2,i+1))
        b.add(v,faces,PALE if row%3 else RED,'Loggia roof/tile row '+str(row+1))
        b.add(shadow,sf,JOINT,'Loggia roof/lips row '+str(row+1))
    b.tube([e+normal*.027,d+normal*.027],.068,RIDGE,6 if lod else 12,'Loggia roof/upper ridge')
    b.tube([a-.05*normal,c-.05*normal],.063,DARK,6 if lod else 10,'Loggia roof/gutter')
