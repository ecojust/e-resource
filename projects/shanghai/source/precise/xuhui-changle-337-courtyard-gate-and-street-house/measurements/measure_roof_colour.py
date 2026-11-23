"""Measure identical pixel patches in exterior photographs and registered model renders."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
# Coordinates and square half widths are in original pixels. The four
# eastern-wing tile samples receive substantially more sunlight than the main hip.
SAMPLES = {
    '2017': {
        'main tiles': [(2070,1212,20),(2260,1157,20),(2450,1037,20),(2120,1183,20)],
        'wing tiles': [(3710,1070,11),(4340,930,11),(4640,997,11),(4660,1006,11)],
        'ridge cap': [(1948,1154,9)],
        'fascia': [(2255,1266,8)],
        'main wall': [(2090,1465,24),(2788,1380,18)],
        'wing wall': [(4800,1197,18),(4880,1180,18)],
    },
    '2015-12-front': {
        'main tiles': [(227,316,5),(303,307,5),(374,287,5)],
        'wing tiles': [(847,317,5),(920,297,4)],
        'wing wall': [(770,383,6),(975,399,6)],
        'fascia': [(954,344,4)],
    },
}

def patch(image,x,y,radius,scale=1):
    x,y=round(x*scale),round(y*scale)
    r=max(1,round(radius*scale))
    sample=image[y-r:y+r+1,x-r:x+r+1,:].reshape(-1,3)
    return np.rint(np.median(sample,axis=0)).astype(int).tolist()

def srgb_luminance(rgb):
    rgb=np.asarray(rgb)/255.
    linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
    return float(linear@np.array([.2126,.7152,.0722]))

def measure(name,source,registered):
    def load(path):
        return np.asarray(Image.open(path).convert('RGB'))
    photo,render=load(source),load(registered)
    scale=render.shape[1]/photo.shape[1]
    groups={}
    for group,samples in SAMPLES[name].items():
        rows=[]
        for x,y,r in samples:
            observed=patch(photo,x,y,r)
            painted=patch(render,x,y,r,scale)
            rows.append({'pixel':[x,y],'radius':r,'photo_srgb':observed,'render_srgb':painted,
                         'photo_luminance':srgb_luminance(observed),'render_luminance':srgb_luminance(painted)})
        groups[group]=rows
    def ratio(roof,wall,channel):
        key=channel+'_luminance'
        return round(float(np.median([r[key]for r in groups[roof]])/np.median([r[key]for r in groups[wall]])),4)
    rel={}
    for prefix in ('main','wing'):
        wall=prefix+' wall'
        if wall in groups:
            rel[prefix]={channel:ratio(prefix+' tiles',wall,channel)for channel in ('photo','render')}
    return {'photo_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
            'render_sha256':hashlib.sha256(registered.read_bytes()).hexdigest(),'samples':groups,
            'relative_luminance_to_same_wing_wall':rel}

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('photo_2017',type=Path)
    cli.add_argument('photo_2015',type=Path)
    cli.add_argument('render_directory',type=Path)
    cli.add_argument('output',type=Path)
    a=cli.parse_args()
    records={k:measure(k,p,a.render_directory/(k+'-model.jpg'))for k,p in [('2017',a.photo_2017),('2015-12-front',a.photo_2015)]}
    data={'space':'Observed and rendered medians are sRGB bytes. Relative luminance uses the IEC sRGB transfer function before linear weighting.',
          'limits':'The central 2017 hip is under a tree canopy. The wing tiles include direct highlights, while the diffuse registered renderer has no foliage, atmospheric exposure, sun or camera tone curve. These patches constrain the palette; they are not an intrinsic reflectance measurement.',
          'views':records}
    a.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
