from pathlib import Path
from PIL import Image,ExifTags
import json,numpy as np,argparse
P=Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('--photo',default=str(P/'hsbc-20250501-original.jpg'));args=ap.parse_args();im=Image.open(args.photo);a=np.asarray(im).mean(axis=2);d=json.loads((P/'calibration.json').read_text())
def homography(q):
 A=[];b=[]
 for (s,t),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],q):A.extend([[s,t,1,0,0,0,-s*x,-t*x],[0,0,0,s,t,1,-s*y,-t*y]]);b.extend([x,y])
 return np.r_[np.linalg.solve(A,b),1].reshape(3,3)
for w in d['windows']:
 H=homography(np.array(w['quad_display'])*2.7);s,t=np.meshgrid(np.arange(300)/299,np.arange(500)/499);q=H@np.stack([s.ravel(),t.ravel(),np.ones(s.size)]);x=q[0]/q[2];y=q[1]/q[2];g=a[np.round(y).astype(int),np.round(x).astype(int)].reshape(s.shape)
 rows=np.arange(40,475,5); pts=[]
 for y in rows:
  sm=np.convolve(g[y],'valid' and np.ones(9)/9,mode='same'); xx=90+sm[90:190].argmin()
  if g[y,30:270].mean()>105:pts.append([y/499,xx/299])
 cc=np.polyfit(np.array(pts)[:,0],np.array(pts)[:,1],1)
 bars=[]
 for lo,hi in ([(.25,.42)] if w['level']==3 else[(.19,.38),(.59,.76)]):
  hp=[]
  for x in range(25,275,5):
   if abs(x/299-(cc[0]*.5+cc[1]))<.13:continue
   sm=np.convolve(g[:,x],np.ones(8)/8,mode='same');yy=int(lo*499)+sm[int(lo*499):int(hi*499)].argmin();hp.append([x/299,yy/499])
  # robust remove narrow grille alternatives; main center among per-column locations
  med=np.median(np.array(hp)[:,1]);hp=np.array([p for p in hp if abs(p[1]-med)<.04]);hc=np.polyfit(hp[:,0],hp[:,1],1);bars.append(hc.tolist())
 w['measured_center_s_of_t']=cc.tolist();w['measured_main_bars_t_of_s']=bars
 w['quad_original_pixels']=(np.array(w['quad_display'])*2.7).round(3).tolist()
 print(w['id'],'center',cc,'bars',bars)
d['calibration_limits']='Manual photo-window quadrilaterals plus numeric broad-frame centerline estimates; no survey scale or global photogrammetric registration. Main physical casement bars will be matched; thin decorative grille detail is carried in the original photograph.'
(P/'calibration.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
s=json.loads((P/'photo-source.json').read_text());ex=im.getexif();s['exif_ifd']={ExifTags.TAGS.get(k,str(k)):str(v) for k,v in ex.get_ifd(0x8769).items()};s['gps_ifd']={ExifTags.GPSTAGS.get(k,str(k)):str(v) for k,v in ex.get_ifd(0x8825).items()};(P/'photo-source.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
