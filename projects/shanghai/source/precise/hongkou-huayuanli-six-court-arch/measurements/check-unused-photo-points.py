"""Compare previously unused pixels on the arch soffit to vertical intersections with the actual raw/decoded GLBs."""
import argparse
import hashlib
import json
import runpy
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter1d

HERE=Path(__file__).absolute().parent
AUDIT=HERE.parents[3]/'data/audit'
SCENE=runpy.run_path(AUDIT/'central-reserve-bank-changshu-front-v1/verify-export.py')['Scene']
measure=runpy.run_path(HERE/'measure-photograph.py')
transform=measure['transform']


def check(image,meshes):
    record=json.loads((HERE/'plate-725.json').read_bytes())
    assert hashlib.sha256(image.read_bytes()).hexdigest()==record['photo_sha256']
    rgb=np.asarray(Image.open(image).convert('RGB'),dtype=float)
    sample=[]
    for x in range(280,581,20):
        rough=671+(x-420)**2*.00065
        strip=rgb[:,x-2:x+3].mean((1,2))
        diff=gaussian_filter1d(strip,1.8,order=1)
        bottom,top=int(rough-13),int(rough+14)
        y=bottom+int(np.argmin(diff[bottom:top]))
        assert diff[y]<-12
        sample.append([x,y])
    assert not set(p[0]for p in sample)&set(p[0]for p in record['arch_edge_pixels'])
    matrix=np.asarray(record['door_plane_homography'])
    projected=(transform(matrix,sample)-[0,1.5])*record['assumption']['porch_relative_scale']+[0,1.5]
    out={}
    for role,path in meshes.items():
        scene=SCENE(path);rows=[]
        for pixel,(x,z) in zip(sample,projected):
            hit=scene.ray([x,-.36,1.5],[0.,0.,1.],1.7)
            assert hit and hit['material']=='Buff lime finish'
            measured=float(hit['point_enu_m'][2])
            rows.append(dict(pixel=pixel,x_m=float(x),apparent_z_m=float(z),mesh_z_m=measured,difference_m=measured-float(z)))
        err=np.array([v['difference_m']for v in rows]);out[role]=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                samples=rows,rms_m=float(np.sqrt(np.mean(err**2))),maximum_m=float(np.max(abs(err))))
    bars=[]
    targets=np.array(record['median_horizontal_divider_heights_m'])
    for x in [357,376,482,503]:
        band=rgb[:,x-3:x+4].mean(1)
        red=gaussian_filter1d(band[:,0]-band[:,1],1.1)+.11*(band[:,0]-band[:,2])
        pixels=[[x,lo+int(np.argmax(red[lo:hi]))]for lo,hi in [(100,150),(183,232),(280,321)]]
        z=transform(matrix,pixels)[:,1]
        bars.append(dict(pixel=pixels,heights_m=z.tolist(),deviation_from_sash_rail_centres_m=(z-targets).tolist()))
    return dict(photo_sha256=record['photo_sha256'],calibration_sha256=hashlib.sha256((HERE/'plate-725.json').read_bytes()).hexdigest(),
                arch=out,sash=bars,sash_rms_m=float(np.sqrt(np.mean([np.square(v['deviation_from_sash_rail_centres_m'])for v in bars]))),
                scope='Reprojection comparison within a single image, using an assumed doorway scale. It does not establish construction accuracy or geographic placement.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for item in ('photo','raw','full','lod','out'):parser.add_argument(item,type=Path)
    args=parser.parse_args()
    report=check(args.photo,{role:getattr(args,role)for role in ('raw','full','lod')})
    args.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
