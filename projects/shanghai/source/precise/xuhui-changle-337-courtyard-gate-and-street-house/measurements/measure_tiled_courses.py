"""Measure repeated waves and course seams in unoccluded patches of the 2017 roof."""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
from PIL import Image
import argparse
cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('original', type=Path);cli.add_argument('output',type=Path);args=cli.parse_args()
im=np.asarray(Image.open(args.original).convert('L'),float)
def signal(x,y,dx,dy,samples,strip):
 s=np.arange(samples);k=np.arange(-strip,strip+1)
 xx=x+s[:,None]*dx-k*dy;yy=y+s[:,None]*dy+k*dx
 values=map_coordinates(im,[yy,xx],order=1)
 a=np.median(values,axis=1);return a-gaussian_filter1d(a,11)
slices=[]
for label,x,y,dx,dy,l,sw,mn,mx in [('crest A',2070,1224,1,-.11,380,2,10,39),('crest B',2220,1165,1,-.125,280,2,10,39),('crest C',2590,1100,1,-.13,310,2,10,39),('courses A',2250,1075,.02,1,151,12,17,51),('courses B',2470,985,.07,1,213,12,17,52),('courses C',2770,966,.06,1,200,12,17,55)]:
 a=signal(x,y,dx,dy,l,sw);corr=np.correlate(a,a,'full')[l-1:];corr=corr/(np.arange(l,0,-1)*np.mean(a*a)); peaks=[i for i in find_peaks(corr[:mx],prominence=.05)[0]if i>=mn];pieces=[(p,round(float(corr[p]),2))for p in peaks]
 slices.append(dict(label=label,start=[x,y],direction=[dx,dy],samples=l,median_radius=sw,autocorrelation_maxima=pieces))
args.output.write_text(json.dumps(slices,indent=2,default=int)+'\n')
