"""Create four distinct raised foliage wreaths on the photographed street pilasters."""
import json
from pathlib import Path

import numpy as np
from photo_plane import D, H, position

DATA=Path(__file__).resolve().parents[1]/'measurements/four-photographed-wreaths.json'
RED='Russet wreath relief'
EDGE='Dark red wreath returns'
def pigment(rgb):
    values=np.asarray(rgb)/255.
    return dict(color=np.where(values<.04045,values/12.92,((values+.055)/1.055)**2.4).tolist(),roughness=.89,metallic=0.)
PALETTE={RED:pigment([133,84,72]),EDGE:pigment([110,66,55])}

CAMERA = np.linalg.solve(np.column_stack((H[:,0],D,H[:,1])),-H[:,2])

def outward_front(a,b,c):
    # On an obliquely viewed, steep fold, a surface facing the source camera
    # can have a positive component along the street-wall normal.
    return np.dot(np.cross(b-a,c-a),CAMERA-a)>0

def section(builder,rows,angles,material,label):
    geometry=rows[angles]
    length,breadth=geometry.shape[:2]
    faces=[]
    for i in range(length-1):
        for j in range(breadth-1):
            k=i*breadth+j
            face=(k,k+breadth,k+breadth+1,k+1)
            faces.append(face)
    vertices=geometry.reshape(-1,3)
    if faces and not outward_front(*(vertices[list(faces[len(faces)//2])[:3]])):
        faces=[face[::-1]for face in faces]
    builder.add(vertices,faces,material,label)

def edge_wall(builder,path,base,inner,label):
    n=len(path);verts=np.vstack((path,base));faces=[]
    # Rays in the source photograph run clockwise in image coordinates. Test
    # the actual wall-space radial direction so the hole lining faces inward.
    centre=np.mean(path,axis=0)
    for i in range(n):
        j=(i+1)%n
        f=(i,j,j+n,i+n)
        normal=np.cross(verts[j]-verts[i],verts[j+n]-verts[i])
        radial=verts[i]-centre;radial[1]=0
        if (np.dot(normal,radial)<0)!=inner:f=f[::-1]
        faces.append(f)
    builder.add(verts,faces,EDGE,label)

def add_wreaths(builder,lod,pier_y):
    report=json.loads(DATA.read_bytes())
    depths=np.broadcast_to(np.asarray(pier_y,dtype=float),(4,))
    overlaps=json.loads((DATA.parent/'observed-leaf-overlaps.json').read_bytes())['wreaths']
    for wreath,carving,back in zip(report['wreaths'],overlaps,depths):
        inner=np.asarray(wreath['inner'])
        outer=np.asarray(wreath['outer'])
        relief=np.asarray(wreath['normalized_relief'])
        stations=len(inner)
        stops=sorted(set(wreath['groove_stations'])|{0,stations})
        radial=np.arange(relief.shape[1])
        if lod:radial=radial[::2]
        weights=radial/(relief.shape[1]-1)
        relief_edges=np.zeros_like(relief)
        station_grid=np.arange(stations)[:,None]
        for fold in carving['folds']:
            path=np.asarray(fold['trough_path'])[None,:]
            delta=(station_grid-path+stations/2)%stations-stations/2
            lip=2.5*fold['lip_direction']
            # The repeated dark line lies below the edge of an adjacent leaf.
            # Its measured diagonal through the band controls that overlap.
            relief_edges+=-.025*np.exp(-.5*(delta/1.25)**2)
            relief_edges+=.021*np.exp(-.5*((delta-lip)/1.85)**2)
        xyz=[];bases=[]
        for i in range(stations):
            p=inner[i,None,:]+weights[:,None]*(outer[i]-inner[i])[None,:]
            rounding=np.sin(np.pi*weights)**.76
            raised=.025+rounding*(.069+.032*relief[i,radial]+relief_edges[i,radial])
            # Depth is nominal. Placing the measured silhouettes on their
            # individual camera rays keeps the photographed central openings.
            row=[position(*uv,float(back-h))for uv,h in zip(p,raised)]
            xyz.append(row)
            bases.append([position(*uv,float(back+.006))for uv in p])
        xyz=np.asarray(xyz);bases=np.asarray(bases)
        number=str(wreath['number'])
        select=np.unique(np.r_[np.arange(0,stations,2 if lod else 1),np.array(stops[:-1])])
        closed_stations=np.r_[select,stations]
        for j,(lo,hi)in enumerate(zip(stops,stops[1:]),1):
            angles=closed_stations[(closed_stations>=lo)&(closed_stations<=hi)]%stations
            section(builder,xyz,angles,RED,'Wreath '+number+' measured fold '+str(j))
        edge_wall(builder,xyz[select,0],bases[select,0],True,'Wreath '+number+' inner return')
        edge_wall(builder,xyz[select,-1],bases[select,-1],False,'Wreath '+number+' outer return')
        # An annular back keeps each piece self-contained for editing. Its
        # central void is retained all the way to the underlying pilaster.
        ring=np.r_[select,select[:1]];a=bases[ring,0];b=bases[ring,-1]
        verts=np.vstack([a,b]);count=len(a)
        faces=[(i,i+1,i+1+count,i+count)for i in range(count-1)]
        f0=faces[0]
        if np.cross(verts[f0[1]]-verts[f0[0]],verts[f0[2]]-verts[f0[0]])[1]<0:faces=[f[::-1]for f in faces]
        builder.add(verts,faces,EDGE,'Wreath '+number+' concealed annular back')
