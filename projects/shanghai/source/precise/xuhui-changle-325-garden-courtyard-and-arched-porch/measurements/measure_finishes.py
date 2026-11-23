"""Sample unobstructed roughcast, stair risers and carved stone in the 2015 courtyard photograph."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter
from measure_porch import HASH,SOURCE
PATCHES={'roughcast':[(1072,1092,1179,1168),(1438,1175,1542,1230),(1614,1040,1706,1146)],
         'stair-stone':[(541,1025,600,1036),(605,946,669,958),(638,988,707,996),(487,1066,548,1076)],
         'rail-stone':[(361,933,385,969),(827,921,840,957),(457,812,469,838)]}
def sample(path):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=HASH:raise ValueError('Original Fayhoo photograph required.')
    im=Image.open(path);result={}
    for name,patches in PATCHES.items():
        readings=[]
        for r in patches:
            rgb=np.asarray(im.crop(r).convert('RGB'),float);grey=rgb@np.array([.299,.587,.114])
            high=grey-gaussian_filter(grey,2)
            readings.append({'xyxy':r,'median_srgb':np.rint(np.median(rgb,axis=(0,1))).astype(int).tolist(),
                             'fine_contrast_rms_on_255':round(float(np.sqrt((high**2).mean())),2)})
        result[name]=readings
    return dict(source=SOURCE,sha256=HASH,readings=result)
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('image',type=Path);cli.add_argument('output',type=Path)
    args=cli.parse_args();r=sample(args.image);args.output.write_text(json.dumps(r,indent=2)+'\n');print(r['readings'])
