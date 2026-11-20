"""Map the four photographed column axes and cornice to a metric street front."""
from itertools import product
from pathlib import Path
import json,math
import numpy as np
from scipy.optimize import least_squares

SOURCE=Path(__file__).resolve().parent.parent
source=json.loads((SOURCE/'footprint-review.json').read_bytes())
width=source['local_frame']['street_width_m']
axes=(np.array([183.,255.,330.,403.])-289.5)*width/475
bottoms=np.array([[193,670],[310,671],[404,669],[473,666]])
capitals=np.array([[220,293],[313,332],[389,365],[453,395]])

def fit(focal,eye,offset):
    principal=np.array([275.,414.])
    def screen(x,z,p):
        cx,d,bearing,pitch,height=p;a=math.radians(bearing);v=math.radians(pitch)
        h=z-eye;dist=(x-cx)*math.sin(a)+d*math.cos(a);left=(x-cx)*math.cos(a)-d*math.sin(a)
        return principal+focal*np.asarray([left,-h*math.cos(v)+dist*math.sin(v)])/(dist*math.cos(v)+h*math.sin(v))
    def residual(p):
        low=[screen(x,.74,p)-q-[0,offset]for x,q in zip(axes,bottoms)]
        high=[screen(x,p[4],p)-q for x,q in zip(axes,capitals)]
        return np.ravel(low+high)
    q=least_squares(residual,[-8,12,18,26,11],bounds=([-50,2,-5,0,5],[10,40,80,70,24]),loss='soft_l1')
    cx,d,bearing,pitch,h=q.x;a=math.radians(bearing);v=math.radians(pitch)
    def elevation(x,y,setback=0):
        depth=(x-cx)*math.sin(a)+(d+setback)*math.cos(a);y_ratio=(414-y)/focal
        return eye+depth*(y_ratio*math.cos(v)+math.sin(v))/(math.cos(v)-y_ratio*math.sin(v))
    return {'capital_m':round(h,3),'rms_pixels':round(float(np.sqrt(np.square(residual(q.x)).mean())),3),
            'street_cornice_from_left_and_right_m':[round(elevation(x,y),3)for x,y in [(-width/2,78),(width/2,344)]],
            'upper_roof_from_left_and_right_without_setback_m':[round(elevation(x,y),3)for x,y in [(-width/2,13),(width/2,284)]]}

if __name__=='__main__':
    trials=[fit(*v)for v in product([540.,582.],[1.45,1.82],[-4.,4.])]
    result={'photo':'2015-01-02 Livelikerw, Former Mitsubishi Bank Building Shanghai.JPG','original_pixels':[3264,4912],
            'inspection_pixels':[550,828],'camera':'Sony NEX-3N; 16 mm, EXIF equivalent 24 mm. Assume image center principal point.',
            'cross_image_scale':'Web article street elevation bank2025-10, crop original x=560…796, y=151…306 scaled 2.5×. Facade edges x=52,527; column axes x=183,255,330,403. Fitted to frozen 28.386 m street edge.',
            'column_bases_at_assumed_074m_px':bottoms.tolist(),'column_capitals_px':capitals.tolist(),'nominal':fit(564.,1.64,0.),
            'alternative_cameras':trials,'adopted_model_m':{'underside_of_column_abacus':12.45,'cornice_top':17.15,'high_front_wall':20.71},
            'limits':'The photographed front is oblique and stepped. Eye height, hidden foundation corners and unknown alignment make the separate heights approximate, especially roof endpoints. No surveyed section or roof depth was available.'}
    (SOURCE/'elevation-estimate.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
