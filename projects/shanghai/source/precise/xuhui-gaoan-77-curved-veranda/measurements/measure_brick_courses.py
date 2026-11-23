"""Extract repeated bed-joint centres on plate 37 and estimate the timber spacing conditionally."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
HERE=Path(__file__).resolve().parent
def estimate(original):
    fit=json.loads((HERE/'south-window-and-gallery-fit.json').read_text())
    source=next(r for r in json.loads((HERE/'original-image-metadata.json').read_text())['originals'] if r['plate']==37)
    assert hashlib.sha256(original.read_bytes()).hexdigest()==source['sha256']
    im=Image.open(original);scale=im.width/690
    camera=np.asarray(fit['cameras']['sina-37']['projection']);inv=np.linalg.inv(camera[:,:3]);eye=-inv@camera[:,3]
    def unit_z(x,y):
        line=inv@[x,y,1.];return float((eye+line*(-eye[1])/line[1])[2])
    rows=[]
    for x in [207,208]:
        sx=round(x*scale);start=round(247.8*scale);end=round(287.65*scale)
        pixels=np.asarray(im.crop((sx-4,start,sx+5,end))).astype(float)
        red=(pixels[:,:,0]-pixels[:,:,2]).mean(axis=1)
        cleaned=gaussian_filter1d(red,.75)-gaussian_filter1d(red,3*scale)
        hits=find_peaks(-cleaned,distance=round(1.35*scale),prominence=4.)[0]
        y=(hits+start)/scale
        intervals=len(y)-1
        if intervals<16 or np.max(np.diff(y))>2.45:raise ValueError('Incomplete course sequence')
        units=unit_z(x,float(y[0]))-unit_z(x,float(y[-1]))
        rows.append({'x_reduced':x,'bed_centres_original_y':(hits+start).tolist(),'courses':intervals,'height_in_post_spacing_units':units,'conditional_post_span_m_at_65_5_mm':intervals*.0655/units})
    values=[r['conditional_post_span_m_at_65_5_mm'] for r in rows]
    return {'photo':source,'working_width':690,'prior_course_m':[.063,.068],'course_centre_m':.0655,'location':'Brick panel between the western narrow sash and the central double sash of the south elevation. Two neighbouring scans follow pale mortar bed centres in the original full-resolution 2018 photograph.','rows':rows,'conditional_mean_span_m':float(np.mean(values)),'course_only_range_m':[min(values)*.063/.0655,max(values)*.068/.0655]}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('original',type=Path);p.add_argument('output',type=Path);args=p.parse_args();r=estimate(args.original);args.output.write_text(json.dumps(r,indent=2)+'\n');print(r['conditional_mean_span_m'],r['course_only_range_m'])
