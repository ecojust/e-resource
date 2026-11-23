"""Read colour medians on the architectural rendering used for the 2014 repair proposal."""
from pathlib import Path
import json,hashlib,argparse
from PIL import Image
import numpy as np

PATCHES={'walls':[(160,212,173,223),(185,216,195,225),(333,211,341,221),(211,214,220,224)],'roof':[(149,149,155,156),(259,135,264,142),(343,143,352,148),(167,131,175,137)],'lime':[(175,187,181,196),(220,187,225,195),(334,192,336,195)],'oak':[(144,191,148,196),(238,214,240,222),(321,212,324,220)]}
def read(p):
    im=np.array(Image.open(p).convert('RGB'))
    rows={}
    for group,patches in PATCHES.items():
        rows[group]=[]
        for box in patches:
            l,t,r,b=box;v=im[t:b,l:r]
            rows[group].append(dict(box=box,median_srgb=np.median(v.reshape(-1,3),axis=0).tolist(),interquartile=np.percentile(v.reshape(-1,3),[25,75],axis=0).tolist()))
    return {'source_page':'https://www.jianweigroup.com/site/10/category0051/b1216655955211e89cd6408d5c6f7eaa.html','source_image':'https://www.jianweigroup.com/userfiles/image/20170807/80646f556ca29657bdcaf3a7a8b7f34a24c46af5.jpg','size':[im.shape[1],im.shape[0]],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'kind':'Colour proposal, not a dated post-construction survey. The 1937 print independently checks geometry and tonal contrast.','readings':rows}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('image',type=Path);parser.add_argument('output',type=Path)
    a=parser.parse_args();a.output.write_text(json.dumps(read(a.image),indent=2)+'\n')
