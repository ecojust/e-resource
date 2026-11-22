"""Measure rail widths directly from the two source photographs (not included in the repository)."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d

HERE = Path(__file__).resolve().parent
NATIVE = json.loads((HERE/'terrace-source-observations.json').read_text())['sources']
# Hand-traced endpoints of the four visible rail centres at quarter scale.
SECTIONS = {
    'yan05': [('southwest bevel',[394,502],[41,57,73,89],[35,51,67,82]),
              ('front edge',[503,616],[36,52,67,82],[125,139,151,165])],
    'yan07': [('front edge',[187,225],[218,228,239,246],[190,201,212,220]),
              ('southeast bevel',[226,285],[190,201,212,223],[193,205,217,231])]
}


def measure(tag, filename):
    with filename.open('rb') as file:
        if hashlib.file_digest(file,'sha256').hexdigest()!=next(row['sha256'] for row in NATIVE if row['tag']==tag):
            raise ValueError('Expected the full-size, bordered original of '+tag)
    image=np.asarray(Image.open(filename).convert('L'))
    controls,omissions=[],[]
    for side,(xa,xb),left,right in SECTIONS[tag]:
        for level,(y0,y1) in enumerate(zip(left,right)):
            for frac in (.17,.31,.44,.59,.74,.84):
                x=round(4*(xa+(xb-xa)*frac))
                predicted=int(4*(y0+(y1-y0)*frac))
                intensity=gaussian_filter1d(np.median(image[:,x-1:x+2],axis=1),1.)
                window=np.arange(predicted-16,predicted+17)
                centre=int(window[np.argmin(intensity[window])])
                side_a=intensity[centre-18:centre-4].max()
                side_b=intensity[centre+5:centre+19].max()
                contrast=float(min(side_a,side_b)-intensity[centre])
                omitted=[side,level,x,predicted,round(contrast,1)]
                if contrast<36 or abs(centre-predicted)>14:
                    omissions.append(omitted)
                    continue
                half=intensity[centre]+contrast*.5
                a=b=centre
                while a>centre-23 and intensity[a]<half:
                    a-=1
                while b<centre+23 and intensity[b]<half:
                    b+=1
                if not 3 <= b-a <=31:
                    omissions.append(omitted)
                    continue
                controls.append(dict(side=side,level=level,uv=[x,round((a+b)/2,1)],
                                     observed_dark_band_y=[a,b],contrast_grey_levels=round(contrast,1)))
    return dict(controls=controls,uninformative_or_overlapping_samples=omissions)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('yan05',type=Path)
    ap.add_argument('yan07',type=Path)
    ap.add_argument('output',type=Path)
    a=ap.parse_args()
    results={tag:measure(tag,getattr(a,tag)) for tag in SECTIONS}
    a.output.write_text(json.dumps(results,ensure_ascii=False,indent=1)+'\n')
