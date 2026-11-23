from pathlib import Path
import numpy as np,json
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
import argparse
ap=argparse.ArgumentParser(description='Measure median original-photo intensity across the registered front hip.')
ap.add_argument('original',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
s=Path(__file__).resolve().parent
d=json.load(open(s/'curved-veranda-folded-roof.json')); controls=d['controls']; a,b,c=np.asarray([controls[k] for k in ['front_fascia_left','front_fascia_right','ridge_end']]);P=np.array(d['stations']['sina-37']['P'])
im=np.asarray(Image.open(args.original).convert('L'));H,W=im.shape
image_c=np.asarray(Image.open(args.original).convert('RGB'))
ss=np.linspace(-.82,.82,161);ts=np.linspace(0,1,341);series=[];colour=[]
for t in ts:
 y=(1-t)*((a+b)/2+(b-a)[None,:]*ss[:,None]/2)+t*c
 pix=np.c_[y,np.ones(len(y))]@P.T; pix=pix[:,:2]/pix[:,2:]
 uv=np.vstack([pix[:,1]*H/459,pix[:,0]*W/690])
 series.append(np.median(map_coordinates(im,uv,order=1)))
 colour.append([np.median(map_coordinates(image_c[...,k],uv,order=1)) for k in range(3)])
raw=np.array(series);v=gaussian_filter1d(raw,2);pk=find_peaks(-v,prominence=4,distance=18)[0]
print('minima',list(zip(ts[pk].round(3),v[pk].round(1)))); print('peaks:',ts[find_peaks(v,prominence=5,distance=18)[0]].round(3))
ds={'reference':'sina large-37.jpg 4912×3264, 2018-02-27','sha256':__import__('hashlib').sha256((args.original).read_bytes()).hexdigest(),'coordinate':'Fraction along the front hip, from lowest continuous tile edge (0) to upper termination (1); median brightness across the middle 82 percent of each available row.','interior_joint_samples':[{'fraction':round(float(ts[k]),4),'grey':float(v[k])} for k in pk], 'profile_step':round(1/340,7),'median_grey_lows_to_highs':[[int(t)for t in r] for r in colour[::5]]}
args.output.write_text(json.dumps(ds,indent=2)+'\n')
