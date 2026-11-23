from pathlib import Path
from PIL import Image
from scipy.ndimage import map_coordinates
import argparse
import numpy as np
parser=argparse.ArgumentParser(description='Read four candidate mortar band periods from the original 2053 by 1369 reference photograph.')
parser.add_argument('original',type=Path)
a=parser.parse_args();im=np.array(Image.open(a.original).convert('L'),float)
assert im.shape==(1369,2053)
for x,y,W,H in [(800,602,50,50),(820,622,60,40),(705,655,47,25),(850,630,55,36)]:
 estimates=[]
 for slope in np.linspace(-.32,-.08,49):
  t=np.arange(-H/2,H/2,.25);u=np.arange(-W/2,W/2);uv,tt=np.meshgrid(u,t)
  plane=map_coordinates(im,[y+tt+slope*uv,x+uv],order=1).mean(axis=1)
  p=[]
  for pitch in np.arange(1.9,8.,.02):
   wave=np.abs(np.mean((plane-np.mean(plane))*np.exp(-2j*np.pi*t/pitch)))
   p.append((wave,pitch))
  amp,per=max(p);estimates.append((round(amp,3),round(per,3),round(slope,4)))
 print(x,y,sorted(estimates,reverse=True)[:2])
