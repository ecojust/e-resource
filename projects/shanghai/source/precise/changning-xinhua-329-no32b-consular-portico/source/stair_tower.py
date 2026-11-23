"""Faceted stair tower and the two recessed split windows facing the garden."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon,box

JOINT=Path(__file__).absolute().parents[1]/'measurements/joint-court-roof.json'
PARAPET=('parapet point west','parapet shoulder west','parapet shoulder east','parapet point east')
# TL, TR, BR, BL on the native 579 by 386 court photograph.
WINDOWS=(('lower',((322.,242.),(336.5,242.),(337.,286.),(323.,287.5))),
         ('upper',((319.5,168.5),(332.,170.),(331.5,192.5),(319.5,192.))))

CHEEK_PIXELS=((805.,76.),(896.,38.),(895.,192.),(813.,194.))

def height_at_pixel(camera,pixel,start,outer):
    eye=np.asarray(camera['C'])
    ray=np.asarray(camera['R']).T @ np.linalg.solve(camera['K'],[*pixel,1.])
    return float(eye[2]+ray[2]*np.dot(start-eye[:2],outer)/np.dot(ray[:2],outer))

def window_on_face(camera,pixels,start,along,outer):
    centre=np.asarray(camera['C'])
    rays=np.asarray(camera['R']).T @ np.linalg.inv(camera['K'])
    corners=[]
    for u,v in pixels:
        ray=rays @ [u,v,1.]
        distance=np.dot(start-centre[:2],outer)/np.dot(ray[:2],outer)
        if distance<=0:
            raise ValueError('Tower window plane is behind the courtyard camera')
        xyz=centre+distance*ray
        corners.append((np.dot(xyz[:2]-start,along),xyz[2]))
    tl,tr,br,bl=np.asarray(corners)
    return box((tl[0]+bl[0])/2,(br[1]+bl[1])/2,(tr[0]+br[0])/2,(tl[1]+tr[1])/2)

def add_tower(builder,cameras,materials):
    model=json.loads(JOINT.read_bytes())
    points={p['feature']:np.asarray(p['xyz_m']) for p in model['points']}
    parapet=[points[n] for n in PARAPET]
    west,east=parapet[0],parapet[-1]
    # Only the front and oblique cheeks are documented; close the short rear depth.
    parapet.extend(([east[0],5.4,east[2]],[west[0],5.4,west[2]]))
    corners=np.asarray(parapet);ends=np.roll(corners,-1,axis=0)
    vectors=ends[:,:2]-corners[:,:2];lengths=np.linalg.norm(vectors,axis=1)
    tangents=vectors/lengths[:,None];normals=np.column_stack((tangents[:,1],-tangents[:,0]))
    miters=[]
    for i,normal in enumerate(normals):
        last=normals[i-1]
        miters.append((normal+last)/(1.+np.dot(normal,last)))
    labels=('west cheek','window face','east cheek','east return','rear closure','west return')
    for i,(a,b,length,along,outer) in enumerate(zip(corners,ends,lengths,tangents,normals)):
        next_i=(i+1)%len(corners)
        wall=Polygon(((0,0),(length,0),(length,b[2]),(0,a[2])))
        openings=[]
        if i==1:
            for storey,pixels in WINDOWS:
                hole=window_on_face(cameras['wide'],pixels,a[:2],along,outer)
                if not wall.contains(hole):
                    raise ValueError(f'{storey} stair window outside its measured wall')
                openings.append((storey,hole))
                wall=wall.difference(hole)
        if i==0:
            cam=cameras['portrait']
            x0,_,x1,head=window_on_face(cam,CHEEK_PIXELS,a[:2],along,outer).bounds
            # The porch balustrade conceals the sill. Stop at the lowest visible glass.
            bottom=min(height_at_pixel(cam,p,a[:2],outer) for p in CHEEK_PIXELS[2:])
            hole=box(x0,bottom,x1,head)
            if not wall.contains(hole):raise ValueError('West landing window outside its cheek')
            openings.append(('west landing',hole))
            wall=wall.difference(hole)
        def wall_point(u,z,d):
            direction=outer
            if abs(u)<1.e-7:direction=miters[i]
            elif abs(u-length)<1.e-7:direction=miters[next_i]
            xy=a[:2]+u*along+d*direction
            return (float(xy[0]),float(xy[1]),float(z))
        builder.prism(wall,-.18,0.,wall_point,materials['brick'],'stair tower/'+labels[i])
        for storey,hole in openings:
            inner=hole.buffer(-.035,join_style='mitre')
            if inner.is_empty:raise ValueError('Stair sash is narrower than its frame')
            name='stair tower/'+storey+' light';x0,z0,x1,z1=inner.bounds
            if storey=='west landing':
                rail=height_at_pixel(cameras['portrait'],(828.,170.),a[:2],outer)
                panes=(box(x0,z0,x1,rail-.012),box(x0,rail+.012,x1,z1))
                names=('bottom','top')
            else:
                middle=(x0+x1)*.5
                panes=(box(x0,z0,middle-.012,z1),box(middle+.012,z0,x1,z1))
                names=('left','right')
            frame=hole.difference(panes[0]).difference(panes[1])
            builder.prism(frame,-.125,-.085,wall_point,materials['window'],name+'/divided sash')
            for side,pane in zip(names,panes):
                if storey=='lower':
                    # The foliage hides the lowest part. Retain this interval as a plain reveal.
                    limit=np.mean([height_at_pixel(cameras['wide'],p,a[:2],outer) for p in [(336.,278.),(323.,279.)]])
                    left,bottom,right,head=pane.bounds
                    builder.prism(box(left,bottom,right,limit),-.165,-.156,wall_point,materials['window'],name+'/'+side+' obscured base')
                    pane=box(left,limit,right,head)
                builder.prism(pane,-.134,-.126,wall_point,materials['glass'],name+'/'+side+' pane')
