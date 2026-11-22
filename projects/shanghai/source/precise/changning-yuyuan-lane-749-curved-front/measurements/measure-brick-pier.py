import json
from pathlib import Path
from PIL import Image
import numpy as np
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
s=Path(__file__).absolute().parent.parent
m=s/'measurements';rec=json.loads((m/'curved-corner-camera.json').read_bytes());P=np.array(rec['world_to_working_image']);D=rec['model'];R=D['radius_m'];eye=np.array(rec['eye_m'])
photo=np.asarray(Image.open(m/'antigng-rounded-street-front.jpg').convert('RGB'))
def undo(uv,rho=R):
 p=np.linalg.solve(P[:,:3],[*uv,1]);a=np.sum(p[:2]**2);o=eye-np.array([0,R,0]);q=2*o[:2]@p[:2];c=o[:2]@o[:2]-rho*rho;roots=np.roots([a,q,c]);t=min(r.real for r in roots if np.isreal(r)and r.real>0);x=eye+t*p;return np.arctan2(x[0],R-x[1])*R,x[2]
def strip(ss,zs):
    ar,z=np.meshgrid(ss,zs);p=np.stack([R*np.sin(ar/R),R-R*np.cos(ar/R),z,np.ones(ar.shape)],axis=-1)@P.T
    q=(p[:,:,:2]/p[:,:,2,None]).reshape(-1,2)*[3.3,2632/798]
    return np.stack([map_coordinates(photo[:,:,k],q[:,::-1].T,order=1,mode='nearest')for k in range(3)],axis=1).reshape(*ar.shape,3)

if __name__=='__main__':
 x=np.linspace(-1.83,-1.25,251);z=np.linspace(-1.65,2.22,1201)
 rgb=strip(x,z).astype(float)
 sampled=np.median(rgb[:,(x>-1.613)&(x< -1.437)],axis=1)
 brightness=sampled@np.array([.25,.55,.20])-.55*(sampled[:,0]-sampled[:,2])
 signal=gaussian_filter1d(brightness,.75)-gaussian_filter1d(brightness,5)
 peaks,_=find_peaks(signal,distance=23,prominence=12)
 assert np.array_equal(peaks,find_peaks(signal,distance=21,prominence=9)[0])
 assert np.array_equal(peaks,find_peaks(signal,distance=24,prominence=15)[0])
 bed=z[peaks];short_rows=[];course_readings=[]
 for idx,(a,b)in enumerate(zip(bed,bed[1:])):
    vals=np.median(rgb[np.abs(z-(a+b)/2)<.009],axis=0)
    intensity=vals@np.array([.25,.55,.2])-.5*(vals[:,0]-vals[:,2])
    high=gaussian_filter1d(intensity,1)-gaussian_filter1d(intensity,6)
    pp,meta=find_peaks(high,distance=20,prominence=29)
    joints=[float(x[i])for i in pp if -1.625<x[i]<-1.41]
    course_readings.append(dict(z_m=float((a+b)/2),strong_vertical_joints_s_m=joints))
    if len(joints)>=2:short_rows.append(idx)
 across=[]
 for a,b in [((288,140),(313,140)),((294,360),(322,360))]:
    across.append([undo(a)[0],undo(b)[0]])
 recs=dict(original_sha256=rec['original_photo_sha256'],crop_sha256=rec['crop_sha256'],between_bays='left and centre',
   pier_width_m=float(np.median([b-a for a,b in across])),observed_pier_edges_s_m=across,
   photographed_beds_z_m=np.round(bed,5).tolist(),course_median_m=float(np.median(np.diff(bed))),
   course_readings=course_readings,rows_with_two_strong_inside_joints=short_rows,
   description='大面积水刷石之间嵌一条窄色砖带。横缝连续，一皮多见完整长面，相邻一皮有两处清楚的竖向分缝。')
 (m/'vertical-brick-pier.json').write_text(json.dumps(recs,ensure_ascii=False,indent=2)+'\n')
 print(len(bed),recs['course_median_m'],recs['pier_width_m'],short_rows)
