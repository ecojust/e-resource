"""Read native colour patches from the numbered photograph and document their variability."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
WINDOWS={'coarse grey-brown pebble dash':[(555,309),(541,298),(569,290),(567,122),(577,130)],'warm red facing brick':[(460,323),(627,291),(621,309),(679,340),(689,253)],'pale precast cement':[(506,350),(539,349),(539,399),(558,191)],'terracotta roof':[(419,192),(431,192),(443,187),(429,203)]}
def sample(photo):
    im=np.array(Image.open(photo).convert('RGB'));out={}
    for name,samples in WINDOWS.items():
        patches=[im[y-2:y+3,x-2:x+3,:].reshape(-1,3)for x,y in samples];colors=np.concatenate(patches)
        out[name]=dict(centers=samples,patch_radius_pixels=2,median_srgb=np.median(colors,axis=0).round().tolist(),interquartile_srgb=np.quantile(colors,[.25,.75],axis=0).round().tolist())
    return dict(photo_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),pixel_frame=[780,520],materials=out,limitations='Sunlit and shaded surfaces have different colours. The measurements seed procedurally drawn tileable finishes without retaining any photographic pixels.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('photo',type=Path);p.add_argument('output',type=Path);a=p.parse_args();a.output.write_text(json.dumps(sample(a.photo),ensure_ascii=False,indent=2)+'\n')
