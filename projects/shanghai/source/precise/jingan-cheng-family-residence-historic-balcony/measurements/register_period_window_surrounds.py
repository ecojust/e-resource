"""Log the measured window-edge differences between the old and later street photographs."""
import json,sys,numpy as np
from pathlib import Path
import argparse
from measure_window_surrounds import face_point,intersect
parser=argparse.ArgumentParser(description=__doc__)
for key in ['later_wall', 'period_camera', 'output']:parser.add_argument(key,type=Path)
args=parser.parse_args()
P=np.array(json.loads(args.period_camera.read_bytes())['P'])
data=json.loads(args.later_wall.read_bytes())
obs={
'left_splay':([[23.5,89.4],[60.6,101.6],[60.1,184.8],[22.9,176]],[[28.2,97.6],[55.1,107.1],[54.1,180.6],[27.3,172.0]]),
'right_splay':([[311,134.8],[363.8,131.0],[364,205.8],[311,206.4]],[[319,138.3],[357.1,136],[356,201.6],[320.6,204.6]]),
'right_front':([[431.2,136.3],[471.1,140.5],[474,212],[430.5,208.8]],[[437.7,142.6],[466.2,146.2],[466.7,208.3],[436.7,204.9]])}
def point(xz,o,u):
 p=P@np.r_[o+xz[0]*u,xz[1],1];return p[:2]/p[2]
def rect(q):
 tl,tr,br,bl=q
 return [round(float(z),5)for z in ((tl[0]+bl[0])/2,(tr[0]+br[0])/2,(bl[1]+br[1])/2,(tl[1]+tr[1])/2)]
# The west return is truncated in the historical negative. Its own three visible
# horizontal edges recover a shallower local direction than the modern-only estimate.
angles=[]
for a,b in [((23.5,89.4),(60.6,101.6)),((28.2,97.6),(55.1,107.1)),((22.9,176),(60.1,184.8))]:
 p1,p2=[intersect(P,q,2,2.47)[:2] for q in (a,b)]
 uv=p2-p1;angles.append(np.arctan2(uv[1],uv[0]))
az=float(np.median(angles));u=np.array([np.cos(az),np.sin(az)]);q=data['faces'][0]
q['later_start']=q['start'];q['start']=np.round(np.array(q['end'])-u*1.78,5).tolist()
q['historic_horizontal_directions_deg']=np.round(np.rad2deg(angles),2).tolist()
q['direction_note']='The printed left edge interrupts this return. Three separate old window edges constrain the local direction with the historical camera. The wall continues only to just west of the recorded surround.'
for win in data['windows']:
 k=win['key']
 if k not in obs:continue
 f=data['faces'][win['face']];a=np.array(f['start']);b=np.array(f['end']);u=b-a;u/=np.linalg.norm(u)
 ro,ri=obs[k];win['old_640_surround']=ro;win['old_640_opening']=ri
 for field,c in [('surround_m',ro),('opening_m',ri)]:
  old=win[field];new=rect(np.array([face_point(P,uv,a,b)for uv in c]))
  win['later_'+field]=old;win[field]=new
  def error(r):
   x,X,z,Z=r
   delta=np.array([point(uv,a,u)for uv in [(x,Z),(X,Z),(X,z),(x,z)]])-c
   return np.round(delta,2).tolist()
  win['from_later_'+field+'_minus_old_photo_px']=error(old);win['from_historic_'+field+'_minus_old_photo_px']=error(new)
  print(k,field,'old/new',old,new,'error before/after',np.linalg.norm(error(old),axis=1).round(1),np.linalg.norm(error(new),axis=1).round(1))
data['historic_adjustment']='The three exposed side openings use the 640px historical reprint. Later-camera rectangles are retained for comparison. Both central window heads are common to the two photographs. Balcony obscures their feet in the old exposure.'
for r in data['windows']:
 k=r['key'];f=data['faces'][r['face']];a=np.array(f['start']);b=np.array(f['end']);u=b-a;u/=np.linalg.norm(u);n=np.array([-u[1],u[0]])
 if k=='left_splay':
  r['historic_field_note']='Dark opening across the full visible aperture. The 640px print at x41 from row110 to154 has an uninterrupted dark field (no intermediate light meeting stile).'
  continue
 uv={'balcony_left':[137,127.5],'balcony_right':[243,141.0],'right_splay':[349,149.0],'right_front':[443,149.5]}[k]
 r['historic_transom_px']=uv;r['transom_z_m']=float(np.round(face_point(P,uv,a+.139*n,b+.139*n)[1],5))
 print(k,r['transom_z_m'],r['opening_m'][-1])
args.output.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n')
