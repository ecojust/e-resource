"""Measure the lighting-dependent sRGB ranges of the two synthesized surfaces."""
import argparse,json
from pathlib import Path
from PIL import Image
import numpy as np
REGIONS={'weathered timber':[(668,640,681,688),(970,666,984,701),(547,455,616,496)],'grey clay':[(740,288,802,306),(819,315,883,339),(1004,340,1059,355)]}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('commons',type=Path);a.add_argument('out',type=Path);args=a.parse_args();rgb=np.asarray(Image.open(args.commons).convert('RGB'))
    result={key:[dict(xyxy=[x,y,x1,y1],median=np.median(rgb[y:y1,x:x1].reshape(-1,3),axis=0).round(2).tolist(),p10=np.percentile(rgb[y:y1,x:x1].reshape(-1,3),10,axis=0).round(2).tolist(),p90=np.percentile(rgb[y:y1,x:x1].reshape(-1,3),90,axis=0).round(2).tolist())for x,y,x1,y1 in boxes]for key,boxes in REGIONS.items()}
    args.out.write_text(json.dumps(dict(photo='commons-2006',ranges=result,limits='Observed channels include daylight, shading, reflections and weathering. Procedural material samples are original and represent an indirect-light approximation.'),indent=2)+'\n')
