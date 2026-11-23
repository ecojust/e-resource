"""Sample small wall, corner-brick and roof fields. Only numerical samples are saved."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
from PIL import Image
H=Path(__file__).absolute().parent
samples={'coarse grey-brown pebble dash':{'court':[(62,95),(64,142),(47,146)],'back':[(399,358),(374,333),(394,206)]},'warm red facing brick':{'court':[(77,108),(76,143),(76,168)],'back':[(451,325),(448,237),(452,217)]},'terracotta roof':{'court':[(136,81),(157,75),(57,42)],'back':[(424,58),(391,57),(363,65)]}}
def measure(a,b):
    data={n:np.array(Image.open(m).convert('RGB'))for n,m in [('court',a),('back',b)]};out={}
    for name,parts in samples.items():
        med=[]
        for station,points in parts.items():
            for x,y in points:med.append(np.median(data[station][y-1:y+2,x-1:x+2],axis=(0,1)))
        out[name]={'sample_centres_original_pixels':parts,'sample_patch_radius':1,'patch_medians':np.array(med).astype(int).tolist(),'median_srgb':np.median(med,axis=0).astype(int).tolist()}
    return dict(source_signatures=[hashlib.sha256(p.read_bytes()).hexdigest()for p in [a,b]],materials=out,method='Native 3 by 3 medians, then equal weight for six small patches. Cloudy north and sunlit court colours differ. New procedural texels use numerical medians and no photograph fragments.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('court',type=Path);p.add_argument('back',type=Path);a=p.parse_args();(H/'finish-readings.json').write_text(json.dumps(measure(a.court,a.back),indent=2)+'\n')
