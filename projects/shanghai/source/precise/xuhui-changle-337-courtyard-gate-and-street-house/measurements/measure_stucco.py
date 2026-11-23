"""Measure rather than redistribute upper/lower roughcast and the dark painted leaf from the 2017 original."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

PATCHES={
    'upper warm roughcast':[(2425,1452,2535,1561),(2420,1570,2530,1692),(1985,1480,2092,1595)],
    'pale ground storey':[(1900,2150,2016,2262),(1960,2230,2080,2338),(2428,2185,2535,2286)],
    'green upper frame':[(2136,1474,2153,1500),(2238,1486,2250,1520)],
    'outward lower leaf':[(2152,2210,2252,2294),(2250,2242,2362,2329)],
}
def measure(image):
    raw=image.read_bytes()
    assert hashlib.sha1(raw).hexdigest()=='e2422463ff04d5698e72f5e3834d339e554fec5a'
    im=Image.open(image).convert('RGB');rows={}
    for surface, regions in PATCHES.items():
        samples=[]
        for rect in regions:
            rgb=np.asarray(im.crop(rect),dtype=float)
            y=rgb @ [.2126,.7152,.0722]
            detail=y-gaussian_filter(y,6.,mode='reflect')
            gx,gy=np.gradient(detail);cov=np.cov(np.stack((gx.ravel(),gy.ravel())))
            unit=detail.std()
            decorrelation=[]
            for axis in (0,1):
                shifted=[float((detail*np.roll(detail,n,axis=axis)).mean()/max(unit**2,1e-12)) for n in range(1,10)]
                decorrelation.append(next((n+1 for n,v in enumerate(shifted) if v<.4),None))
            samples.append({'region':rect,'median_srgb':np.median(rgb,axis=(0,1)).round(1).tolist(),
                            'quantiles_luma_10_90':np.quantile(y,[.1,.9]).round(1).tolist(),
                            'high_pass_sd':round(float(unit),3),'gradient_covariance':cov.round(3).tolist(),
                            'lag_to_correlation_below_0_4_px_yx':decorrelation})
        rows[surface]=samples
    return {'author':'Antigng','photo_license':'CC BY-SA 4.0','original_sha256':hashlib.sha256(raw).hexdigest(),'observations':rows,
            'interpretation':'The upper roughcast is more sharply textured than the pale lower storey. Photographic sRGB includes shade and sun. Generated material colour and relief are approximations; no pixels are copied into textures.'}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('photo',type=Path);parser.add_argument('out',type=Path);args=parser.parse_args()
    args.out.write_text(json.dumps(measure(args.photo),ensure_ascii=False,indent=2)+'\n')
