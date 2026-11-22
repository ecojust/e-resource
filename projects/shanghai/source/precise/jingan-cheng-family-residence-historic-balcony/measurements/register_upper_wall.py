import json,sys,hashlib
from pathlib import Path
import importlib.util,numpy as np
from measure_window_surrounds import build,face_point,intersect
from pathlib import Path
import argparse
p=argparse.ArgumentParser();p.add_argument('camera',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
cam=a.camera;P=np.array(json.loads(cam.read_bytes())['gao2018']['P']);j=build(P)
def face(i,pts):
 seg=j['faces'][i];return [np.round(face_point(P,uv,np.array(seg['start']),np.array(seg['end'])),5).tolist()for uv in pts]
def line(i,pts):return [[v for v in q]for q in face(i,pts)]
j['camera_sha256']=hashlib.sha256(cam.read_bytes()).hexdigest()
j['main_eave_courses']=[round(intersect(P,[1820,v],1,0)[2],4)for v in [1244,1224,1216,1204,1184,1174,1114,1095,1082]]
j['upper_margin_m']=[line(1,p)for p in [[[1087,978],[1205,978],[1206,866],[1430,861]],[[1715,846],[1943,842],[1947,947],[2054,943]]]]
j['pier_wings_uv']=[[1087,970],[1205,968],[1207,868],[1430,858],[1715,850],[1940,846],[1940,943],[2054,943]]
j['right_bay_crown']={}
for k,p in {
 'outline':[[2662,711],[2877,707],[2881,892],[2667,898]],
 'inner':[[2687,729],[2853,725],[2858,871],[2694,875]],
 'top_cap':[[2615,668],[2923,661],[2929,704],[2606,712]],
 'stone_sill':[[2655,898],[2900,889],[2903,912],[2655,922]],
 'left_volute':[[2536,820],[2539,786],[2548,771],[2572,758],[2594,747],[2608,735],[2615,715],[2626,709],[2624,822]],
 'right_volute':[[2920,711],[2931,707],[2941,726],[2951,740],[2977,750],[2992,766],[3006,784],[2993,810],[2989,815],[2921,815]],
 'left_spiral_center':[[2592,790],[2558,789],[2593,757]],
 'right_spiral_center':[[2958,779],[2993,779],[2958,748]],
 'upper_light':[[2729,751],[2737,745],[2799,744],[2811,747],[2808,754],[2772,786],[2737,761]],
 'right_light':[[2797,812],[2827,777],[2834,779],[2838,790],[2837,838],[2829,847],[2818,844],[2791,819]],
 'lower_light':[[2733,859],[2766,826],[2777,828],[2811,858],[2807,868],[2744,870]],
 'left_light':[[2704,785],[2709,778],[2719,780],[2749,812],[2720,846],[2714,848],[2706,841],[2703,830]],
 }.items():j['right_bay_crown'][k]=dict(native_pixels=p,face_xz_m=line(3,p))
j['right_shoulder_z']=round(np.mean([q[1]for q in line(3,[[2440,821],[3170,811]])]),5)
j['left_and_centre_top']=line(1,j['pier_wings_uv'])
out=a.output;out.write_text(json.dumps(j,indent=2,ensure_ascii=False)+'\n')
for k in ['faces','main_eave_courses','left_and_centre_top','right_shoulder_z']:print(k,j[k])
