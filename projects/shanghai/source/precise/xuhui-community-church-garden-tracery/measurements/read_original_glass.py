from pathlib import Path
from PIL import Image
import numpy as np,json
from scipy.ndimage import gaussian_filter,maximum_filter
import argparse
parser=argparse.ArgumentParser(description='Read numeric materials and lead spacing from the original Fayhoo photograph.')
parser.add_argument('fayhoo_photo',type=Path)
parser.add_argument('--output',type=Path)
args=parser.parse_args()
S=Path(__file__).resolve().parent
im=Image.open(args.fayhoo_photo);w=im.width/687
samples={}
for name,patches in [('Community Church | weathered russet brick',[(327,89,340,97),(370,87,381,96),(279,151,286,162)]),('Community Church | buff window stone',[(290,208,295,231),(414,210,419,232),(345,151,347,161)])]:
 samples[name]=[]
 for x0,y0,x1,y1 in patches:
  x0,y0,x1,y1=[round(q*w)for q in [x0,y0,x1,y1]];samples[name].append({'photo':'fayhoo2017','rectangle':[x0,y0,x1,y1],'median_srgb':np.median(np.asarray(im.crop((x0,y0,x1,y1)).convert('RGB')).reshape(-1,3),axis=0).tolist()})
j0,j1,i0,i1=[round(q*w)for q in [208,256,348.3,362.2]];patch=np.asarray(im.crop((i0,j0,i1,j1)).convert('L'),float);im.close()
d=(patch-gaussian_filter(patch,8))*np.hanning(patch.shape[0])[:,None]*np.hanning(patch.shape[1])[None,:];spectrum=np.abs(np.fft.fft2(d,(512,512)));fx,fy=np.meshgrid(np.fft.fftfreq(512),np.fft.fftfreq(512))
freqs=[]
for direction in [1,-1]:
 usable=(fx*direction>.018)&(fx*direction<.082)&(fy>.012)&(fy<.066)&(spectrum==maximum_filter(spectrum,7));i=np.argmax(spectrum[usable]);freqs.append([float(fx[usable][i]),float(fy[usable][i])])
book=json.loads((S/'church-registration.json').read_bytes());c=book['stations']['fayhoo2017'];k,r,C=[np.array(c[q])for q in ['K','R','C']];y=book['parameters']['window_plane_y'];x0,y0=(i0+i1)/2,(j0+j1)/2
def wall(x,y_image):
 ray=r.T@np.linalg.solve(k,[x,y_image,1]);return C+(y-C[1])/ray[1]*ray
period_u=np.median([abs(wall(x0+1/abs(f[0]),y0)[0]-wall(x0,y0)[0])for f in freqs]);period_v=np.median([abs(wall(x0,y0+1/abs(f[1]))[2]-wall(x0,y0)[2])for f in freqs])
out={'finish_samples':samples,'diamond_lead':{'photo':'fayhoo2017','native_px_crop':[i0,j0,i1,j1],'working_resample':False,'fft_pad':512,'frequency_pairs_per_pixel':freqs,'periods_m':[period_u,period_v],'notes':'Two opposite directions in the high-pass Hann-windowed field. Geometry uses their median absolute periods at the fitted window plane; dead straight reinforcing bars are measured separately.'},'independent_inside':{k:v for k,v in json.loads((S/'source-and-address.json').read_bytes())['interior_crosscheck'].items()if k in ['page','image','sha256','licenses','dimensions']}}
(args.output or S/'brick-stone-and-diamond-measurements.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
