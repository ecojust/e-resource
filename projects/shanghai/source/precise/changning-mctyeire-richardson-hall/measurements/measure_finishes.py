"""Read representative finish colours from the uncropped lawn and interior photographs."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image
SAMPLES={
 'grey ashlar':('lawn',[(170,245,180,260),(325,291,337,304),(473,285,485,297),(932,352,945,363),(1005,283,1028,296)]),
 'rust red pantile':('lawn',[(497,142,512,152),(645,148,665,160),(742,151,758,157),(856,148,873,156),(430,143,449,151)]),
 'dark oak':('entrance',[(740,823,774,847),(755,908,794,933),(882,849,895,877),(1059,892,1086,923),(1083,803,1108,827)])}
def read(images):
    d={}
    for material,(name,rects) in SAMPLES.items():
        path=images[name]
        with Image.open(path) as im:
            samples=[dict(xyxy=rect,median_srgb=np.median(np.asarray(im.convert('RGB').crop(rect)).reshape(-1,3),axis=0).tolist()) for rect in rects]
        d[material]=dict(source=name,file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),samples=samples)
    return dict(method='Axis-aligned patches in the original published pixels. The procedural finish describes visible tone and grain. Illumination, course dimensions and tile pitch remain estimates.',materials=d)
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('lawn',type=Path);ap.add_argument('entrance',type=Path);a=ap.parse_args()
    (Path(__file__).parent/'finish-readings.json').write_text(json.dumps(read(vars(a)),indent=2)+'\n')
