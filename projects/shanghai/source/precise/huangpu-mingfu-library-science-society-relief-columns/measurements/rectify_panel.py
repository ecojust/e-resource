"""Rectify an externally supplied image using the four published control points."""
from pathlib import Path
import argparse,hashlib,json
import numpy as np
from PIL import Image

def rectify(source,output):
    reference=json.loads(Path(__file__).with_name('medallion-rectangle.json').read_bytes())
    with source.open('rb')as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if digest!=reference['sha256']:raise ValueError('Source differs from the cited photograph')
    corners=reference['corner_pixels_clockwise'];size=reference['rectified_px']
    system=[];target=[]
    for (x,y),(u,v) in zip([(0,0),(size,0),(size,size),(0,size)],corners):
        system.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        target.extend((u,v))
    coefficients=np.linalg.solve(np.asarray(system),np.asarray(target))
    assert np.allclose(coefficients,reference['inverse_projection'],rtol=1e-9,atol=1e-10)
    panel=Image.open(source).transform((size,size),Image.Transform.PERSPECTIVE,coefficients,resample=Image.Resampling.BICUBIC)
    panel.save(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('reference_photo',type=Path);p.add_argument('output',type=Path)
    args=p.parse_args();rectify(args.reference_photo,args.output)
