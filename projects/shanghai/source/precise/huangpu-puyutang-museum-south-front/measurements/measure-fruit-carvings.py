"""Measure fruit outlines and four visible depressions on the archived portal photograph."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter, gaussian_filter1d, map_coordinates


def sample(field, xy):
    return map_coordinates(field, [xy[...,1],xy[...,0]],order=1,mode="nearest")


def measure(photo, survey):
    if hashlib.sha256(photo.read_bytes()).hexdigest()!=survey["source"]["sha256"]:
        raise ValueError("Unexpected source photograph")
    with Image.open(photo) as original:
        x,y=survey["festoon"]["origin_px"]
        image=np.asarray(original.crop((x,y,x+192,y+145)).convert("L"),float)
    luminance=gaussian_filter(image,.58)
    theta=np.arange(24)*2*np.pi/24
    wheel=np.column_stack((np.cos(theta),np.sin(theta)))
    factors=np.linspace(.77,1.24,24)
    settings={7:[83.6,74.4],8:[88.,74.5],10:[98.5,83.6],14:[114.1,86.]}
    shapes=[]
    for i,(x,y,rx,ry) in enumerate(survey["festoon"]["fruit_ellipses"],1):
        c=np.array([x,y])
        radii=np.array([rx,ry])
        # Follow the nearest local edge around each sampled fruit. The weak
        # circular prior guards against a neighbouring berry obscuring a lobe.
        pts=c+factors[None,:,None]*wheel[:,None,:]*radii
        values=sample(luminance,pts)
        contrast=abs(np.gradient(gaussian_filter1d(values,.9,axis=1),factors,axis=1))
        score=contrast-.8*np.maximum(6.,np.median(contrast,axis=1))[:,None]*((factors-1.)/.24)**2
        rim=gaussian_filter1d(factors[np.argmax(score,axis=1)],1.3,mode="wrap")
        item={"number":i,"perimeter_factors":rim.round(4).tolist()}
        if i in settings:
            target=np.array(settings[i])
            offsets=np.linspace(-1.,1.,11)
            test=target+np.stack(np.meshgrid(offsets,offsets),axis=-1)
            value=sample(luminance,test)
            score=value+1.8*np.sum((test-target)**2,axis=-1)
            centre=test[np.unravel_index(np.argmin(score),score.shape)]
            ring=sample(luminance,centre+wheel*1.85)
            contrast=float(np.median(ring)-sample(luminance,centre[None,:])[0])
            if contrast<=1.:raise ValueError(f"No dark depression on fruit {i}: {contrast}")
            item["visible_depression"]={"source_centre_px":centre.round(2).tolist(),
                "radius_px":1.42,"core_to_rim_luminance_difference":round(contrast,2)}
        shapes.append(item)
    return {"photograph_sha256":survey["source"]["sha256"],"angles":"24 angles counterclockwise in mathematical x,y from positive source u, with image v increasing downwards.","shapes":shapes,
            "method":"Local edge search around measured fruit outlines; source pixels and colours are not reproduced. The depth of the four small hollows is an estimate."}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("photo","survey","output"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();record=measure(a.photo,json.loads(a.survey.read_bytes()))
    a.output.write_text(json.dumps(record,ensure_ascii=False,indent=1)+"\n")
    print([(s["number"],s["visible_depression"]) for s in record["shapes"] if "visible_depression" in s])
