"""Extract aggregate colour statistics and course spacings from the three public article frames."""
from pathlib import Path
import argparse, json
from hashlib import file_digest
import numpy as np
from scipy.signal import find_peaks
from PIL import Image
PATCHES={'gao-01.jpg':[(341,167,365,207)],
         'gao-04.jpg':[(596,304,635,403)],
         'gao-09.jpg':[(360,239,405,359),(552,254,600,351),(361,45,406,145)]}
def measure(directory):
    result={}
    for name,patches in PATCHES.items():
        p=directory/name
        with p.open('rb')as f:sig=file_digest(f,'sha256').hexdigest()
        a=np.asarray(Image.open(p).convert('RGB'))
        rows=[]
        for left,top,right,bottom in patches:
            t=a[top:bottom,left:right]
            v=np.median(t.mean(axis=2),axis=1)
            peaks=find_peaks(v,distance=2,prominence=3)[0]
            q=np.percentile(t.reshape(-1,3),[15,35,55,75,90],axis=0)
            rows.append(dict(half_open_rectangle=[left,top,right,bottom],rgb_percentile_15_35_55_75_90=np.round(q,1).tolist(),
                             light_course_edges_y=(top+peaks).tolist(),mean_edge_separation_px=round(float(np.diff(peaks).mean()),3)))
        result[name]=dict(sha256=sig,width=a.shape[1],height=a.shape[0],patches=rows)
    return dict(sources=result,finish='The neutral frontal exposures 01 and 04 show grey-brown face brick and lighter mortar. Image 09 has warm direct light. The original tile takes the midtones from 01 and 04 and models the stronger mortar contrast resolved in 09.')
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('originals',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.write_text(json.dumps(measure(args.originals),ensure_ascii=False,indent=2)+'\n')
