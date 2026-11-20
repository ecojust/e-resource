"""Count observable image changes above the pre-existing plinths and on the same central steps."""
from pathlib import Path
from PIL import Image
import numpy as np,hashlib,json
from argparse import ArgumentParser
p=ArgumentParser(description=__doc__);p.add_argument('before',type=Path);p.add_argument('after',type=Path);p.add_argument('out',type=Path);args=p.parse_args()
files=[args.before,args.after]
squares={'east_plinth_and_lion':[350,278,425,407],'west_plinth_and_lion':[673,278,748,407],'center_stair_treads':[463,410,639,468]}
old,new=[np.asarray(Image.open(f).convert('RGB'),dtype=np.int16)for f in files];assert old.shape==new.shape==(744,1100,3)
diff=np.max(np.abs(new-old),axis=2)
def measure(bounds):
 x1,y1,x2,y2=bounds;region=diff[y1:y2,x1:x2];mask=region>8
 return {'xyxy_half_open':bounds,'pixels':int(region.size),'at_least_9_channel_difference':int(mask.sum()),'median_largest_channel_delta':int(np.median(region)),'max_channel_delta':int(region.max())}
out={'source':'1100 × 744 actual map north-entrance paired close camera. Crops are centered on the original plinths or the central steps.','before_sha256':hashlib.file_digest(args.before.open('rb'),'sha256').hexdigest(),'after_sha256':hashlib.file_digest(args.after.open('rb'),'sha256').hexdigest(),'regions':{k:measure(v)for k,v in squares.items()}}
args.out.write_text(json.dumps(out,indent=2)+'\n');print(out['regions'])
