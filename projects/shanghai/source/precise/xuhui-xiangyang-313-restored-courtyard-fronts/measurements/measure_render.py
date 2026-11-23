"""Read the tonal range of uncluttered render samples in both contractor photographs."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from PIL import Image
REGIONS={
 'case1':[(485,57,506,75),(528,88,545,104),(383,86,395,99),(299,112,317,123)],
 'case2':[(119,39,140,62),(155,63,173,82),(229,204,251,218),(505,104,521,118),(516,140,525,151)],
}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('image1',type=Path);p.add_argument('image2',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
 report={}
 for (key,boxes),path in zip(REGIONS.items(),[a.image1,a.image2]):
  image=np.asarray(Image.open(path).convert('RGB'),float)
  samples=[]
  for x,y,r,b in boxes:
   area=image[y:b,x:r];dx=area[:,1:]-area[:,:-1];dy=area[1:]-area[:-1]
   samples.append({'box_xyxy':[x,y,r,b],'median_rgb':np.median(area,axis=(0,1)).tolist(),'std_rgb':np.std(area,axis=(0,1)).round(3).tolist(),'median_absolute_neighbour_change':float(np.median(np.abs(np.r_[dx.reshape(-1),dy.reshape(-1)])))})
  report[key]={'image_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'patches':samples}
 report['interpretation']='Image tone varies with exposure, shade and compression. These values constrain the two pale plaster colours. The measured noise constrains contrast only. Grain size and relief below image resolution are original material estimates.'
 a.out.write_text(json.dumps(report,indent=2)+'\n')
