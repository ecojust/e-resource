"""Check previously unused left-hand brick silhouette samples against raw and decoded mesh surfaces."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import numpy as np
from PIL import Image
from scipy.ndimage import map_coordinates, gaussian_filter1d

HERE=Path(__file__).absolute().parent
scene_type=runpy.run_path(HERE.parents[3]/'data/audit/central-reserve-bank-changshu-front-v1/verify-export.py')['Scene']


def samples(photo):
    source=json.loads((HERE/'signed-photograph.json').read_bytes())
    assert hashlib.sha256(photo.read_bytes()).hexdigest()==source['sha256']
    image=np.array(Image.open(photo).convert('RGB'),dtype=float)
    cam=json.loads((HERE/'camera-and-relative-dimensions.json').read_bytes())['result']
    R=np.array(cam['rotation_matrix']);origin=np.array(cam['translation']);f=cam['estimated_focal_px']
    center=np.array(cam['principal_point_px']);fixed=cam['front_plane_x_y_z_m']['side_of_upper_wall'][0]
    # Hue at the cream/brick boundary is less affected by mortar joints than brightness.
    y=np.linspace(.99,2.03,530);data=[]
    for z in [4.84,4.93,5.04,5.26,5.46,5.67,5.91,6.13,6.38,6.57,6.70,6.82,6.93]:
        xyz=np.column_stack([np.full(len(y),fixed),y,np.full(len(y),z-4.20)])
        v=xyz@R.T+origin
        pix=v[:,:2]/v[:,2:]*f+center
        rgb=np.stack([map_coordinates(image[:,:,k],[pix[:,1],pix[:,0]],order=1)for k in range(3)],axis=1)
        strength=(rgb[:,0]-rgb[:,1])/(rgb[:,0]+rgb[:,1]+1.)
        strength=gaussian_filter1d(strength,4.)
        threshold=.073
        # Demand a contiguous patch of face brick after the transition.
        runs=np.convolve((strength>threshold).astype(int),np.ones(18,dtype=int),'valid')
        indices=np.flatnonzero(runs>=17)
        if not len(indices):raise ValueError(('No source edge at elevation',z))
        i=int(indices[0]);data.append(dict(z_m=z,photo_y_m=round(float(y[i]),5),pixel=pix[i].round(3).tolist(),hue_threshold=threshold))
    return fixed,data


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for n in ['photograph','raw','full','lod','output']:ap.add_argument(n,type=Path)
    q=ap.parse_args();fixed,edges=samples(q.photograph);report={}
    for role in ['raw','full','lod']:
        p=getattr(q,role);scene=scene_type(p);rows=[]
        for obs in edges:
            start=.93;hit=scene.ray([fixed+.014,start,obs['z_m']],[0.,1.,0.],1.6)
            assert hit and hit['material']=='Light lime pointing',(obs,hit)
            value=hit['point_enu_m'][1];rows.append({**obs,'mesh_y_m':round(value,5),'difference_m':round(value-obs['photo_y_m'],5)})
        errors=np.array([v['difference_m']for v in rows])
        report[role]=dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),samples=rows,rms_m=round(float(np.sqrt(np.mean(errors**2))),5),max_abs_m=round(float(np.max(abs(errors))),5))
    q.output.write_text(json.dumps(dict(source_sha256=hashlib.sha256(q.photograph.read_bytes()).hexdigest(),method='Thirteen independent horizontal cuts through the projected side wall. A red/green transition in the original photograph is compared with a physical ray cast against the outer mortar surface. Results are conditional on the assumed main sash height and camera model.',models=report),ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
