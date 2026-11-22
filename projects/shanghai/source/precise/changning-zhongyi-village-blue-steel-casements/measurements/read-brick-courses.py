"""Measure repeated mortar beds and head joints on the solid pier between the two photographed windows."""
from pathlib import Path
import json,runpy
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks

HERE=Path(__file__).absolute().parent
f=runpy.run_path(HERE/'fit-windows.py')
crop=json.loads((HERE/'primary-crop.json').read_bytes())
im=np.asarray(Image.open(HERE/crop['file']).convert('RGB'),dtype=float)
xs=np.linspace(-2.00,-.88,361);zs=np.linspace(.12,1.38,501)
x,z=np.meshgrid(xs,zs)
coords=f['G']@np.stack([x.ravel(),z.ravel(),np.ones(x.size)])
u,v=coords[:2]/coords[2:]
pix=np.stack([map_coordinates(im[:,:,c],[v-crop['crop_original_px'][1],u-crop['crop_original_px'][0]],order=1,mode='nearest')for c in range(3)],axis=1).reshape(*x.shape,3)
score=pix.mean(axis=2)-.5*(pix[:,:,0]-pix[:,:,2])
# Suppress the bedding illumination independently in each column before
# measuring row prominence. The photographed wires cover only a small part of this pier.
edge=np.median(score-gaussian_filter1d(score,6,axis=0),axis=1)
peaks,meta=find_peaks(edge,distance=16,prominence=16.)
dz=np.diff(zs[peaks]);period=float(np.median(dz))
good=[float(v)for v in dz if .8*period<v<1.2*period]
height=float(np.median(good))
beds=[float(zs[i])for i in peaks]
widths=[];rows=[]
for lo,hi in zip(beds,beds[1:]):
    if not .79*height<hi-lo<1.21*height:continue
    sample=np.median(score[np.abs(zs-(lo+hi)/2)<.006],axis=0)
    excess=sample-gaussian_filter1d(sample,9)
    joints,_=find_peaks(excess,distance=37,prominence=12.)
    d=np.diff(xs[joints]);widths.extend(float(v)for v in d if .125<v<.39)
    rows.append(dict(z_mid_m=round((lo+hi)/2,5),x_at_joints_m=np.round(xs[joints],5).tolist()))
if __name__=='__main__':
    data=dict(photo_sha256=crop['source_sha256'],crop_sha256=crop['sha256'],pier_x_m=[xs[0],xs[-1]],pier_z_m=[zs[0],zs[-1]],
        resolved_mortar_beds_m=np.round(beds,5).tolist(),regular_course_intervals_m=np.round(good,5).tolist(),
        course_height_m=round(height,5),regular_horizontal_joints=rows,individual_width_estimates_m=np.round(widths,5).tolist(),
        header_module_m=round(float(np.median([v for v in widths if v<.23])),5),
        stretcher_module_m=round(float(np.median([v for v in widths if v>=.23])),5),
        bond='每皮短头与长砖面交替，相邻砖皮错缝。',method='真实照片经立面校正，逐行取灰度和红蓝差；在窗间墙读水平灰缝，再对相邻两缝中部逐皮读竖缝。所有长度随采用的1.55米窗高成比例。')
    (HERE/'brick-course-measurement.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print('beds',len(beds),'regular',len(good),height,'joints',len(widths),np.round(np.quantile(widths,[.1,.25,.5,.75,.9]),4))
