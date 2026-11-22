"""Measure offsets along the outer rakes in Antigng's EXIF-upright full-resolution photograph."""
import argparse, hashlib, json
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
from scipy.ndimage import map_coordinates,gaussian_filter

def measure(file):
    upright=ImageOps.exif_transpose(Image.open(file))
    assert upright.size==(2988,5312)
    # Only the local survey crop is converted to floating point.
    x0,y0=1200,1490
    crop=np.asarray(upright.crop((x0,y0,2170,2250)).convert('L'),np.float32)
    gray=gaussian_filter(crop,1.0)
    # Independent observer's ten image landmarks. Right eave points identify
    # the rake/run-out junction, rather than the end of the level return.
    bays={'left':[(1313,2151),(1470,1885),(1644,1953),(1342,2173),(1644,1989)],
          'right':[(1667,1942),(1857,1642),(2066,1702),(1697,1956),(2072,1739)]}
    station=np.linspace(.10,.9,11);steps=np.linspace(-7,7,57);out=[]
    for bay,anchors in bays.items():
        for edge,(a,b) in enumerate(zip(anchors[:2],anchors[1:3])):
            a,b=np.array(a),np.array(b);direc=(b-a)/np.linalg.norm(b-a);n=np.array([-direc[1],direc[0]])
            for si,t in enumerate(station):
                start=a+t*(b-a);pos=start+steps[:,None]*n
                val=map_coordinates(gray,[pos[:,1]-y0,pos[:,0]-x0],order=1,mode='nearest')
                grad=np.gradient(val,steps);i=int(np.argmax(abs(grad)))
                out.append(dict(bay=bay,rake=edge,station=si+1,xy=pos[i].round(3).tolist(),normal=n.round(8).tolist(),
                                offset_px=round(float(steps[i]),3),contrast_per_px=round(float(abs(grad[i])),3),
                                accepted=bool(1<i<len(steps)-2 and abs(grad[i])>=3.)))
    return dict(photo_sha256=hashlib.sha256(file.read_bytes()).hexdigest(),photo_author='Antigng',exif_date='2015-07-20 15:16:42',upright_pixels=list(upright.size),reference_anchors=bays,held_out_edge_stations=out,accepted=sum(r['accepted'] for r in out))
if __name__=='__main__':
    cli=argparse.ArgumentParser();cli.add_argument('photograph',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();r=measure(args.photograph);assert r['accepted']>=28
    args.output.write_text(json.dumps(r,indent=2)+'\n');print(r['accepted'])
