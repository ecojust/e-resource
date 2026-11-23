from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter1d
from scipy.signal import find_peaks
import numpy as np,json
from pathlib import Path
s=Path(__file__).resolve().parent
import argparse, hashlib
parser=argparse.ArgumentParser(); parser.add_argument('original_gao_08',type=Path); input_file=parser.parse_args().original_gao_08
data=json.loads((s/'house-three-two-registered-views.json').read_text());P=np.array(data['stations'][0]['native_P'])
assert hashlib.sha256(input_file.read_bytes()).hexdigest()==data['stations'][0]['source']['sha256']
im=np.array(Image.open(input_file).convert('L'),dtype=np.float32);z=np.linspace(.58,2.30,1721)
res=[]
for u0 in (-1.03,.78,.91,1.04):
 u,t=np.meshgrid(np.linspace(u0-.045,u0+.045,9),z);X=np.vstack([u.ravel(),u.ravel()*0,t.ravel(),u.ravel()*0+1]);p=P@X
 intensity=map_coordinates(im,[p[1]/p[2],p[0]/p[2]],order=1).reshape(len(z),-1).mean(1)
 vals=intensity-gaussian_filter1d(intensity,12)
 corr=np.correlate(vals,vals,mode='full')[len(vals)-1:];peaks,_=find_peaks(corr[40:90]);best=sorted([(round(corr[40+j]/corr[0],3),int(40+j)) for j in peaks],reverse=True)[:3]
 print(u0,best);res.append({'u_m':u0,'sample_z_m':[.58,2.30],'autocorrelation_peaks':[{'lag_m':lag/1000,'normalized':float(score)} for score,lag in best]})
(s/'house-three-brick-courses.json').write_text(json.dumps({'source_sha256':data['stations'][0]['source']['sha256'],'description':'Nine vertical probes traverse the Gao 2013 red brick panel over a 90mm width. Bilinear original-resolution samples, 1mm Z increments, local mean removed. Strongest recurring horizontal mortar pitch on the assumed metre scale. A physical survey remains unavailable.','samples':res},indent=2)+'\n')
