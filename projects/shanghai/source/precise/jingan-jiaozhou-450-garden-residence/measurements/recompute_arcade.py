"""Re-read the three brick arch curves from the two original, separately licensed garden photographs."""
import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.optimize import least_squares

HERE=Path(__file__).resolve().parent
def rectify(path,record,H):
    if sha256(path.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Input photograph differs from the cited original')
    im=np.array(Image.open(path).convert('RGB'))
    x,z=np.meshgrid(np.arange(-.24,16.1,1/105),np.arange(6.55,-.10,-1/105))
    pr=H@np.stack([x,z,np.ones_like(z)]).reshape(3,-1);u,v=(pr[:2]/pr[2]).reshape(2,*x.shape)
    pixels=np.stack([map_coordinates(im[:,:,k],(v,u),order=1,mode='constant',cval=225) for k in range(3)],axis=-1)
    # The original readings were made on this rectified 93-quality reference
    # export. Repeat that same stage locally; no reference photograph is saved.
    buf=BytesIO();Image.fromarray(pixels).save(buf,format='JPEG',quality=93);buf.seek(0)
    return np.array(Image.open(buf)).mean(2)
def curve(views,which,l,r):
    centre=(l+r)/2;radius=(r-l)/2;spring=2.465;rising=1.51
    hits=[];counts={}
    for key,im in views.items():
        collected=0
        for t in np.radians(np.arange(0.,180.01,2.)):
            if which==3 and (key=='8' or t<.62):continue
            rs=np.arange(.87,1.13,.0025)
            u=centre+radius*np.cos(t)*rs;v=spring+rising*np.sin(t)*rs
            profile=map_coordinates(im,((6.55-v)*105,(u+.24)*105),order=1)
            signal=np.gradient(gaussian_filter1d(profile,2));p=signal.argmax()
            if signal[p]>.88 and .885<rs[p]<1.118:hits.append((u[p],v[p]));collected+=1
        counts[key]=collected
    cells=np.array(hits)
    def distance(params):
        cx,sp,a,b=params
        return (np.sqrt(((cells[:,0]-cx)/a)**2+((cells[:,1]-sp)/b)**2)-1)*a
    final=least_squares(distance,[centre,spring,radius,rising],loss='soft_l1',f_scale=.012)
    return final.x,counts,float(np.median(abs(distance(final.x))))
def run(files):
    cams=json.loads((HERE/'arcade-cameras.json').read_text());sections=json.loads((HERE/'garden-arcade-sections.json').read_text())['arcades']
    views={key:rectify(path,cams['sources'][key],np.array(cams[key]['H'])) for key,path in files.items()}
    for i,(l,r) in enumerate([(.765,4.06),(4.865,8.065),(8.877,12.17)],1):
        ellipse,counts,residual=curve(views,i,l,r);src=sections[i-1]
        if not np.allclose(ellipse,src['ellipse'],atol=.002) or counts!=src['contour_measurements']:
            raise ValueError(f'Arch {i}: source reproduction differs: {ellipse}, {counts}')
        print(i,counts,ellipse.round(4).tolist(),round(residual,5))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('design13',type=Path);parser.add_argument('design8',type=Path)
    o=parser.parse_args();run({'13':o.design13,'8':o.design8})
