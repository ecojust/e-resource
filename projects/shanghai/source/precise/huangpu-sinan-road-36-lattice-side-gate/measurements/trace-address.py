"""Rectify the photographed enamel plaque and trace its seven groups of painted strokes."""
from pathlib import Path
import argparse
import hashlib
import json

import contourpy
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates
from shapely.geometry import Polygon

CROP=(2330,3060,2840,3500)
# Limits select intact portions of each straight enamel rim, omitting rounded corners.
SPAN={'top':(169,338),'bottom':(201,350),'left':(170,269),'right':(145,257)}
def line_fit(x,y):
    keep=np.ones(len(x),bool)
    for _ in range(5):
        a,b=np.polyfit(x[keep],y[keep],1)
        residual=abs(y-(a*x+b))
        keep=residual<max(1.5,2.8*np.median(residual[keep]))
    return [a,b],int(keep.sum())
def intersection(y_of_x,x_of_y):
    a,b=y_of_x;c,d=x_of_y
    x=(c*b+d)/(1-c*a)
    return [x, a*x+b]
def homography(source,dest):
    rows=[];obs=[]
    for (x,y),(u,v) in zip(source,dest):
        rows.extend([[x,y,1,0,0,0,-x*u,-y*u],[0,0,0,x,y,1,-x*v,-y*v]])
        obs.extend([u,v])
    return np.append(np.linalg.solve(rows,obs),1.).reshape(3,3)
def list_polygons(signal):
    paths=contourpy.contour_generator(z=signal).lines(.5)
    rings=[]
    for path in paths:
        if np.linalg.norm(path[0]-path[-1])>.05:continue
        p=Polygon(path).buffer(0)
        if p.geom_type=='Polygon' and p.area>1.5:rings.append(p)
    rings.sort(key=lambda p:-p.area)
    result=Polygon()
    for p in rings:result=result.symmetric_difference(p)
    polygons=list(result.geoms) if result.geom_type=='MultiPolygon' else [result]
    return [p for p in polygons if p.area>2.]
def outline(poly,offset,w,h):
    def norm(coords):
        return [[round((x+offset[0]+.5)/w,6),round((y+offset[1]+.5)/h,6)]for x,y in coords[:-1]]
    return {'shell':norm(poly.exterior.coords[:]),'holes':[norm(i.coords[:])for i in poly.interiors]}
def run(photo):
    a,b,c,d=CROP
    with Image.open(photo) as original:
        if original.size!=(5312,2988) or original.getexif().get(274)!=6:raise ValueError('Unexpected source size or orientation')
        im=original.crop((b,original.height-c,d,original.height-a)).transpose(Image.Transpose.ROTATE_270).convert('RGB')
    rgb=np.asarray(im,dtype=float)
    green=(rgb[:,:,1]-rgb[:,:,0]>16)&(rgb[:,:,2]-rgb[:,:,0]>2)
    # Candidates must be in the photographed sign, away from the rest of the pier.
    yy,xx=np.indices(green.shape)
    green&=(xx>136)&(xx<385)&(yy>99)&(yy<318)
    fits={};used={}
    for side,(lo,hi) in SPAN.items():
        horizontal=side in ('top','bottom');field=green.T if horizontal else green
        scans=[];values=[]
        for index in range(lo,hi+1):
            hits=np.flatnonzero(field[index])
            if hits.size:
                scans.append(index);values.append(hits.min()if side in ('top','left')else hits.max())
        fits[side],used[side]=line_fit(np.array(scans),np.array(values))
    corners=np.array([intersection(fits['top'],fits['left']),intersection(fits['top'],fits['right']),
                      intersection(fits['bottom'],fits['right']),intersection(fits['bottom'],fits['left'])])
    w,h=400,326
    H=homography([(0,0),(w,0),(w,h),(0,h)],corners)
    gy,gx=np.indices((h,w));v=np.stack([gx.ravel()+.5,gy.ravel()+.5,np.ones(w*h)]);q=H@v
    sx,sy=(q[:2]/q[2]).reshape(2,h,w)
    rect=np.stack([map_coordinates(rgb[:,:,i],[sy,sx],order=1) for i in range(3)],axis=2).clip(0,255)
    return rect,corners+np.array([a,b]),used
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('photo',type=Path);parser.add_argument('output',type=Path);parser.add_argument('--rectified',type=Path)
    args=parser.parse_args();rect,corners,used=run(args.photo)
    if args.rectified:Image.fromarray(rect.round().astype('uint8')).save(args.rectified)
    h,w=rect.shape[:2]
    # Each box separates a printed character from the rim, mounting damage and the narrow white scratch.
    boxes={'3':(.20,.075,.49,.66),'6':(.50,.075,.78,.66),'思':(.18,.67,.37,.93),'南':(.38,.67,.59,.93),'路':(.61,.67,.80,.94),'边':(.78,.59,.865,.72),'门':(.865,.59,.96,.72)}
    results={}
    pigment={}
    enamel_samples=[]
    paint_samples=[]
    for key,bb in boxes.items():
        x0,y0,x1,y1=np.rint(np.array(bb)*[w,h,w,h]).astype(int)
        part=rect[y0:y1,x0:x1]
        red,green,blue=part.transpose(2,0,1)
        # Cream strokes have both more red relative to green and higher intensity
        # than the green glaze, even on the side that falls into tree shadow.
        chroma=red-.35*green
        dark,light=np.percentile(chroma,[10,95])
        signal=(chroma-dark)/(light-dark)
        signal[[0,-1],:]=0;signal[:,[0,-1]]=0
        enamel_samples.extend(part[(signal<.10)&(green>40)][::18].tolist())
        paint_samples.extend(part[signal>.9][::8].tolist())
        polygons=list_polygons(signal)
        groups=[outline(p.simplify(.65,preserve_topology=True),(x0,y0),w,h)for p in polygons]
        results[key]=groups
        if key in ('思','南','路','边','门'):
            pigment[key]={}
            for cut in (.68,.82):
                fine=list_polygons(signal*(.5/cut))
                pigment[key][str(cut)]=[outline(p.simplify(.4,preserve_topology=True),(x0,y0),w,h) for p in fine]
    payload={'source_sha256':hashlib.sha256(args.photo.read_bytes()).hexdigest(),'source_url':'https://commons.wikimedia.org/wiki/File:%E6%80%9D%E5%8D%97%E8%B7%AF36%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg','credit':'Antigng, 2018-07-30, CC BY-SA 4.0','rectified_size':[w,h],'enamel_corners_upright':np.round(corners,3).tolist(),'rim_stations':used,'coordinates':'Normalized plaque face, x right and y down. Each shell and its holes form one filled cream paint region.','groups':results,'fine_pigment_contours':pigment,'photo_rgb_medians':{'green_glaze':np.median(enamel_samples,axis=0).round().astype(int).tolist(),'light_paint':np.median(paint_samples,axis=0).round().astype(int).tolist()},'small_letter_detail':'Two optional interior pigment contours preserve the photographed tonal breaks of the smallest characters. They describe paint on one surface.'}
    args.output.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(corners.round(2),{k:(len(ps),sum(len(p['shell']) for p in ps)) for k,ps in results.items()})
if __name__=='__main__':main()
