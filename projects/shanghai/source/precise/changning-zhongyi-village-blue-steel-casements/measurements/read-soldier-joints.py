"""Read the seventeen mortar positions across each window head from the licensed photograph."""
from pathlib import Path
import hashlib,json,runpy
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks

M=Path(__file__).absolute().parent
if __name__=='__main__':
    fit=runpy.run_path(M/'fit-windows.py');doc=json.loads((M/'primary-crop.json').read_bytes())
    reference=M/doc['file'];assert hashlib.sha256(reference.read_bytes()).hexdigest()==doc['sha256']
    pic=np.asarray(Image.open(reference).convert('RGB'),float)
    x=np.linspace(-4.02,1.12,900);z=np.linspace(2.08,-.41,440);xx,zz=np.meshgrid(x,z)
    pp=fit['G']@np.stack([xx.ravel(),zz.ravel(),np.ones(xx.size)]);u,v=pp[:2]/pp[2:]
    uv=[v-doc['crop_original_px'][1],u-doc['crop_original_px'][0]]
    pix=np.stack([map_coordinates(pic[:,:,c],uv,order=1,mode='nearest')for c in range(3)],axis=1).reshape(440,900,3)
    score=pix.mean(axis=2)-.5*(pix[:,:,0]-pix[:,:,2]);records=[]
    for role,b in [('open',fit['bounds']),('closed',[-fit['width']/2,0,fit['width']/2,1.55])]:
        l,_,r,top=b;along=(x>l-.06)&(x<r+.06);strip=score[(z>top+.04)&(z<top+.165)][:,along]
        row=np.median(strip,axis=0);edge=row-gaussian_filter1d(row,4.2)
        inds,detail=find_peaks(edge,distance=11,prominence=8.)
        assert len(inds)==17
        records.append(dict(bay=role,x_joints_m=np.round(x[along][inds],5).tolist(),prominences=np.round(detail['prominences'],2).tolist(),
            observed_units=len(inds)-1,strip_above_lintel_m=[.04,.165]))
    (M/'soldier-joints.json').write_text(json.dumps(dict(reference_crop_sha256=doc['sha256'],bays=records),ensure_ascii=False,indent=2)+'\n')
