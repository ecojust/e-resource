"""Pitched tiled surfaces and raised joint covers around the photographed service-wing dormers."""
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from service_materials import TILE,EDGE

def cover_tiles(b,start,end,lod,label):
    start,end=np.asarray(start,float),np.asarray(end,float)
    direction=end-start
    length=np.linalg.norm(direction)
    axis=direction/length
    sideways=np.cross(axis,[0.,0.,1.]);sideways/=np.linalg.norm(sideways)
    up=np.cross(sideways,axis)
    size=.31 if not lod else .66
    n=max(1,int(np.ceil(length/size)))
    for i in range(n):
        a=start+axis*length*i/n
        z=start+axis*min(length,length*(i+1)/n+.033)
        pts=[]
        angles=np.linspace(0,np.pi,5 if lod else 9)
        for point,radius in ((a,.099),(z,.104),(z,.077),(a,.072)):
            pts.extend(point+radius*(np.cos(t)*sideways+np.sin(t)*up) for t in angles)
        m=len(angles);faces=[]
        for loop in range(4):
            nxt=(loop+1)%4
            for k in range(m-1):faces.append([loop*m+k,loop*m+k+1,nxt*m+k+1,nxt*m+k])
        faces.extend([[0,m,2*m,3*m],[m-1,4*m-1,3*m-1,2*m-1]])
        # Orient the shell from its measured centreline, including the hollow underside.
        verts=np.array(pts);signed=0.
        for face in faces:
            for k in range(1,len(face)-1):
                signed+=verts[face[0]]@np.cross(verts[face[k]],verts[face[k+1]])
        if signed<0:faces=[f[::-1] for f in faces]
        b.add(pts,faces,TILE,'Eves roof / '+label)

def add_roof(b,frame,lod=False,front_holes=(),side_holes=()):
    w,d,h=frame.width,frame.depth,frame.eave
    ll=frame.left_hip
    # Both dated views show the high roof continuing over the low link at
    # the right end. The last unoccluded ridge pick is read in each image.
    right_marks=[(frame.design,[372,137]),(frame.album,[608,500])]
    right_joint=np.mean([cam.plane(uv,[0,d/2,0],[0,1,0]) for cam,uv in right_marks],axis=0)
    rr=right_joint[0]
    front=-.25;back=d+.24;left=-.29;right=w+.23
    eave=frame.roof_level(front)
    ridge=frame.ridge
    # The front slope uses the same plane as the dormer sills and their cut-outs.
    xy=[(left,front),(right,front),(right,back),(left,back)]
    p=(ll,d/2);q=(rr,d/2)
    face_specs=[
        ([xy[0],(right+.97,front),q,p],frame.roof_level,front_holes,'long courtyard slope'),
        ([xy[0],p,xy[3]],None,side_holes,'left hip above the return'),
    ]
    for outline,fn,holes,label in face_specs:
        pts=Polygon(outline)
        if holes:pts=pts.difference(unary_union(holes))
        if fn:
            mapping=lambda x,y,z:(x,y,fn(y)+z)
        else:
            mapping=lambda x,y,z:(x,y,eave+(x-left)/(ll-left)*(ridge-eave)+z)
        b.prism(pts,-.123,0,mapping,TILE,'Eves roof / '+label)
    # The back slope has no photograph of its openings. The visible ridge and
    # projecting front edge are independently closed; no rear elevation is inferred.
    b.box([(left+right)/2,front+.026,eave-.073],[right-left,.072,.14],EDGE,label='Eves roof / front eaves board')
    b.box([left+.026,(front+back)/2,eave-.073],[.072,back-front,.14],EDGE,label='Eves roof / eaves of return')
    for a,c,label in [([*xy[0],eave],[*p,ridge],'front hip clay covers'),([*xy[3],eave],[*p,ridge],'return hip clay covers'),([*p,ridge],[*q,ridge],'ridge clay covers')]:
        cover_tiles(b,a,c,lod,label)
