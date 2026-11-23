"""Render the delivered GLB in four observed camera frames, preserving obliqueness, camera roll and time of day."""
import argparse
import ctypes
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch
import numpy as np
from PIL import Image, ImageDraw
from register_court import Camera

HERE=Path(__file__).absolute().parent
PRECISE=HERE.parents[1]
from sky_sampling import sky_maps, SAMPLES, DEPTH_RESOLUTION
sys.path.insert(0,str(PRECISE/'huangpu-yuanmingyuan-apartments-street-front/measurements'))
backend=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
VIEWS={'commons':('2015-02-07T13:38:39','Fayhoo | 7 Feb 2015'),
       '05':('2018-09-09T16:33:22','Courtyard | 9 Sep 2018'),
       '10':('2016-01-09T13:57:50','Courtyard | 9 Jan 2016'),
       '06':('2018-09-09T16:33:37','Entrance | 9 Sep 2018')}
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def photo_camera(name):
    if name!='06':
        c=Camera(name);return c.projection(),c.size
    m=json.loads((HERE/'entrance-cameras.json').read_bytes())['close_view']
    r,k,c=[np.asarray(m[n]) for n in ('R','K','C')]
    return k@r@np.column_stack((np.eye(3),-c)),tuple(m['size'])
def daylight(stamp):
    date=dt.datetime.fromisoformat(stamp);hour=date.hour+date.minute/60+date.second/3600
    lat,lon=math.radians(31.215),121.457
    phase=2*np.pi/365*(date.timetuple().tm_yday-1+(hour-12)/24)
    e=229.18*(.000075+.001868*np.cos(phase)-.032077*np.sin(phase)-.014615*np.cos(2*phase)-.040849*np.sin(2*phase))
    dec=.006918-.399912*np.cos(phase)+.070257*np.sin(phase)-.006758*np.cos(2*phase)+.000907*np.sin(2*phase)-.002697*np.cos(3*phase)+.00148*np.sin(3*phase)
    ha=np.radians((60*hour+e+4*lon-480)/4-180)
    east=-np.cos(dec)*np.sin(ha);north=np.sin(dec)*np.cos(lat)-np.cos(dec)*np.cos(ha)*np.sin(lat)
    z=np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.cos(ha)
    a=np.radians(73.2);local=[east*np.sin(a)+north*np.cos(a),-east*np.cos(a)+north*np.sin(a),z]
    return np.ascontiguousarray(local,dtype='float32'),[round(np.degrees(np.arctan2(east,north))%360,2),round(np.degrees(np.arcsin(z)),2)]
def render(mesh,output,width=680):
    output.mkdir(parents=True,exist_ok=True);renderer=backend['renderer'];data=renderer.read_glb(mesh);report={};thumbs=[]
    with tempfile.TemporaryDirectory() as tmp:
        so=Path(tmp)/'photograph.so';source=HERE/'entrance_daylight.c'
        subprocess.run(['cc','-O2','-std=c99','-shared','-fPIC',str(source),'-lm','-o',str(so)],check=True)
        lib=ctypes.CDLL(str(so))
        for idx,mat in enumerate(data[1]):
            if 'emissiveFactor' in mat:
                lib.set_globe(idx,*[ctypes.c_float(v) for v in mat['emissiveFactor']])
        trans,dirs,depths=sky_maps(data[0],lib,renderer)
        lib.set_sky(SAMPLES,DEPTH_RESOLUTION,renderer.ptr(trans),renderer.ptr(dirs),renderer.ptr(depths))
        for key,(time,label) in VIEWS.items():
            projection,size=photo_camera(key);sw,sh=size
            pixels=round(width*.70) if key=='06' else width
            spacing=sw/pixels
            sky=np.full((round(sh/spacing),pixels),-1,dtype='float32')
            inv=np.linalg.inv(projection[:,:3]);inverse=np.ascontiguousarray(np.column_stack((inv,-inv@projection[:,3])),dtype='float32')
            sun,angles=daylight(time)
            lib.set_photo(renderer.ptr(inverse),ctypes.c_float(spacing),1,renderer.ptr(sky))
            clipped=backend['projected_parts'](data,projection)
            with patch.object(renderer,'read_glb',return_value=clipped):
                picture,stats=renderer.raster(mesh,lib,pixels,projection,(0,0,*size),sun,angles)
            fg=sky[sky>=0]
            if len(fg)!=stats['zbuffer_foreground_pixels']:raise ValueError('Depth and sky coverage disagree')
            f=output/('view-'+key+'.jpg');picture.save(f,quality=92,optimize=True)
            stats.update(photo_exif_local=time,model_sha256=sha(mesh),image_sha256=sha(f),solar_azimuth_elevation_deg=angles,
                         source_sha256=sha(source),sky_directions=SAMPLES,sky_depth_side_px=DEPTH_RESOLUTION,
                         sky_fraction_quantiles=np.quantile(fg,[.1,.5,.9]).tolist(),camera=projection.tolist())
            report[key]=stats
            tile=picture.convert('RGB');tile.thumbnail((390,267));thumbs.append((tile,label))
    sheet=Image.new('RGB',(788,596),'#f6f4ee');draw=ImageDraw.Draw(sheet)
    for i,(tile,label) in enumerate(thumbs):
        a=(i%2)*396;b=(i//2)*298
        sheet.paste(tile,(a+(390-tile.width)//2,b));draw.text((a+7,b+274),label,fill='#342f29')
    sheet.save(output/'courtyard-and-entrance.jpg',quality=94)
    (output/'four-photograph-renders.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);p.add_argument('--width',type=int,default=680)
    args=p.parse_args();render(args.mesh,args.output,args.width)
