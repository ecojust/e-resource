"""Measure running courses on the transmitted 2017 source photograph."""
from pathlib import Path
import argparse,json,sys,hashlib
import numpy as np
from scipy.ndimage import gaussian_filter1d,map_coordinates
from scipy.signal import find_peaks
from PIL import Image
here=Path(__file__).resolve().parent
sys.path.insert(0,str(here.parent/'source'))
from photo_plane import position,pixel,original

# Strips across clear masonry areas only, omitting drying rails and hanging fabric.
STRIPS={'grey_under_window':[(301,845,931),(319,843,932),(347,838,929),(367,839,928),(394,847,926),(422,842,928),(447,830,929),(479,830,927)],
'lower_pier_red':[(572,506,750),(591,467,707),(735,603,801),(768,697,821)],
'upper_pier_red':[(521,90,184),(568,144,210),(621,67,137)],
'upper_grey_spandrel':[(309,286,333),(332,283,326),(357,282,317),(380,276,309)]}
def measure(image):
    source=Image.open(image)
    results={}
    for group,profiles in STRIPS.items():
        output=[]
        for u,top,bottom in profiles:
            # Use the medoid luminance along a strip narrower than a brick.
            x,y=original(u,top);_,end=original(u,bottom)
            crop=source.crop((int(x)-10,int(y),int(x)+11,int(end)))
            a=np.median(np.asarray(crop.convert('L')),axis=1).astype(float)
            # Lime joints show as bright peaks set between darker brick faces.
            signal=gaussian_filter1d(a,1.15)-gaussian_filter1d(a,12)
            peaks,_=find_peaks(signal,distance=12,prominence=max(4.,.13*np.ptp(signal)))
            z=[round(float(position(x,y+i)[2]),5) for i in peaks]
            output.append({'local_profile':[u,top,bottom],'mortar_centres_source_px':[[x,y+int(i)] for i in peaks],'planes_z_m':z})
        dist=[a-b for r in output for a,b in zip(r['planes_z_m'],r['planes_z_m'][1:]) if .035<a-b<.13]
        results[group]={'profiles':output,'median_observed_spacing_m':round(float(np.median(dist)),5),'interval_count':len(dist)}
    return {'source_sha256':hashlib.sha256(Path(image).read_bytes()).hexdigest(),'local_pixel_to_source':'u = 2630 + 3*local_x, v = 3*local_y','groups':results}
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('image',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    args.output.write_text(json.dumps(measure(args.image),ensure_ascii=False,indent=2)+'\n')
