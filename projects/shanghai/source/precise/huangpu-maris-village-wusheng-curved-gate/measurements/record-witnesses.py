"""Record points on the observed gilt strokes and black interiors of all four medallions."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt,map_coordinates

def farthest(mask,limit,spacing):
    depth=distance_transform_edt(mask)
    yy,xx=np.indices(depth.shape);points=[]
    for _ in range(limit):
        y,x=np.unravel_index(np.argmax(depth),depth.shape)
        if depth[y,x]<1.5:break
        points.append((x,y))
        depth[(xx-x)**2+(yy-y)**2<spacing*spacing]=0
    return points
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for field in ['source','registration','photo','trace','output']:ap.add_argument('--'+field,required=True,type=Path)
    args=ap.parse_args();sys.path.insert(0,str(args.source))
    from photo_plane import project,axes
    trace=runpy.run_path(args.trace);sz=trace['SIZE'];yy,xx=np.indices((sz,sz))
    inside=((xx+.5-sz/2)**2+(yy+.5-sz/2)**2)<(.385*sz)**2
    desc=json.loads(args.registration.read_bytes());station=desc['stations']['2020'];photo=Image.open(args.photo)
    points=[]
    for disc in desc['letters']:
        c=np.array(disc['centre_xz_m']);r=disc['radius_m']
        data=trace['sample'](photo,station['camera_xyz_yaw'],station,axes,c,r)
        density=trace['pigment'](data)
        for expected,region,limit,space in [('gilt',inside&(density>.73),8,15.),('black',inside&(density<.095),4,25.)]:
            for x,y in farthest(region,limit,space):
                normal=np.array([2*(x+.5)/sz-1,1-2*(y+.5)/sz])
                world=c+r*normal;coord=np.array([world[0],-.025,world[1]])
                pixels=trace['projection'](station['camera_xyz_yaw'],station,axes,coord)
                points.append(dict(letter=disc['character'],expected=expected,local_xz_m=world.round(6).tolist(),
                                   original_2020_crop=np.round(pixels,3).tolist(),detail_2021_px=project(coord).round(3).tolist(),source_rgb=np.rint(data[y,x]).astype(int).tolist()))
    info=dict(source='Baidu Maps public street imagery, Wusheng Road, 2020-02-22',station=station['id'],
              source_research_crop_sha256=hashlib.sha256(args.photo.read_bytes()).hexdigest(),points=points)
    args.output.write_text(json.dumps(info,ensure_ascii=False,indent=2)+'\n');print('points',len(points))
if __name__=='__main__':main()
