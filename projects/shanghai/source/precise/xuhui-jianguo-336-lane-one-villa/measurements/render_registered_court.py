"""Render the delivered villa from four registered photographic stations.

The input images are embedded glTF materials. Photographs only supply measured
camera matrices and, for two stations, the exposure time used for the sun.
"""
import argparse
import ctypes
import datetime
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
from register_court import Camera

HERE = Path(__file__).absolute().parent
PRECISE = HERE.parents[1]
DAYLIGHT = PRECISE / 'xuhui-yuqing-80-twin-winter-gardens/measurements/garden_daylight.c'
sys.path.insert(0, str(PRECISE / 'xuhui-shaanxi-202-former-yihe-hospital/measurements'))
from sky_sampling import sky_maps, SAMPLES, DEPTH_RESOLUTION
BACKEND = runpy.run_path(str(PRECISE / 'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
RASTER = BACKEND['renderer']
STATIONS = {
    '03': ('Garden elevation','', 'https://s15.sinaimg.cn/orignal/001HIrzOzy7MmCNvSJsb2'),
    '04': ('West corner', '2013-12-07T13:41:58', 'https://s10.sinaimg.cn/orignal/001HIrzOgy6EOgj6EY1a9'),
    '05': ('Entrance stairs', '', 'https://s2.sinaimg.cn/orignal/5d1bdf48gx6DgReH1wB51'),
    '02': ('West wing across the gate', '2013-12-07T13:42:43', 'https://s15.sinaimg.cn/orignal/001HIrzOgy6EOgp15sW1e')
}
def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def camera(key):
    if key != '02':
        c = Camera(key)
        return c.projection(), c.size
    c = json.loads((HERE/'west-photo02-camera.json').read_bytes())
    k,r,eye = [np.array(c[f]) for f in ('K','R','C')]
    return k @ r @ np.column_stack((np.eye(3), -eye)), tuple(c['working_size'])

def sunlight(stamp):
    if not stamp:
        return np.array([0., -.8, .6], dtype='float32'), None
    date = datetime.datetime.fromisoformat(stamp)
    hour = date.hour + date.minute/60 + date.second/3600
    lat, lon = np.radians(31.205), 121.462
    g = 2*np.pi/365*(date.timetuple().tm_yday-1+(hour-12)/24)
    eq = 229.18*(.000075+.001868*np.cos(g)-.032077*np.sin(g)-.014615*np.cos(2*g)-.040849*np.sin(2*g))
    dec = .006918-.399912*np.cos(g)+.070257*np.sin(g)-.006758*np.cos(2*g)+.000907*np.sin(2*g)-.002697*np.cos(3*g)+.00148*np.sin(3*g)
    ha = np.radians((60*hour+eq+4*lon-480)/4-180)
    east = -np.cos(dec)*np.sin(ha)
    north = np.sin(dec)*np.cos(lat)-np.cos(dec)*np.cos(ha)*np.sin(lat)
    up = np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.cos(ha)
    axis = np.radians(72.)
    vector = [east*np.sin(axis)+north*np.cos(axis), -east*np.cos(axis)+north*np.sin(axis), up]
    return np.array(vector,dtype='float32'), [round(np.degrees(np.arctan2(east,north))%360,2),round(np.degrees(np.arcsin(up)),2)]

def make_library(tmp):
    base = DAYLIGHT.read_text()
    hooks = {
        'al*daylight+reflect,0,1':'al*daylight+reflect+emissive[ch],0,1',
        'void paint(': '#include "court_normal_map.h"\nvoid paint(',
        'if(fabsf(D)<1.e-7f||a[2]<=0||b[2]<=0||c[2]<=0)continue;':
            'if(fabsf(D)<1.e-7f||a[2]<=0||b[2]<=0||c[2]<=0)continue;\n   float basis[6]; int mapped=tangent_frame(a,b,c,basis);',
        'float dl=fmaxf(0,nx*sun[0]+ny*sun[1]+nz*sun[2]),vis=0;':
            'if(mapped)perturb(attr[3],attr[4],basis,&nx,&ny,&nz);\n   float dl=fmaxf(0,nx*sun[0]+ny*sun[1]+nz*sun[2]),vis=0;'
    }
    for old,new in hooks.items():
        if base.count(old)!=1:
            raise ValueError('Daylight raster interface changed: '+old)
        base=base.replace(old,new)
    src=tmp/'complete.c'
    src.write_text(base)
    so=tmp/'court.so'
    subprocess.run(['cc','-O2','-std=c99','-shared','-fPIC','-I',str(HERE),str(src),'-lm','-o',str(so)],check=True,env={**os.environ,'TMPDIR':str(tmp)})
    if hasattr(os,'memfd_create'):
        fd=os.memfd_create('court-daylight')
        try:
            os.write(fd,so.read_bytes())
            return ctypes.CDLL('/proc/self/fd/'+str(fd))
        finally:
            os.close(fd)
    return ctypes.CDLL(str(so))

class MaterialPass:
    def __init__(self, lib, materials, textures):
        self.lib=lib
        self.materials=materials
        self.textures=textures
        self.shadow_depth=lib.shadow_depth
        self.active=True

    def paint(self,*args):
        m=self.materials[args[8]]
        self.lib.set_emission(*[ctypes.c_float(v) for v in m.get('emissiveFactor',[0,0,0])])
        if self.active and 'normalTexture' in m:
            ref=m['normalTexture']
            assert ref.get('texCoord',0)==0
            img,wu,wv,_=self.textures[ref['index']]
            self.lib.set_normal_map(RASTER.ptr(img), img.shape[1], img.shape[0],wu,wv,ctypes.c_float(ref.get('scale',1.)))
        else:
            self.lib.set_normal_map(None,0,0,0,0,ctypes.c_float(0.))
        self.lib.paint(*args)

def render(mesh,out,width):
    out.mkdir(exist_ok=True,parents=True)
    data=RASTER.read_glb(mesh)
    note={'model_sha256':sha(mesh),'shared_daylight_sha256':sha(DAYLIGHT),'normal_map_shader_sha256':sha(HERE/'court_normal_map.h'),
          'camera_files':{n:sha(HERE/n) for n in ('court-cameras.json','west-photo02-camera.json')},'views':{}}
    thumbs=[]
    with tempfile.TemporaryDirectory(dir=out) as temp:
        lib=make_library(Path(temp))
        painter=MaterialPass(lib,data[1],data[2])
        trans,dirs,depths=sky_maps(data[0],lib,RASTER)
        lib.set_sky(SAMPLES,DEPTH_RESOLUTION,RASTER.ptr(trans),RASTER.ptr(dirs),RASTER.ptr(depths))
        for key,(label,time,url) in STATIONS.items():
            proj,size=camera(key)
            pixels=min(width,round(width*size[0]/size[1])) if size[1]>size[0] else width
            spacing=size[0]/pixels
            field=np.full((round(size[1]/spacing),pixels),-1.,'float32')
            inv=np.linalg.inv(proj[:,:3])
            back=np.ascontiguousarray(np.column_stack((inv,-inv@proj[:,3])),dtype='float32')
            sun,angles=sunlight(time)
            lib.set_photo(RASTER.ptr(back),ctypes.c_float(spacing),bool(time),RASTER.ptr(field))
            clipped=BACKEND['projected_parts'](data,proj)
            with patch.object(RASTER,'read_glb',return_value=clipped):
                painter.active=True
                image,stats=RASTER.raster(mesh,painter,pixels,proj,(0,0,*size),sun,angles)
                painter.active=False
                flat,_=RASTER.raster(mesh,painter,pixels,proj,(0,0,*size),sun,angles)
            target=out/('view-'+key+'.jpg')
            image.save(target,quality=94,subsampling=0,optimize=True)
            diff=np.abs(np.array(image,dtype='int16')-np.array(flat,dtype='int16'))
            stats.update(source_url=url,source_time_local=time or None,solar_azimuth_altitude_deg=angles,
                         diffuse_sky_directions=SAMPLES,sky_depth_resolution=DEPTH_RESOLUTION,
                         normal_mapping_difference_pixels=int(np.count_nonzero(np.max(diff,axis=2))),max_normal_map_channel_delta=int(diff.max()),
                         normal_materials_visible=[m['name'] for m in data[1] if 'normalTexture' in m and m['name'] in stats['materials_visible_samples']],
                         photo_pixel_frame=list(size),projection=proj.tolist(),file=target.name,sha256=sha(target))
            assert stats['normal_mapping_difference_pixels']>0 and stats['zbuffer_foreground_pixels']>100
            note['views'][key]=stats
            tile=image.copy();tile.thumbnail((413,290))
            thumbs.append((tile,key+'   '+label))
    sheet=Image.new('RGB',(860,676),'#f3f1eb')
    draw=ImageDraw.Draw(sheet)
    for i,(tile,label) in enumerate(thumbs):
        x=(i%2)*430;y=(i//2)*338
        sheet.paste(tile,(x+(430-tile.width)//2,y+(299-tile.height)//2+5))
        draw.text((x+12,y+307),label,fill='#39362c')
    name=out/'registered-courtyard.jpg';sheet.save(name,quality=94,subsampling=0)
    note['sheet']={'file':name.name,'sha256':sha(name)}
    (out/'registered-renders.json').write_text(json.dumps(note,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('glb',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--width',type=int,default=790)
    args=parser.parse_args()
    render(args.glb,args.output,args.width)
