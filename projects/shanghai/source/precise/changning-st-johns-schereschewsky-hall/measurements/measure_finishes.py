"""Read masonry, roof and joinery tones from small unoccluded regions of the two registered views."""
from pathlib import Path
import argparse
import json
import numpy as np
from PIL import Image
WINDOWS={
 'blue-grey facing brick':{'metromod-00':[(427,270,448,301),(545,265,570,300),(428,158,451,225)],'newspaper-03':[(468,200,491,216),(605,167,619,191)]},
 'warm red brick dressings':{'metromod-00':[(455,320,493,325),(584,462,616,469),(689,478,715,484)],'newspaper-03':[(453,600,460,608),(462,621,468,628),(859,526,865,532)]},
 'grey butterfly tile':{'metromod-00':[(302,310,349,329),(680,299,735,327),(390,309,415,328)]},
 'painted red-brown timber':{'metromod-00':[(296,565,312,569),(691,561,706,566)]}}
def sample(path,window):
 im=Image.open(path).convert('RGB');roi=np.asarray(im.crop(window));lo,mid,hi=np.quantile(roi.reshape(-1,3),[.15,.5,.85],axis=0)
 return dict(native_xyxy=window,median_srgb=mid.tolist(),quantile15=lo.round(1).tolist(),quantile85=hi.round(1).tolist())
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('photos',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
 d={m:{k:[sample(a.photos/(k+'.jpg'),v)for v in spots]for k,spots in stations.items()}for m,stations in WINDOWS.items()}
 a.out.write_text(json.dumps(dict(method='Median camera sRGB in original pixel coordinates on the same-size working images. The 2004 courtyard gives the body colour. Both exposure and white balance contribute to differences between views.',materials=d),ensure_ascii=False,indent=2)+'\n')
