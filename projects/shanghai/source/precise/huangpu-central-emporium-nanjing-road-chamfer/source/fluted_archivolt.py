"""Model the shallow, individually measured radial grooves of the entrance archivolt."""
import numpy as np
from corner_fanlight import STONE,read
from photo_plane import D,H,positions

CAMERA=np.linalg.solve(np.column_stack((H[:,0],D,H[:,1])),-H[:,2])


def grid_solid(builder,pixels,front_y,back_y,label):
    top=positions(pixels,front_y)
    underside=positions(pixels,back_y)
    rows,cols=top.shape[:2]
    count=rows*cols
    vertices=np.concatenate((top.reshape(-1,3),underside.reshape(-1,3)))
    faces=[]
    for i in range(rows-1):
        for j in range(cols-1):
            a=i*cols+j
            faces.append((a,a+cols,a+cols+1,a+1))
    face=faces[len(faces)//2]
    a,b,c=vertices[list(face)[:3]]
    if np.dot(np.cross(b-a,c-a),CAMERA-a)<0:
        faces=[f[::-1]for f in faces]
    # Preserve the actual inner and outer extents of each editable flute.
    # Removing common interior grid edges gives the one oriented outer boundary.
    boundary=set()
    for f in faces:
        for a,b in zip(f,f[1:]+f[:1]):
            if (b,a)in boundary:boundary.remove((b,a))
            else:boundary.add((a,b))
    faces+= [tuple(v+count for v in reversed(f))for f in faces]
    faces.extend((b,a,a+count,b+count)for a,b in sorted(boundary))
    builder.add(vertices,faces,STONE,label)


def add_reeded_archivolt(builder,lod,wall_y):
    survey=read('2022-fluted-archivolt.json')
    ribs=np.asarray([survey['left_edge'],*survey['centre_traces'],survey['right_edge']])
    stations=np.arange(0,ribs.shape[1],2 if lod else 1)
    t=np.linspace(0.,1.,7 if lod else 11)
    for i,(a,b)in enumerate(zip(ribs,ribs[1:])):
        a=a[stations];b=b[stations]
        pixels=(1-t[:,None,None])*a[None,:,:]+t[:,None,None]*b[None,:,:]
        # Begin and end on the observed dark groove; most of each interval
        # is the broader, slightly convex face of a rib. These metric depths
        # estimate the shallow stone relief and are not survey measurements.
        across=np.minimum(t,1-t)
        if i==0:across=1-t
        if i==len(ribs)-2:across=t
        relief=.005+.019*(1-np.exp(-(across/.19)**2))
        roll=.91+.09*np.sin(np.pi*stations/(ribs.shape[1]-1))
        front=wall_y-relief[:,None]*roll[None,:]
        grid_solid(builder,pixels,front,wall_y+.008,'Archivolt measured flute face '+str(i+1))
