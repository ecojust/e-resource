"""Read native brick-bed peaks and tile-column periods on Fayhoo's garden-front photograph."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

def measure(source):
    digest=sha256(source.read_bytes()).hexdigest()
    assert digest=='e01c70ff00fa37bff3202cf71a1f6e0ea6270a9ac2f2ebc205a78c632ce3eeb4'
    grey=np.asarray(Image.open(source).convert('RGB'),dtype=float).mean(2)
    samples=[]
    for title,(x0,y0,x1,y1),low,high in [
        ('Middle ground pier',(722,954,765,1127),969,1099),
        ('West ground pier',(494,954,526,1123),968,1093),
        ('East upper pier',(737,584,762,741),684,737)]:
        profile=np.median(grey[y0:y1,x0:x1],axis=1)
        smooth=profile-gaussian_filter1d(profile,2.9)
        peaks=find_peaks(smooth,distance=3,prominence=max(1.,np.percentile(smooth,80)*.8))[0]+y0
        selected=peaks[(peaks>=low)&(peaks<=high)]
        pitch=float(np.polyfit(np.arange(len(selected)),selected,1)[0])
        samples.append(dict(pier=title,rectangle=[x0,y0,x1,y1],unobstructed_beds_y=selected.tolist(),pixels_per_course=pitch))
    tile_rows=[]
    for y in (346,351,356,363,376,386,390,398,408,410,416):
        strip=grey[y,610:765];strip-=gaussian_filter1d(strip,5)
        ac=np.correlate(strip,strip,'full')[len(strip)-1:]
        lag=int(np.argmax(ac[8:13])+8)
        tile_rows.append(dict(y=y,range_x=[610,765],native_column_lag_px=lag))
    period=float(np.mean([row['pixels_per_course'] for row in samples]))
    return dict(source='https://commons.wikimedia.org/wiki/File:Shanyinlu_209_Long_Zhuzhai.JPG',sha256=digest,
                patches=samples,mean_native_course_px=period,middle_clear_opening_px=183,
                assumed_course_height_m=.063,illustrative_course_range_m=[.055,.070],
                middle_opening_m_from_nominal=183*.063/period,
                illustrative_opening_range_m=[183*k/period for k in [.055,.070]],model_clear_width=2.38,
                measured_roof_tile_rows=tile_rows,metric_status='Photographic relative scale. Physical brick module and elevations remain unmeasured.')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('photo',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args();args.output.write_text(json.dumps(measure(args.photo),indent=2)+'\n')
