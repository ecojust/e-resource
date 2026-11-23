"""Recover the observed eave tile repeat directly from two source photographs in native pixels."""
import argparse,json
import numpy as np
from pathlib import Path
from PIL import Image
from scipy.ndimage import gaussian_filter1d

def measure(image,span,rows):
    p=np.asarray(Image.open(image).convert('L'),float)
    values=[]
    for row in rows:
        line=p[row-1:row+2,span[0]:span[1]].mean(axis=0)
        contrast=line-gaussian_filter1d(line,10)
        fft=abs(np.fft.rfft(np.hanning(len(line))*contrast));freq=np.fft.rfftfreq(len(line))
        region=np.flatnonzero((freq>1/32)&(freq<1/3.5));best=region[np.argmax(fft[region])]
        values.append(dict(row=row,native_period_px=round(1/freq[best],4)))
    return dict(interval_native=list(span),readings=values)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('school_image',type=Path);p.add_argument('reverse_image',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
    a.out.write_text(json.dumps(dict(school_front=measure(a.school_image,(133,293),(64,68,72)),reverse=measure(a.reverse_image,(235,601),(176,180,184)),eave_widths_native_px=[333,720],adopted_number_of_intervals=49,limits='The horizontal bands cover the relatively level middle of each roof. Tree cover and uplift make a definitive end-to-end row count impractical.'),indent=2)+'\n')
