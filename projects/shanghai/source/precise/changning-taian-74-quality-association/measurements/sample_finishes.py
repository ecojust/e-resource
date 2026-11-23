"""Read unoccluded original colour patches in the 2020 street-front survey."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
import numpy as np
PATCHES={'scored pale render':[[316,187,327,194],[324,236,335,244],[431,215,441,224]],
         'off-white cast moulding':[[306,142,311,155],[250,238,254,251],[408,218,410,226]],
         'blue-black canopy metal':[[320,289,326,292],[411,292,421,295],[351,286,355,288]],
         'warm red entrance tile':[[335,426,348,429],[372,430,382,434],[464,435,471,438]]}
if __name__=='__main__':
    c=argparse.ArgumentParser(description=__doc__);c.add_argument('photo',type=Path);c.add_argument('out',type=Path);a=c.parse_args()
    rgb=np.array(Image.open(a.photo).convert('RGB'))
    data={}
    for k,r in PATCHES.items():
        sample=np.concatenate([rgb[t:b,l:h].reshape(-1,3)for l,t,h,b in r])
        data[k]=dict(rectangles=r,samples=len(sample),median_srgb=np.rint(np.median(sample,axis=0)).astype(int).tolist(),percentiles=np.rint(np.percentile(sample,[10,90],axis=0)).astype(int).tolist())
    a.out.write_text(json.dumps(dict(source='street-front-2020',sha256=hashlib.sha256(a.photo.read_bytes()).hexdigest(),materials=data),ensure_ascii=False,indent=2)+'\n')
