"""Sample the open centres, two silhouette edges, and local folds of four photographed wreaths."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy

import numpy as np
from PIL import Image,ImageDraw,ImageOps
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.signal import find_peaks
from shapely.geometry import Polygon
from shapely import contains_xy

def sampled_fields(im,ordinal,box,methods):
    rgb,_,mask=methods['large_ring'](im)
    loops=sorted(methods['outline'](mask),key=lambda p:-abs(Polygon(p).area))
    if len(loops)<2:raise ValueError('Expected an outer silhouette and an open centre')
    outer=Polygon(loops[0]);opening=Polygon(loops[1])
    centre=np.array(opening.centroid.coords[0])
    theta=np.arange(256)*2*np.pi/256
    along=np.stack([np.cos(theta),np.sin(theta)],axis=1)
    distances=np.arange(0,max(im.size),.22)
    rays=centre[None,None,:]+along[:,None,:]*distances[None,:,None]
    in_outer=contains_xy(outer,rays[:,:,0],rays[:,:,1])
    in_inner=contains_xy(opening,rays[:,:,0],rays[:,:,1])
    # The source band is star-shaped around the visible pale centre. Pick the
    # furthest boundary crossing in the rare concave notch with multiple crossings.
    outer_r=distances[in_outer.shape[1]-1-np.argmax(in_outer[:,::-1],axis=1)]
    inner_r=distances[in_inner.shape[1]-1-np.argmax(in_inner[:,::-1],axis=1)]
    a=centre+along*inner_r[:,None];b=centre+along*outer_r[:,None]
    v=np.linspace(0,1,15)
    xy=a[:,None,:]+(b-a)[:,None,:]*v[None,:,None]
    src=(.52*rgb[:,:,0]+.36*rgb[:,:,1]+.12*rgb[:,:,2])
    if ordinal==3:
        # The distinct diagonal black utility wire crosses the lower right wreath.
        # Inpaint this narrow band only for estimating small relief variations.
        yy,xx=np.indices(src.shape);wire=abs(yy-219-.609*xx)<3
        a1=map_coordinates(src,[yy-4.5,xx],order=1,mode='nearest')
        a2=map_coordinates(src,[yy+4.5,xx],order=1,mode='nearest')
        src=np.where(wire,(a1+a2)*.5,src)
    intensity=map_coordinates(src,[xy[:,:,1],xy[:,:,0]],order=1,mode='nearest')
    fine=gaussian_filter(intensity,(1.15,.68),mode=('wrap','nearest'))
    broad=gaussian_filter(fine,(5.5,2.1),mode=('wrap','nearest'))
    relief=np.clip((fine-broad)/max(6.,np.percentile(abs(fine-broad)[:,2:-2],91)),-1.4,1.4)
    # Component boundaries follow persistent dark grooves through the band. An
    # individual leaf's depth is inferred, while outline and groove position
    # remain tied to image measurements.
    crease=-np.median((fine-broad)[:,3:12],axis=1)
    cyc=np.tile(gaussian_filter(crease,1.2,mode='wrap'),3)
    peaks,_=find_peaks(cyc,distance=10,prominence=max(3.,np.percentile(abs(crease),52)))
    seams=[int(i-256)for i in peaks if 256<=i<512]
    def camera(p):return np.round(p+np.asarray(box[:2]),2).tolist()
    return dict(number=ordinal+1,source_box=box,centre=camera(centre),inner=camera(a),outer=camera(b),groove_stations=seams,
                normalized_relief=np.round(relief,3).tolist()),(rgb,a,b,relief,seams)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('photo',type=Path);ap.add_argument('output',type=Path);ap.add_argument('--study',type=Path)
    args=ap.parse_args();methods=runpy.run_path(Path(__file__).with_name('measure-garlands.py'))
    im=ImageOps.exif_transpose(Image.open(args.photo));report=[];sheet=Image.new('RGB',(4*230,375),'#f3f1e8')
    for i,box in enumerate(methods['BOXES']):
        rec,(rgb,a,b,folds,seams)=sampled_fields(im.crop(box),i,box,methods);report.append(rec)
        panel=Image.fromarray(rgb.astype('uint8'));pen=ImageDraw.Draw(panel)
        for line in (a,b):
            pen.line([tuple(k)for k in np.vstack((line,line[:1]))],fill='#5fe9c4',width=1)
        for ind in seams:pen.line((tuple(a[ind]),tuple(b[ind])),fill='#ffe369',width=1)
        panel.thumbnail((225,330));sheet.paste(panel,(230*i,0))
        print(i+1,len(seams),flush=True)
    if args.study:sheet.save(args.study,quality=92)
    output={'photographer':'Antigng','date':'2015-07-20','source':'https://commons.wikimedia.org/wiki/File:%E8%8B%B1%E5%95%86%E4%B8%8A%E6%B5%B7%E7%94%B5%E8%BD%A6%E5%85%AC%E5%8F%B8%E5%A4%A7%E6%A5%BC.jpg','license':'CC BY-SA 4.0','upright_size':[2988,5312],'photo_sha256':hashlib.sha256(args.photo.read_bytes()).hexdigest(),'coordinates':'Upright original pixels, x right and y down; wreaths run left to right in the street photograph. Each inner and outer ring has 256 stations. Their measured separation bounds 15 relief samples. Depth and hidden return remain estimates.','wreaths':report}
    args.output.write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'))+'\n')
if __name__=='__main__':main()
