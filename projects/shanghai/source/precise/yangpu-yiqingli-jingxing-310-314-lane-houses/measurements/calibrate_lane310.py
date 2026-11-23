from pathlib import Path
import json
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
import argparse, hashlib
cli=argparse.ArgumentParser(description='Calibrate the 2015 lane photograph using the original brick-course rows and independent post separation.')
cli.add_argument('photograph',type=Path)
cli.add_argument('output',type=Path)
args=cli.parse_args()
assert hashlib.sha256(args.photograph.read_bytes()).hexdigest()=='835840be3949c08c2d1659af5fc908518ad4732abd34147bba68333d804d2749'
source=Image.open(args.photograph).convert('L')
img=np.asarray(source);k=2144/880
regions=[[660,700,105,125],[555,575,105,144],[560,580,111,146]]
intervals=[]
measurements=[]
for x0,x1,y0,y1 in regions:
    column=img[round(y0*k):round(y1*k),round(x0*k):round(x1*k)].mean(1)
    smooth=column-gaussian_filter1d(column,9)
    peaks,_=find_peaks(smooth,distance=3,prominence=1)
    positions=(peaks+round(y0*k))
    gaps=[int(n) for n in np.diff(peaks) if 5<=n<=8];intervals.extend(gaps)
    measurements.append({'box_in_reference':[x0,y0,x1,y1],'positive_native_rows':positions.tolist(),'native_course_intervals':gaps})
pitch=float(np.mean(intervals))/k
def unit(a):
    return np.array(a)/np.linalg.norm(a)
def camera(horizon=400,course=.064):
    f=660.;cx=440.;cy=1424/k/2
    ey=unit([(456-cx)/f,(horizon-cy)/f,1])
    near_horizontal=np.array([1.,-.006,0.]);ex=unit(near_horizontal-ey*np.dot(near_horizontal,ey));ez=np.cross(ex,ey)
    R=np.column_stack((ex,ey,ez))
    def slopes(u,v):
        ray=R.T@np.array([(u-cx)/f,(v-cy)/f,1])
        return ray/ray[1]
    dz=slopes(665,120)[2]-slopes(665,120+pitch)[2]
    far=course/dz
    height=-far*slopes(442,477.5)[2]
    near=-height/slopes(418,568)[2]
    C=np.array([-near*slopes(418,568)[0],-near,height])
    K=np.array([[f,0,cx],[0,f,cy],[0,0,1.]])
    return K@np.column_stack((R,-R@C)),C,far-near
P,C,y=camera()
samples=[{'horizon_y':h,'historical_course_m':c,'rear_y_m':round(camera(h,c)[2],3),'camera_z_m':round(camera(h,c)[1][2],3)} for h in [389,400,411] for c in [.058,.064,.071]]
d={'reference_pixels':[880,1424/k],'native_pixels':[2144,1424],'input_pixel_multiplier':k,'local_axes':'X increases towards photograph right, Y into the courtyard, Z upwards. Gate midpoint on grade at X0, front face Y0.','photo_sha256':'835840be3949c08c2d1659af5fc908518ad4732abd34147bba68333d804d2749','source':'https://commons.wikimedia.org/wiki/File:Jingxinglu_310_Long_Zhuzhai.JPG','camera_P_reference':P.tolist(),'camera_origin_m':C.tolist(),'rear_front_y_m':float(y),'rear_door_grade_reference_px':[442,477.5],'gate_grade_reference_px':[418,568],'course_target_m':.064,'mean_measured_native_pitch_px':float(np.mean(intervals)),'brick_course_checks':measurements,'depth_sensitivity':samples,'scale_note':'The scale uses a nominal 64 mm brick-and-mortar course. The photograph has no dimensioned mark. Sensitivity varies that course between 58 and 71 mm and the estimated vanishing ordinate by 11 reference pixels. Ground and threshold obscured at the edges; no survey depth is inferred.','depth_direction_px':[456,400],'horizontal_slope':-.006,'effective_equivalent_focal_length_mm':27,'evidence':'Approximate depth direction from visible orthogonal jamb returns and near and far ground fragments. Painted brick highlights at six to seven native pixels per course. The near and far thresholds are assumed to share grade. The west gable crown is screened by the utility pole.'}
doc=d
P=np.array(doc['camera_P_reference']);C=np.array(doc['camera_origin_m']);M=np.linalg.inv(P[:,:3]);y=doc['rear_front_y_m']
def cut(u,v,d):
 a=M@[u,v,1];return C+a*((d-C[1])/a[1])
points=[cut(280,268,0),cut(555,266,0)]
correct=np.hypot(2.7,.3)/(points[1][0]-points[0][0]);offset=(points[0][0]+points[1][0])/2
T=np.array([[correct,0,0,-correct*offset],[0,correct,0,0],[0,0,correct,0],[0,0,0,1]])
Q=P@np.linalg.inv(T);vec=C*correct;vec[0]-=correct*offset
doc['display_camera_P_reference']=Q.tolist();doc['display_camera_origin_m']=vec.tolist();doc['display_rear_y_m']=y*correct;doc['uniform_scale_from_2017_street_piers']=correct
doc['registered_scale_note']='Independent street registration gives approximately 2.72 m between the red rounds. Applying that one length uniformly to the photograph fit yields a course of about 58 mm. The earlier single-photo estimates and their sensitivity remain available above.'
doc['display_controls']={name:(T@np.r_[cut(u,v,d),1])[:3].tolist() for name,u,v,d in [('west_pier',280,268,0),('east_pier',555,266,0),('left_gable_estimated_crown',260,30,y),('right_gable_crown',618,32,y),('rear_arch_crown',440,240,y)]}
args.output.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n')
print(correct,doc['display_rear_y_m'],doc['display_controls'])
