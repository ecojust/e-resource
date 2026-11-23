"""Record small colour samples from the institutional entrance photograph and the plaque detail."""
import argparse,json,hashlib
from pathlib import Path
import numpy as np
from PIL import Image
MATERIALS={'grey-pink aggregate plaster':[(463,298,480,324),(785,299,800,321),(822,351,835,369)],'worn pale cement':[(654,639,687,651),(408,645,435,652),(517,644,542,652)],'black enamel gate iron':[(68,410,72,418),(24,430,27,438),(40,550,53,558)],'heritage plaque stone':[(538,416,547,428),(602,411,611,420),(541,463,551,469)]}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('photo',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
 with Image.open(a.photo)as im:rgb=np.array(im.convert('RGB').resize((1000,701),Image.Resampling.LANCZOS))
 result={}
 for name,rects in MATERIALS.items():
  patches=[rgb[y:b,x:r].reshape(-1,3)for x,y,r,b in rects];values=np.vstack(patches)
  result[name]={'boxes':rects,'individual_median_srgb':[np.median(p,axis=0).round().astype(int).tolist()for p in patches],'median_srgb':np.median(values,axis=0).round().astype(int).tolist()}
 a.output.write_text(json.dumps({'photo_sha256':hashlib.sha256(a.photo.read_bytes()).hexdigest(),'measurement_frame':[1000,701],'image':'https://cn.storage.shmedia.tech/9822b8b1f7a44038af885e39f3eb36d1.jpeg','materials':result},indent=2)+'\n')
