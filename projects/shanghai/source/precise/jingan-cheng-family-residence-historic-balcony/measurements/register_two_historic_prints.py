import argparse,hashlib,json
from pathlib import Path
import cv2,numpy as np
def match(first,second):
 s=cv2.imread(str(first),0)[:216];h=cv2.imread(str(second),0);sift=cv2.SIFT_create(nfeatures=1500,contrastThreshold=.015);cv2.setNumThreads(1)
 a,d=sift.detectAndCompute(s,None);b,e=sift.detectAndCompute(h,None)
 matches=sorted([m for m,n in cv2.BFMatcher().knnMatch(d,e,k=2)if m.distance<n.distance*.77],key=lambda m:m.queryIdx)
 x=np.float32([a[i.queryIdx].pt for i in matches]);y=np.float32([b[i.trainIdx].pt for i in matches])
 hold=(np.arange(len(x))%4)==0;H,keep=cv2.findHomography(x[~hold],y[~hold],cv2.RANSAC,2)
 # A second scan of the same negative can be aligned over the street, both facades and the car.
 dist=np.linalg.norm(cv2.perspectiveTransform(x.reshape(-1,1,2),H)[:,0]-y,axis=1);test=dist[hold]
 return dict(sources=[dict(name=p.name,sha256=hashlib.sha256(p.read_bytes()).hexdigest())for p in [first,second]],test='SIFT correspondences, Lowe ratio 0.77. Every fourth sorted correspondence is held out before RANSAC.',matrix_323_to_640=H.tolist(),matches=len(x),training_inliers=int(keep.sum()),test_count=int(hold.sum()),test_within_2_pixels=int((test<2).sum()),held_out_median_px=round(float(np.median(test)),4),held_out_p90_px=round(float(np.quantile(test,.90)),4),same_historical_exposure=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('first',type=Path);p.add_argument('second',type=Path);p.add_argument('out',type=Path);a=p.parse_args()
 a.out.write_text(json.dumps(match(a.first,a.second),ensure_ascii=False,indent=2)+'\n')
