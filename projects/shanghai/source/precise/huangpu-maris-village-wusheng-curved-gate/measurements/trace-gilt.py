"""Recover contours of the four gilt gate letters from two years of measured black disks."""
import argparse
import json
from pathlib import Path
import sys

import contourpy
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.optimize import minimize
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

SIZE=170
def projection(camera,station,axes,xyz):
    delta=xyz-np.asarray(camera[:3])
    direction=delta@axes
    bearing=np.arctan2(direction[...,0],direction[...,1])-camera[3]+np.deg2rad(station['north'])
    elevation=np.arctan2(direction[...,2],np.hypot(direction[...,0],direction[...,1]))
    sx=8192*bearing/(2*np.pi)
    ox,oy=station['origin']
    return (sx-ox+4096)%8192-4096, 2048-8192*elevation/(2*np.pi)-oy
def sample(photo,camera,station,axes,centre,radius):
    yy,xx=np.indices((SIZE,SIZE))
    px=(xx+.5)/SIZE*2-1;pz=1-(yy+.5)/SIZE*2
    xyz=np.stack([centre[0]+px*radius,np.full_like(px,-.025),centre[1]+pz*radius],axis=-1)
    sx,sy=projection(camera,station,axes,xyz)
    xmin,ymin=int(sx.min())-3,int(sy.min())-3
    region=np.asarray(photo.crop((xmin,ymin,int(sx.max())+4,int(sy.max())+4)).convert('RGB'),dtype=float)
    return np.stack([map_coordinates(region[:,:,i],[sy-ymin,sx-xmin],order=1,mode='nearest')for i in range(3)],axis=-1)
def pigment(rgb):
    y,x=np.indices(rgb.shape[:2]);inner=(x+.5-SIZE/2)**2+(y+.5-SIZE/2)**2<(.40*SIZE)**2
    r,g,b=rgb.transpose(2,0,1)
    # Red intensity and yellow chroma both distinguish the lit gilt strokes
    # from the blue-grey iron backing under the two different daylight conditions.
    contrast=.75*r+.30*g-.48*b
    baseline,peak=np.percentile(contrast[inner],[34,98])
    return np.clip((contrast-baseline)/(peak-baseline),0,1.6)
def align(moving,fixed,mask):
    y,x=np.indices(fixed.shape);px,py=x-SIZE/2,y-SIZE/2
    def warp(par):
        dx,dy,turn,scale=par;cs=np.cos(turn);sn=np.sin(turn)
        return map_coordinates(moving,[SIZE/2+scale*(px*sn+py*cs)+dy,SIZE/2+scale*(px*cs-py*sn)+dx],order=1,mode='nearest')
    def loss(par):
        a=warp(par)[mask];b=fixed[mask]
        am=a-a.mean();bm=b-b.mean()
        return 1-float(am@bm/np.sqrt((am@am)*(bm@bm)))
    solve=minimize(loss,[0,0,0,1],bounds=[(-10,10),(-10,10),(-.13,.13),(.92,1.08)],method='Powell')
    return warp(solve.x),solve.x,1-solve.fun
def polygons(density):
    paths=contourpy.contour_generator(z=density).lines(.32)
    outlines=[]
    for curve in paths:
        if np.linalg.norm(curve[0]-curve[-1])>.02:continue
        p=Polygon(curve).buffer(0)
        if p.geom_type=='Polygon' and p.area>7:outlines.append(p)
    result=Polygon()
    for p in sorted(outlines,key=lambda x:-x.area):
        result=result.symmetric_difference(p)
    if result.is_empty:return []
    pieces=result.geoms if result.geom_type=='MultiPolygon' else [result]
    def xy(ring):
        # Local face units are fractions of the measured physical radius.
        return [[round(2*(x+.5)/SIZE-1,6),round(1-2*(y+.5)/SIZE,6)]for x,y in list(ring.coords)[:-1]]
    data=[]
    for p in sorted(pieces,key=lambda a:-a.area):
        if p.area<12:continue
        # Bright rim reflections sit outside the lettering and move with the
        # camera. In both source dates the characters lie inside this circle.
        cx,cy=p.centroid.coords[0]
        if np.hypot(cx+.5-SIZE/2,cy+.5-SIZE/2)>.39*SIZE:continue
        p=orient(p.simplify(.52,preserve_topology=True))
        data.append({'shell':xy(p.exterior),'holes':[xy(h)for h in p.interiors]})
    return data
def trace(registration,source_dir,photo_dir,proof=None):
    sys.path.insert(0,str(source_dir))
    from photo_plane import axes
    yy,xx=np.indices((SIZE,SIZE));rr=(xx+.5-SIZE/2)**2+(yy+.5-SIZE/2)**2
    mask=rr<(.41*SIZE)**2;outer=rr>(.43*SIZE)**2
    photos={key:Image.open(photo_dir/(registration['stations'][key]['id']+'.jpg'))for key in ('2017','2020')}
    overview=Image.new('RGB',(4*SIZE,3*SIZE),'#e5e4df')
    records=[]
    for i,d in enumerate(registration['letters']):
        stations=registration['stations']; pictures={}
        for k,im in photos.items():
            st=stations[k]
            pictures[k]=sample(im,st['camera_xyz_yaw'],st,axes,d['centre_xz_m'],d['radius_m'])
        primary=pigment(pictures['2020'])
        other,transform,agreement=align(pigment(pictures['2017']),primary,mask)
        score=gaussian_filter(.6*primary+.4*other,.48);score[outer]=0
        polys=polygons(score)
        records.append(dict(**d,outline=polys,source_alignment=transform.round(6).tolist(),gold_pattern_correlation=round(agreement,5)))
        for y,k in enumerate(['2017','2020']):
            overview.paste(Image.fromarray(pictures[k].clip(0,255).astype('uint8')),(i*SIZE,y*SIZE))
        clip=Image.new('RGB',(SIZE,SIZE),'#171a1e');dr=ImageDraw.Draw(clip)
        def coords(r):return [((x+1)*SIZE*.5,(1-z)*SIZE*.5)for x,z in r]
        for poly in polys:
            dr.polygon(coords(poly['shell']),fill='#ccb077')
            for h in poly['holes']:dr.polygon(coords(h),fill='#171a1e')
        overview.paste(clip,(i*SIZE,2*SIZE))
    if proof:overview.save(proof,quality=92)
    return records
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ['registration','source','photo_dir','output']:ap.add_argument('--'+name,required=True,type=Path)
    ap.add_argument('--proof',type=Path);a=ap.parse_args()
    r=json.loads(a.registration.read_bytes())
    data=trace(r,a.source,a.photo_dir,a.proof)
    a.output.write_text(json.dumps({'source_dates':['2017-10-14','2020-02-22'],'local_registration_date':'2021-01-08','outlines':'Two-dimensional measured contours on the local X/Z sign plane, in units of the radius of each disk.','letters':data},ensure_ascii=False,indent=2)+'\n')
    print([(x['character'],len(x['outline']),x['gold_pattern_correlation'])for x in data])
