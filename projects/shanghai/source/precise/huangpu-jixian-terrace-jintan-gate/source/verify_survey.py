"""Recompute the two-station survey. Optionally reconstruct the photographed perspective views."""
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from io import BytesIO
import json
import math
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = np.array([121.493365, 31.221174])
SCALE = np.array([111195 * math.cos(math.radians(ORIGIN[1])), 111195])
STATIONS = {
    '0': ('09000300121905171434465709U', 10),
    '4': ('09000300121905171434484809U', 9),
}
WIDTH, HEIGHT, HORIZONTAL_FOV = 450, 325, 95


def camera(meta, pitch):
    center = (np.array(meta['camera_wgs84']) - ORIGIN) * SCALE
    yaw = math.atan2(-center[0], -center[1])
    theta = math.radians(pitch)
    forward = np.array([math.sin(yaw), math.cos(yaw), 0])
    right = np.array([math.cos(yaw), -math.sin(yaw), 0])
    vertical = np.array([0., 0., 1.])
    return np.r_[center, 2.30], (right, math.cos(theta)*forward+math.sin(theta)*vertical,
                                  math.cos(theta)*vertical-math.sin(theta)*forward)


def rays(frame, pixels):
    right, forward, up = frame
    focal = WIDTH / (2 * math.tan(math.radians(HORIZONTAL_FOV / 2)))
    u, v = np.asarray(pixels).T
    return ((u-WIDTH/2)[...,None]*right + focal*forward + (HEIGHT/2-v)[...,None]*up)


def photograph(meta, frame, out):
    from PIL import Image
    from scipy.ndimage import map_coordinates

    def fetch(item):
        url = item['url']
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://map.baidu.com/'}),timeout=35) as response:
            data = response.read()
        assert sha256(data).hexdigest() == item['sha256'] and len(data) == item['bytes']
        from urllib.parse import parse_qs, urlparse
        row, col = map(int,parse_qs(urlparse(url).query)['pos'][0].split('_'))
        return col,row,Image.open(BytesIO(data)).convert('RGB')

    sphere = Image.new('RGB',(4096,2048))
    with ThreadPoolExecutor(4) as pool:
        for col,row,image in pool.map(fetch,meta['tiles']):
            sphere.paste(image,(512*col,512*row))
    x,y=np.meshgrid(np.arange(WIDTH),np.arange(HEIGHT))
    vectors=rays(frame,np.c_[x.ravel(),y.ravel()]).reshape(HEIGHT,WIDTH,3)
    yaw=np.degrees(np.arctan2(vectors[:,:,0],vectors[:,:,1]))
    pitch=np.arctan2(vectors[:,:,2],np.hypot(vectors[:,:,0],vectors[:,:,1]))
    u=(yaw-meta['heading_azimuth']-90)%360 * 4096/360
    v=1024-pitch*(4096/(2*np.pi))
    arr=np.asarray(sphere)
    view=np.stack([map_coordinates(arr[:,:,i],[v,u],order=1,mode='wrap')for i in range(3)],axis=2)
    Image.fromarray(view).save(out,quality=92)


def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument('--images',type=Path,help='Fetch both photographed panoramas and write the perspective views here.')
    args=parser.parse_args()
    registry=json.loads((ROOT/'reference-review.json').read_bytes())
    source=json.loads((ROOT/'street-registration.json').read_bytes())
    index={s['station']:s for s in registry['street_panoramas']}
    cameras={}
    for label,(station,pitch) in STATIONS.items():
        origin,frame=camera(index[station],pitch)
        cameras[label]=(origin,frame)
        if args.images:
            args.images.mkdir(exist_ok=True,parents=True)
            photograph(index[station],frame,args.images/(station+'.jpg'))
    results={}
    for label,trial in source['pixels'].items():
        weighted=[]
        for station,pixel in trial['pixels'].items():
            origin,frame=cameras[station];direction=rays(frame,pixel)
            direction/=np.linalg.norm(direction)
            weighted.append((origin,np.eye(3)-np.outer(direction,direction)))
        point=np.linalg.lstsq(sum(w for _,w in weighted),sum(w@o for o,w in weighted),rcond=None)[0]
        misses=[float(np.linalg.norm(w@(point-o)))for o,w in weighted]
        assert np.allclose(point,trial['xy_z'],atol=1e-8) and np.allclose(misses,trial['miss_m'],atol=1e-8)
        results[label]={'local_m':point.tolist(),'wgs84':(ORIGIN+point[:2]/SCALE).tolist(),'residual_m':misses}
    print(json.dumps(results,indent=2))


if __name__=='__main__':
    main()
