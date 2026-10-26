#!/usr/bin/env python3
"""Recompute explicit per-pane registration from unchanged CC0 reference pixels.
Analysis reads JPEG pixels to locate dark window bars; it writes JSON evidence
only. The production build embeds the original JPEG without resampling it.
"""
from pathlib import Path
import hashlib,json
import numpy as np
from PIL import Image,ImageOps
from scipy.ndimage import map_coordinates,gaussian_filter1d
HERE=Path(__file__).resolve().parent
IMAGE=HERE/'research/nissin-2025-suicasmo-original.jpg'

def homography(quad):
 a=[];b=[]
 for (u,v),(x,y) in zip([(0,0),(1,0),(1,1),(0,1)],quad):
  a.extend([[u,v,1,0,0,0,-u*x,-v*x],[0,0,0,u,v,1,-u*y,-v*y]]);b.extend([x,y])
 return np.r_[np.linalg.solve(a,b),1].reshape(3,3)
def project(h,p):
 q=np.c_[p,np.ones(len(p))]@h.T;return q[:,:2]/q[:,2,None]

def main():
 im=np.array(ImageOps.exif_transpose(Image.open(IMAGE))).astype(float);gray=im[:,:,:3]@np.array([.2126,.7152,.0722])
 candidates=[
  ('left5',5,'left',[[1343,2281],[1484,2260],[1484,2441],[1340,2457]],4),
  ('right5',5,'right',[[1744,2222],[1891,2199],[1894,2378],[1743,2397]],4),
  ('left4',4,'left',[[1343,2681],[1484,2662],[1484,2887],[1340,2904]],5),
  ('right4',4,'right',[[1749,2627],[1902,2608],[1906,2831],[1750,2850]],5),
  ('left3',3,'left',[[1341,3148],[1484,3130],[1484,3359],[1338,3373]],5),
  ('right3',3,'right',[[1756,3098],[1907,3079],[1912,3320],[1759,3336]],5)]
 windows=[]
 for name,floor,side,quad,rows in candidates:
  h=homography(quad);n=400;u,v=np.meshgrid(np.linspace(0,1,n),np.linspace(0,1,n));p=project(h,np.c_[u.ravel(),v.ravel()]);a=map_coordinates(gray,[p[:,1],p[:,0]],order=1).reshape(n,n)
  col=gaussian_filter1d(np.median(a[30:-30],axis=0),1)
  def bars(profile,targets,window):
   out=[]
   for target in targets:
    low=max(1,int((target-window)*n));high=min(n-1,int((target+window)*n));i=low+int(np.argmin(profile[low:high]));base=float(np.percentile(profile[low:high],85));threshold=profile[i]+(base-profile[i])*.42
    l=i;r=i
    while l>low and profile[l-1]<threshold:l-=1
    while r<high-1 and profile[r+1]<threshold:r+=1
    out.append({'center':i/(n-1),'black_interval':[l/(n-1),r/(n-1)],'contrast':float(base-profile[i])})
   return out
  xb=bars(col,[.25,.50,.75],.085)
  mask=np.ones(n,bool)
  for x in xb:
   lo,hi=x['black_interval'];mask[max(0,int((lo-.015)*n)):min(n,int((hi+.015)*n))]=False
  row=gaussian_filter1d(np.median(a[:,mask],axis=1),1)
  yb=bars(row,[.20,.47,.74] if rows==4 else [.18,.40,.61,.82],.065)
  assert all(x['contrast']>8 for x in xb+yb),(name,xb,yb)
  # Inset each photographic pane from detected frame bars by >=2 pixels.
  # Source coordinates refer only to glazing, never stone or human/street pixels.
  x_edges=[(0,0)]+[tuple(t['black_interval']) for t in xb]+[(1,1)]
  y_edges=[(0,0)]+[tuple(t['black_interval']) for t in yb]+[(1,1)]
  panes=[]
  for rr in range(rows):
   for cc in range(4):
    xl=x_edges[cc][1]+.018;xr=x_edges[cc+1][0]-.018
    yt=y_edges[rr][1]+.012;yb0=y_edges[rr+1][0]-.012
    assert xr-xl>.08 and yb0-yt>.07
    pq=project(h,np.array([[xl,yt],[xr,yt],[xr,yb0],[xl,yb0]]))
    panes.append({'row_from_top':rr,'column_from_left':cc,'source_oriented_quad_px':pq.tolist(),'source_normalized_bounds':[xl,yt,xr,yb0]})
  windows.append({'id':name,'floor':floor,'side':side,'rows':rows,'columns':4,'source_outer_glass_quad_oriented_px':quad,'normalized_to_oriented_homography':h.tolist(),'vertical_bar_observations':xb,'horizontal_bar_observations':yb,'panes':panes})
 out={'schema':'bund05-per-pane-photo-registration-v1','image':'research/nissin-2025-suicasmo-original.jpg','image_sha256':hashlib.sha256(IMAGE.read_bytes()).hexdigest(),'image_bytes':IMAGE.stat().st_size,'author':'Suicasmo','license':'CC0-1.0','date':'2025-05-01','source_url':'https://commons.wikimedia.org/wiki/File:Nissin_Building_20250501.jpg','stored_size':[5184,3456],'exif_orientation':6,'oriented_size':[3456,5184],'coordinate_contract':'All controls are original EXIF-oriented pixels. Stored uv=(oriented_y/5184,(3455-oriented_x)/3456). No resampled image is embedded.','method':'Independent 3x4/perspective calibration provided the initial location; six visible glazing quadrilaterals were individually corrected against actual 100% inspection. Dark frame bars are detected only inside each registered window; every sampled glass pane is inset from them. Geometry frames remain independent untextured solids.','scope':'Only six flat central third/fourth/fifth-floor glazing assemblies. Canted bays, attic, doors, stone, exterior shadows and occluded lower panes remain unprojected. The lower-left third-floor indoor dark reflection is inside real glazing, not a street object.','limitations':['Manual outer glazing corners and per-pane registration are photographic estimates; not survey-grade photogrammetry.','Absolute front-plane u bias is not used to map glass.','No date claim beyond the referenced 2025 view.'],'windows':windows}
 (HERE/'photo-glass-controls.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'windows':len(windows),'panes':sum(len(w['panes']) for w in windows),'image_sha256':out['image_sha256'],'minimum_bar_contrast':min(b['contrast'] for w in windows for b in w['vertical_bar_observations']+w['horizontal_bar_observations'])},indent=2))
if __name__=='__main__':main()
