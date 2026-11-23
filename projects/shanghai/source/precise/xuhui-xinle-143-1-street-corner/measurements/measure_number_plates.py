"""Rectify two actual enamel plates on the Xinlefang street corner and trace the visible letters."""
from pathlib import Path
import argparse
import hashlib
import json
import contourpy
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from shapely.geometry import Polygon
from shapely.geometry.polygon import orient

PLATES={
    'black-door':{'inscription':['新乐路','143-1'],'tl_tr_br_bl':[(2798,2276),(2892,2272),(2896,2345),(2800,2350)],
                  'ink_box':(.075,.08,.95,.93),'line_thresholds':(59.,47.),'grid':(142,104)},
    'green-lane':{'inscription':['143弄','新乐路'],'tl_tr_br_bl':[(3017,2200),(3182,2190),(3187,2250),(3018,2258)],
                  'ink_box':(.21,.08,.84,.91),'line_thresholds':(102.,86.),'grid':(204,76)},
}
def project_quad(corners):
    unit=[(0,0),(1,0),(1,1),(0,1)]
    A=[];b=[]
    for (x,y),(u,v) in zip(unit,corners):
        A.extend(([x,y,1,0,0,0,-x*u,-y*u],[0,0,0,x,y,1,-x*v,-y*v]));b.extend((u,v))
    return np.r_[np.linalg.solve(A,b),1].reshape(3,3)

def measure(image,plate):
    width,height=plate['grid'];yy,xx=np.indices((height,width))
    u,v=xx/(width-1),yy/(height-1)
    h=project_quad(plate['tl_tr_br_bl'])
    sample=h@np.stack([u.ravel(),v.ravel(),np.ones(u.size)])
    x,y=(sample[:2]/sample[2]).reshape(2,height,width)
    x0,y0=int(x.min())-2,int(y.min())-2
    region=np.asarray(image.crop((x0,y0,int(x.max())+3,int(y.max())+3)).convert('RGB'),float)
    rgb=np.stack([map_coordinates(region[:,:,i],(y-y0,x-x0),order=1)for i in range(3)],axis=-1)
    intensity=rgb@np.array([.57,.34,.09])
    l,t,r,b=plate['ink_box'];valid=(u>=l)&(u<=r)&(v>=t)&(v<=b)
    threshold=np.where(v<.565,*plate['line_thresholds'])
    mask=valid&(intensity>threshold)
    # Trace smooth subpixel boundaries in the rectification. Isolate the two
    # printed lines from the chipped plate edges and the dark fixing grooves.
    raster=np.where(valid,intensity-threshold,-255.)
    outline=contourpy.contour_generator(x=np.arange(width)/(width-1),y=np.arange(height)/(height-1),
                                         z=raster,fill_type='OuterOffset')
    points,offsets=outline.filled(0.,300)
    polygons=[]
    for coords,stops in zip(points,offsets):
        rings=[coords[a:b]for a,b in zip(stops,stops[1:])]
        poly=Polygon(rings[0],rings[1:]).buffer(0).simplify(.0015,preserve_topology=True)
        for shape in getattr(poly,'geoms',[poly]):
            if shape.area<.000075:continue
            shape=orient(shape,sign=1.)
            ring=lambda rr:np.round(np.array(rr.coords)[:-1],5).tolist()
            polygons.append([ring(shape.exterior),*[ring(rr) for rr in shape.interiors]])
    return dict(inscription=plate['inscription'],corners_full_source_px=plate['tl_tr_br_bl'],
                median_letter_srgb=np.rint(np.median(rgb[mask],axis=0)).astype(int).tolist(),
                median_plate_srgb=np.rint(np.median(rgb[valid&~mask],axis=0)).astype(int).tolist(),
                rectified_ink_regions_uv=polygons,traced_regions=len(polygons))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path);parser.add_argument('data',type=Path)
    args=parser.parse_args();sha=hashlib.sha256(args.source.read_bytes()).hexdigest()
    image=Image.open(args.source)
    if image.size!=(5312,2988):raise ValueError('Use the full 5312 × 2988 original.')
    data={'photo':'https://commons.wikimedia.org/wiki/Special:Redirect/page/66206083',
          'creator':'Antigng','date':'2018-02-07','license':'CC BY-SA 4.0',
          'source_sha256':sha,'coordinates':'u right, v down in independently rectified plate quadrilaterals',
          'plates':{name:measure(image,p) for name,p in PLATES.items()}}
    args.data.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
    print([(k,v['traced_regions'],v['median_plate_srgb'],v['median_letter_srgb'])for k,v in data['plates'].items()])
