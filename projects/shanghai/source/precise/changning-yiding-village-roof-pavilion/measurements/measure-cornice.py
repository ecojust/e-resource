from pathlib import Path
import numpy as np,json
from PIL import Image
from scipy.ndimage import map_coordinates,gaussian_filter1d
from scipy.signal import find_peaks
root=Path(__file__).absolute().parent.parent
m=root/'measurements';img=np.asarray(Image.open(m/'antigng-roof-room.jpg').convert('RGB'),float)
cam=json.loads((m/'roof-room-camera.json').read_bytes());P=np.array(cam['world_to_crop']);d=cam['photographed_dimensions']
w=Path(__file__).parent
def rectify(xs,zs,side=False):
 x,z=np.meshgrid(xs,zs);xyz=np.stack([0*x if side else x, x if side else x*0,z,np.ones(x.shape)],axis=-1)
 uv=xyz@P.T;uv=(uv[:,:,:2]/uv[:,:,2,None]).reshape(-1,2);return np.stack([map_coordinates(img[:,:,c],uv[:,::-1].T,order=1,mode='nearest')for c in range(3)],axis=1).reshape(*x.shape,3)

def course(side,band):
    h=d['roof_level'];start,stop=(.04,d['return_depth']-.10)if side else(-d['front_width']+.015,-.015)
    xs=np.linspace(start,stop,1651);zs=np.linspace(h-band[1],h-band[0],15)
    pixels=rectify(xs,zs,side)
    brightness=np.median(pixels@np.array([.28,.55,.17]),axis=0)
    dx=xs[1]-xs[0]
    bright=gaussian_filter1d(brightness,.005/dx)-gaussian_filter1d(brightness,.038/dx)
    peaks,stats=find_peaks(bright,distance=int(.065/dx),prominence=11)
    typical=np.diff(xs[peaks]);regular=typical[(typical>.072)&(typical<.117)]
    return dict(strip_below_roof_m=band,visible_pale_centres_m=np.round(xs[peaks],5).tolist(),
                regular_differences_m=np.round(regular,5).tolist(),median_period_m=float(np.median(regular)))
if __name__=='__main__':
    rows=[course(False,b)for b in [[.035,.079],[.242,.302]]]
    assert all(len(r['regular_differences_m'])>42 for r in rows)
    info=dict(photo_sha256=cam['photo_sha256'],crop_sha256=cam['source_crop_sha256'],front_rows=rows,
              side_observation='侧返两列红带可见，树阴与侧向透视削弱了浅色刻线；侧面的实体砖缝沿用前檐中位节距。')
    (m/'double-cornice-rhythm.json').write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n')
    print([(len(r['visible_pale_centres_m']),len(r['regular_differences_m']),r['median_period_m'])for r in rows])
