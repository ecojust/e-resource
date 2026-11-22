"""Sample orange roof bedding rows in unobstructed columns beside the dormer."""
import hashlib,json,os
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

HERE=Path(__file__).resolve().parent
photo=Path(os.environ.get('CYPRESS_LAWN_PHOTO',HERE.parent/'lawn-original.jpg'))
im=np.array(Image.open(photo).convert('RGB'),float)
Q=np.array(json.loads((HERE/'lawn-camera.json').read_bytes())['pinhole_3x4'])
def fixed_depth(u,v,y):
    H=Q[:,[0,2,3]].copy();H[:,2]+=y*Q[:,1]
    r=np.linalg.solve(H,[u,v,1]);return np.array([r[0]/r[2],y,r[1]/r[2]])
low=[fixed_depth(u,v,-.27) for u,v in [(455,245),(542,239)]]
high=[fixed_depth(u,v,3.7) for u,v in [(406,174),(584,151)]]
slope=(np.mean(high,0)[2]-np.mean(low,0)[2])/3.97
base=np.mean(low,0)[2]+slope*.27
def roof(u,v):
   H=np.c_[Q[:,0],Q[:,1]+slope*Q[:,2],Q[:,3]+base*Q[:,2]]
   r=np.linalg.solve(H,[u,v,1.]);return [r[0]/r[2], r[1]/r[2], base+slope*r[1]/r[2]]
stroke=[];steps=[]
for u,from_v,to_v in [(524,200,236),(530,189,234),(535,190,233),(540,190,231),(545,187,228),(449,183,199)]:
    profile=im[from_v:to_v+1,u-1:u+2].mean(axis=1)@np.array([.35,.52,.13])
    sm=gaussian_filter1d(profile,.52)
    troughs,_=find_peaks(-sm,prominence=7.4,distance=3)
    points=[]
    for i in troughs:
        a,b,c=sm[i-1:i+2];delta=np.clip((a-c)/(2*(a-2*b+c)),-.5,.5)
        y=float(from_v+i+delta);row=roof(u,y);points.append(dict(pixel=[u,y],surface_yz=row[1:]))
    for a,b in zip(points,points[1:]):
        delta=abs(a['surface_yz'][0]-b['surface_yz'][0])
        if .085<delta<.31:steps.append(delta)
    stroke.append(dict(column=u,measured_centers=points))
step=float(np.median(steps));out=dict(photo_sha256=hashlib.sha256(photo.read_bytes()).hexdigest(),surface_slope=float(slope),elevation_at_y0_m=float(base),samples=stroke,measured_deltas_y=steps,row_advance_y_m=step,row_pitch_along_slope_m=float(step*np.hypot(1,slope)),reference='草坪面上方大屋面，避开老虎窗、筒脊及树木。像素谷底量取每行瓦的暗缝。屋面进深与砖瓦尺寸均为单图估计。')
(HERE/'roof-tile-courses.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(slope,base,sum(len(c['measured_centers'])for c in stroke),step,out['row_pitch_along_slope_m'],[len(c['measured_centers'])for c in stroke])
