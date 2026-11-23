"""Render the distributed GLB in the measured photograph cameras, retaining perspective-correct texture UVs."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import patch

import numpy as np

HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
sys.path.insert(0,str(PRECISE/'huangpu-yuanmingyuan-apartments-street-front/measurements'))
import photo_glb_raster as renderer


def projected_parts(data,camera):
    """Clip triangles that cross the camera plane, including the courtyard path under the eye."""
    parts,materials,textures=data
    result=[]
    for pos,normal,uv,indices,mi,ti in parts:
        depth=pos@camera[2,:3]+camera[2,3]
        faces=indices.reshape(-1,3);front=depth[faces]>=.10
        if front.all():
            result.append((pos,normal,uv,indices,mi,ti));continue
        kept=faces[front.all(axis=1)]
        crossing=faces[front.any(axis=1)&~front.all(axis=1)]
        if not len(kept) and not len(crossing):continue
        attrs=np.column_stack((pos,normal,uv))
        triangles=[attrs[kept].reshape(-1,8)]
        for indices3 in crossing:
            poly=[]
            for prev,nxt in zip(np.roll(indices3,1),indices3):
                d0,d1=depth[[prev,nxt]]
                if (d0>=.1)!=(d1>=.1):
                    t=(.10-d0)/(d1-d0);poly.append(attrs[prev]+t*(attrs[nxt]-attrs[prev]))
                if d1>=.10:poly.append(attrs[nxt])
            triangles.extend([np.asarray((poly[0],poly[j],poly[j+1])) for j in range(1,len(poly)-1)])
        vertices=np.concatenate(triangles)
        pack=lambda a:np.ascontiguousarray(a,dtype=np.float32)
        result.append((pack(vertices[:,:3]),pack(vertices[:,3:6]),pack(vertices[:,6:8]),
                       np.arange(len(vertices),dtype=np.uint32),mi,ti))
    return result,materials,textures


def stations():
    read=lambda name:json.loads((HERE/name).read_bytes())
    layout=json.loads((HERE.parent/'source/garden-layout.json').read_bytes())
    survey=read('six-front-cameras.json')
    north=read('nine-north-windows-and-stepped-gables.json')['views']
    south=read('nine-south-gables-two-oblique-views.json')['registered_sources']
    cafes=read('house-eight-entrance-observations.json')['views']
    entries=[('8-lawn',8,read('courtyard-front-station.json')['house8_to_upright_pixel_camera'],[260,173,1024,660]),
             ('8-north-door',8,cafes['winter2023-08']['P'],[4,39,658,817]),
             ('9-lawn',9,survey['houses']['9']['views']['winter2023-14']['world_to_upright_pixel_camera'],[223,208,855,612]),
             ('9-south-gables',9,south['winter2023-16']['P'],[62,110,856,622]),
             ('9-north-gables',9,north['20']['P'],[163,4,907,548])]
    for name,n,p,crop in entries:
        frame=layout[str(n)]['garden_transform'];m=np.eye(4)
        m[:2,0]=frame['local_X_unit_EN'];m[:2,1]=frame['local_Y_unit_EN'];m[:2,3]=frame['left_wall_projection']['garden_ENU_m']
        yield name,n,np.array(p)@np.linalg.inv(m),crop


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('glb',type=Path);ap.add_argument('output',type=Path)
    ap.add_argument('--pixels',type=int,default=960);args=ap.parse_args();args.output.mkdir(exist_ok=True,parents=True)
    data=renderer.read_glb(args.glb);reports={}
    with tempfile.TemporaryDirectory()as tmp:
        library=Path(tmp)/'depth-raster.so'
        source=PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(source),'-lm','-o',str(library)],check=True)
        lib=ctypes.CDLL(str(library))
        for name,n,p,crop in stations():
            sun=np.array([-.62 if n==8 else .62,-.35,.70],dtype='float32');sun/=np.linalg.norm(sun)
            angles=[float(np.rad2deg(np.arctan2(sun[0],sun[1]))%360),float(np.rad2deg(np.arcsin(sun[2])))]
            clipped=projected_parts(data,p)
            with patch.object(renderer,'read_glb',return_value=clipped):
                im,note=renderer.raster(args.glb,lib,args.pixels,p,crop,sun,angles)
            path=args.output/(name+'.jpg');im.save(path,quality=92,subsampling=0,optimize=True)
            reports[name]={**note,'file':path.name,'sha256':hashlib.file_digest(path.open('rb'),'sha256').hexdigest()}
    report={'glb_sha256':hashlib.file_digest(args.glb.open('rb'),'sha256').hexdigest(),
            'method':'New model-only views from five registered cameras. Z-buffer, shadow map, perspective-correct UVs and embedded textures. Triangles cross-clipped at 0.10 m. Photograph backgrounds are omitted.','views':reports}
    (args.output/'camera-render-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
