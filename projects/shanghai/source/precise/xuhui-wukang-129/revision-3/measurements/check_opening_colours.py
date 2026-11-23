"""Compare colour and relative luminance on fixed areas of two Commons photo stations.

The photographs are read locally. Reports contain only measurements, source
credits and licence references. Delivered model views contain no photo pixels.
"""
import argparse
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image

HERE=Path(__file__).absolute().parent
# 2017 marks are visually selected on the 1328 x 747 working image.
# Coordinates below are area edges; no centre correction applies to box edges.
MARKS={
    '2017':{'door paint':('gate',(774,497,790,530)),'gate grey stone':('gate',(739,491,743,550)),
            'pale wall':('gate',(866,482,874,537)),'dark aperture':('balcony',(1157,189,1176,220)),
            'fanlight glass':('balcony',(1179,113,1189,121))},
    '2026':{'door paint':('gate',(1021,823,1041,863)),'gate grey stone':('gate',(976,809,982,890)),
            'pale wall':('gate',(1121,818,1141,879)),'dark aperture':('balcony',(1413,500,1437,531)),
            'fanlight glass':('balcony',(1434,438,1441,445))}
}

def measures(im,box):
    a=np.array(im.crop(tuple(round(k) for k in box)).convert('RGB'),dtype=float)
    linear=a/255
    linear=np.where(linear<=.04045,linear/12.92,((linear+.055)/1.055)**2.4)
    val=linear@np.array([.2126,.7152,.0722])
    rgb=np.median(a.reshape(-1,3),axis=0)
    return {'pixels':a.shape[0]*a.shape[1],'median_srgb_255':rgb.tolist(),
            'median_linear_luminance':float(np.median(val)),'linear_luminance_p10_p90':np.quantile(val,[.10,.90]).tolist(),
            'median_red_minus_green':float(rgb[0]-rgb[1])}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('renders',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('--references',type=Path,default=HERE.parents[1]/'references')
    args=parser.parse_args()
    obs=json.loads((HERE/'opening-observations.json').read_text())
    report={'camera_sha256':hashlib.sha256((HERE/'two-photo-cameras.json').read_bytes()).hexdigest(),'limits':'Unprofiled source JPEGs and estimated sunlight. Exposure, white balance, weather, vegetation shadows and painting history are uncontrolled. Fixed-image median RGB values describe appearance under each recording, not intrinsic paint or stone reflectance.','views':{}}
    for year,marks in MARKS.items():
        f=next(args.references.glob(year+'*.jpg'))
        assert hashlib.sha256(f.read_bytes()).hexdigest()==obs['rights'][year]['original_jpeg_sha256']
        im=Image.open(f)
        data={'source':obs['rights'][year],'areas':{}}
        for mark,(part,box) in marks.items():
            box=np.array(box)*(4 if year=='2017' else 1)
            results={'source_original':measures(im,box),'native_pixel_box':box.tolist()}
            for role in ('v2','v3'):
                receipt=args.renders/(role+'-registered-renders.json')
                if not receipt.is_file():continue
                frame=json.loads(receipt.read_text())['frames'][year+'-'+part]
                sx,sy,ex,ey=frame['source_native_crop_xyxy']
                target=Image.open(args.renders/frame['file'])
                scale=np.array([target.width/(ex-sx),target.height/(ey-sy)]*2)
                mapped=(box-[sx,sy,sx,sy])*scale
                results[role]=measures(target,mapped)
            data['areas'][mark]=results
        report['views'][year]=data
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    main()
