"""Locate the tile joints of the entrance planter in the registered 2015 street view."""
import argparse,json
from hashlib import sha256
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from PIL import Image

def measure(observations,image):
    o=json.loads(observations.read_bytes())
    assert sha256(image.read_bytes()).hexdigest()==o['input_sha256']
    grey=np.asarray(Image.open(image).convert('L'),float)
    top=np.array(o['top_uv']);bottom=np.array(o['bottom_uv'])
    xx=np.arange(290,421);a=np.interp(xx,top[:,0],top[:,1]);b=np.interp(xx,bottom[:,0],bottom[:,1])
    q=np.linspace(.06,.93,45)
    values=np.stack([grey[np.rint(a+(b-a)*v).astype(int),xx]for v in q])
    column=values.mean(axis=0);peaks=find_peaks(gaussian_filter1d(column,2)-column,height=.7,prominence=1.6,distance=3)[0]
    narrow=np.median(values[:,24:83],axis=1)
    c=find_peaks(gaussian_filter1d(narrow,2.4)-narrow,distance=6,prominence=3.)[0]
    return dict(source_sha256=o['input_sha256'],view=o['view'],vertical_joint_u_px=xx[peaks].tolist(),horizontal_troughs_down_face=q[c].round(4).tolist(),
                note='Vertical mortar readings are from the 2015 street center image. The far return near the pier is strongly foreshortened. At its end the model stops at the last identifiable full tile.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('photograph',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    r=measure(Path(__file__).with_name('entrance-planter-2015.json'),a.photograph);a.output.write_text(json.dumps(r,indent=2)+'\n')
