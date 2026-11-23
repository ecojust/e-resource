"""Reproduce the archival east-gable measurements and register independent numbered photographs.

Album measurements use the 500,240 to 1000,732 crop of the scanned 1280×1823
page, enlarged by 1.48. Gao's full 2013 frame is 4247×3239. Its working
crop is 2350,340 to 3955,3239, displayed at 420×760. Only coordinates are stored.
"""
from pathlib import Path
import argparse,json
import numpy as np
from scipy.optimize import least_squares
ALBUM={
 'door_left_spring':[168,507],'door_right_spring':[226,508],'door_left_threshold':[169,646],
 'door_right_threshold':[225,646],'large_left_floor':[126,438],'large_left_eave':[133,200],
 'large_ridge':[341,-9],'upper_common_base_left':[197,363],'upper_common_base_right':[311,368],
 'upper_left_jamb':[201,271],'upper_right_jamb':[306,275],'attic_left_top':[320,98],
 'attic_right_bottom':[355,164],'lower_small_jamb_left':[265,507],'lower_small_jamb_right':[306,589],
 'lower_brace_joint':[201,435],'lower_lintel_tie':[135,357],'large_tie_left':[133,195],
 'dark_center_post':[254,270],'attic_center_belt_left':[308,99]}
GAO={'door_left_spring':[131,565],'door_right_spring':[170,566],
 'large_left_floor':[91,471],'large_left_eave':[73,177],
 'large_ridge':[177,47],'upper_common_base_left':[139,391],'upper_common_base_right':[196,408],
 'upper_left_jamb':[130,285],'upper_right_jamb':[184,305],
 'attic_left_top':[177,163],'attic_right_bottom':[207,233],
 'lower_small_jamb_left':[195,570],'lower_small_jamb_right':[222,658],
 'lower_brace_joint':[142,478],'lower_lintel_tie':[98,377],
 'large_tie_left':[78,180],'dark_center_post':[157,298],'attic_center_belt_left':[171,159]}
def project(H,p):
 p=np.c_[p,np.ones(len(p))]@H.T
 return p[:,:2]/p[:,2,None]
def homography(xy,uv):
 x=xy[:,0];y=xy[:,1];n=len(x);zero=np.zeros(n);one=np.ones(n);u,v=uv.T
 A=np.stack([np.stack([x,y,one,zero,zero,zero,-u*x,-u*y],axis=1),np.stack([zero,zero,zero,x,y,one,-v*x,-v*y],axis=1)],axis=1).reshape(-1,8)
 h=np.r_[np.linalg.lstsq(A,uv.ravel(),rcond=None)[0],1.]
 fit=least_squares(lambda a:(project(np.r_[a,1].reshape(3,3),xy)-uv).ravel(),h[:8],loss='soft_l1',f_scale=3)
 return np.r_[fit.x,1].reshape(3,3)
def main():
 W=.94;step=.18;spring=2.36
 # The near-level negative shows only weak convergence. The main uprights lean
 # about 1.1/100 pixels of height. The eave band falls 2.2/100 pixels across it.
 B=np.array([[58/W,.78,197],[.022*58/W,-138.5/(spring-step),646+.18*138.5/(spring-step)],[0,0,1.]])
 proj=np.linalg.inv(B)
 uv={k:project(proj,[v])[0].round(4).tolist()for k,v in ALBUM.items()}
 keys=list(GAO);xyz=np.array([uv[k]for k in keys]);target=np.array([GAO[k]for k in keys]);H=homography(xyz,target)
 delta=np.linalg.norm(project(H,xyz)-target,axis=1)
 record={'stations':{'album':{'url':'https://brs.russianshanghai.city/architects/a-l/v-n-dronnikoff','title':'East Elevation, Maisonettes on Route Maresca, 1935','native_size':[1280,1823],'study_crop':[500,240,1000,732],'study_size':[740,728],'address_detail':'Album shows the type. Individual door number is illegible.','pixels':ALBUM,'meters_to_study_pixels':B.tolist()},'gao_1_2':{'url':'https://blog.sina.cn/dpool/blog/s/blog_5d1bdf480101esph.html','native_size':[4247,3239],'study_crop':[2350,340,3955,3239],'study_size':[420,760],'address_detail':'No.1 plaque right of the arch, No.2 on the cream wall beside the outdoor stair.','pixels':GAO,'meters_to_study_pixels':H.tolist(),'errors_px':dict(zip(keys,delta.round(3).tolist())),'median_px':float(np.median(delta)),'p90_px':float(np.percentile(delta,90))}},'scale_assumptions_m':{'odd_door_clear_width':W,'threshold_height':step,'door_spring_height':spring},'main_front_meters':uv,'limits':'Dimension estimates depend on doorway scale; separate southern photo stations must be registered on their own. Projected points around a verge may refer to different roof tile and timber edges.'}
 Path(__file__).with_name('north-front-registration.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 print('modern',record['stations']['gao_1_2']['median_px'],record['stations']['gao_1_2']['p90_px']);print(uv)
if __name__=='__main__':main()
