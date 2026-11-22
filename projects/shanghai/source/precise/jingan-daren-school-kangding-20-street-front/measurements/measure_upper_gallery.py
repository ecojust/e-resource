"""Reproject the fourteen upper gallery apertures and compare two independent street views."""
import argparse,json,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'source'))
from daren_photo_plane import camera_matrix,pixel
BASE=[(40,73),(92,171),(190,225),(248,329),(345,385),(404,483),(500,535),(575,610),(625,702),(721,754),(775,854),(879,916),(932,1010),(1028,1063)]
def tex(img,P,x,y,z):
 xx,zz=np.meshgrid(x,z);pts=np.stack([xx.ravel(),np.full(xx.size,y),zz.ravel(),np.ones(xx.size)])
 q=P@pts
 return map_coordinates(img, [q[1]/q[2],q[0]/q[2]],order=1,mode='nearest').reshape(xx.shape)
def strongest(a,dist,lo,hi):
 t=(a>=lo)&(a<=hi);return float(a[t][np.argmax(dist[t])])
def edgeprofile(g,axis):
 return np.median(np.abs(np.gradient(gaussian_filter1d(g,1.6,axis=axis),axis=axis)),axis=1-axis)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('reference',type=Path);ap.add_argument('centre',type=Path);ap.add_argument('east',type=Path);ap.add_argument('result',type=Path);a=ap.parse_args()
 names=['video-4.28','centre20-wall','east20-wall'];paths=[a.reference,a.centre,a.east]
 source={k:np.array(Image.open(p).convert('L'),float) for k,p in zip(names,paths)}
 cams={k:camera_matrix(k) for k in names}
 out=[];ygrid=np.arange(-.10,.43,.01)
 for i,(u,v)in enumerate(BASE,1):
  l=u*26.7/1100-.1;r=v*26.7/1100-.1;x=np.arange(l-.19,r+.19,.00625);z=np.arange(9.12,11.71,.00625)
  area=tex(source[names[0]],cams[names[0]],x,0.,z);edge=edgeprofile(area[(z>9.7)&(z<11.12)],1)
  l1=strongest(x,edge,l-.09,l+.09);r1=strongest(x,edge,r-.09,r+.09)
  edz=edgeprofile(area[:,(x>l1+.1)&(x<r1-.1)],0)
  bot=strongest(z,edz,9.37,9.68);top=strongest(z,edz,11.15,11.49)
  xx=np.arange(l1+.09,r1-.09,.013);zz=np.arange(9.84,10.92,.035)
  scores=[]
  for y in ygrid:
   cols=[]
   for name in names[1:]:
    g=tex(source[name],cams[name],xx,y,zz);s=np.median(g,axis=0);s=gaussian_filter1d(s,1.5)-gaussian_filter1d(s,5.6)
    cols.append(s/(np.linalg.norm(s)+1e-9))
   scores.append(float(cols[0]@cols[1]))
  iy=int(np.argmax(scores));yy=float(ygrid[iy])
  out.append(dict(number=i,left=l1,right=r1,bottom=bot,top=top,center_vs_east_depth_m=round(yy,3),corr=round(scores[iy],4),correlations=np.round(scores,4).tolist(),outline_video_px=[pixel([x,0,z],'video-4.28')for x,z in [(l1,bot),(r1,bot),(r1,top),(l1,top)]]))
  print(i, *(round(n,2)for n in (l1,r1,bot,top,yy,scores[iy])))
 print('usable depths and median',[o['center_vs_east_depth_m']for o in out if o['corr']>.67 and -.08<o['center_vs_east_depth_m']<.4])
 result={'evidence':[{'camera':n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}for n,p in zip(names,paths)],'depth_grid_m':ygrid.round(3).tolist(),'method':'2026 upper opening endpoints traced in a levelled video frame and refined against vertical and horizontal intensity transitions. For the 2020 stations, the horizontal window contrast profile was standardized and the same frame was tested on stepped planes. Retain low correlations and boundary maxima.','openings':out}
 a.result.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
