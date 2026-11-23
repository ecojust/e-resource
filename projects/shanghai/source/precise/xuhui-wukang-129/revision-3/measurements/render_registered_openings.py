"""Render both reference stations and matched V2/V3 details from real GLB surfaces.

Only GLB materials enter the frames. The two original Commons photographs
supply the camera and an EXIF clock reading; both remain separately credited.
"""
import argparse
import ctypes
from datetime import datetime
import hashlib
import json
from pathlib import Path
import runpy
import sys
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw

from register_openings import Camera

HERE = Path(__file__).absolute().parent
PRECISE = HERE.parents[2]
VILLA = PRECISE / 'xuhui-jianguo-336-lane-one-villa/measurements'
sys.path.insert(0, str(VILLA))
ENGINE = runpy.run_path(str(VILLA / 'render_registered_court.py'))
RASTER = ENGINE['RASTER']
REFERENCE = json.loads((HERE / 'opening-observations.json').read_text())['rights']
STATIONS = {
    '2017': {'exif': '2017-08-19T16:59:37', 'local': '2017-08-19T16:59:37+08:00',
             'basis': 'GPS clock 08:59:26 UTC, same date; local EXIF differs from GPS by 11 seconds after UTC+8 conversion.',
             'gate': [2830, 1470, 3520, 2480], 'balcony': [4340, 306, 5110, 1640]},
    '2026': {'exif': '2026-02-09T15:57:53+10:00', 'local': '2026-02-09T13:57:53+08:00',
             'basis': 'OffsetTimeOriginal is explicitly +10:00, not Shanghai +08:00; no confirming GPS clock. Light uses the recorded absolute instant.',
             'gate': [943, 672, 1148, 956], 'balcony': [1335, 390, 1540, 750]}
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def sun(local):
    date = datetime.fromisoformat(local)
    hour = date.hour + date.minute / 60 + date.second / 3600
    lat,lon = np.radians(31.208765187708064),121.43530309953091
    phase=2*np.pi/365*(date.timetuple().tm_yday-1+(hour-12)/24)
    equation=229.18*(.000075+.001868*np.cos(phase)-.032077*np.sin(phase)-.014615*np.cos(2*phase)-.040849*np.sin(2*phase))
    dec=.006918-.399912*np.cos(phase)+.070257*np.sin(phase)-.006758*np.cos(2*phase)+.000907*np.sin(2*phase)-.002697*np.cos(3*phase)+.00148*np.sin(3*phase)
    angle=np.radians((60*hour+equation+4*lon-480)/4-180)
    east=-np.cos(dec)*np.sin(angle)
    north=np.sin(dec)*np.cos(lat)-np.cos(dec)*np.cos(angle)*np.sin(lat)
    up=np.sin(lat)*np.sin(dec)+np.cos(lat)*np.cos(dec)*np.cos(angle)
    return np.array([east,north,up],dtype='float32'),[round(np.degrees(np.arctan2(east,north))%360,3),round(np.degrees(np.arcsin(up)),3)]

def frames(mesh, out, width, role):
    out.mkdir(parents=True,exist_ok=True)
    model=RASTER.read_glb(mesh)
    note={'file':mesh.name,'sha256':sha(mesh),'frames':{}}
    with tempfile.TemporaryDirectory(dir=out) as temp:
        lib=ENGINE['make_library'](Path(temp))
        painter=ENGINE['MaterialPass'](lib,model[1],model[2])
        transforms,directions,depths=ENGINE['sky_maps'](model[0],lib,RASTER)
        lib.set_sky(ENGINE['SAMPLES'],ENGINE['DEPTH_RESOLUTION'],RASTER.ptr(transforms),RASTER.ptr(directions),RASTER.ptr(depths))
        for year,station in STATIONS.items():
            cam=Camera(year)
            proj=cam.k@cam.r@cam.basis.T@np.column_stack((np.eye(3),-cam.c))
            light,angles=sun(station['local'])
            rects={'gate':station['gate'],'balcony':station['balcony']}
            if role=='v3':
                rects={'view':[0,0,cam.width,cam.height],**rects}
            for name,(x0,y0,x1,y1) in rects.items():
                pixels=width if name=='view' else 330
                spacing=(x1-x0)/pixels
                # The rasterizer samples pixel edges at +.5. Source is calibrated
                # at integer pixel centres. Rebase on each crop's outer left/top edge.
                q=proj.copy()
                q[0]+=(.5-x0)*q[2]
                q[1]+=(.5-y0)*q[2]
                box=(0,0,x1-x0,y1-y0)
                inv=np.linalg.inv(q[:,:3])
                back=np.ascontiguousarray(np.column_stack([inv,-inv@q[:,3]]),dtype='float32')
                field=np.full((round((y1-y0)/spacing),pixels),-1.,dtype='float32')
                lib.set_photo(RASTER.ptr(back),ctypes.c_float(spacing),int(angles[1]>0),RASTER.ptr(field))
                clipped=ENGINE['BACKEND']['projected_parts'](model,q)
                with patch.object(RASTER,'read_glb',return_value=clipped):
                    painter.active=True
                    image,stats=RASTER.raster(mesh,painter,pixels,q,box,light,angles)
                    if name=='view':
                        painter.active=False
                        flat,_=RASTER.raster(mesh,painter,pixels,q,box,light,angles)
                        diff=np.abs(np.array(image,dtype='int16')-np.array(flat,dtype='int16')).max(axis=2)
                        stats['normal_map_changed_pixels']=int(np.count_nonzero(diff))
                dest=out/(('view-'+year) if name=='view' else role+'-'+year+'-'+name)
                dest=dest.with_suffix('.jpg')
                image.save(dest,quality=95,subsampling=0,optimize=True)
                stats.update(year=year,part=name,file=dest.name,sha256=sha(dest),source_native_crop_xyxy=[x0,y0,x1,y1],solar_azimuth_altitude_deg=angles,source_EXIF=station['exif'],shanghai_time=station['local'],timestamp_evidence=station['basis'],source=REFERENCE[year],projection_native_enu=proj.tolist())
                if not stats['zbuffer_foreground_pixels']:raise ValueError('Empty projected view '+dest.name)
                note['frames'][year+'-'+name]=stats
    return note

def sheet(out):
    panel_width,panel_height=235,290
    canvas=Image.new('RGB',(1000,740),'#edeae3')
    draw=ImageDraw.Draw(canvas)
    draw.text((18,7),'129 Wukang Road | Door casing and balcony casements',fill='#20211f')
    for row,year in enumerate(STATIONS):
        y=34+row*344
        draw.text((18,y),year+' photograph station: same measured crop at each model revision',fill='#353c3e')
        for col,(role,part,label) in enumerate([('v2','gate','V2 / entry'),('v3','gate','V3 / entry'),('v2','balcony','V2 / balcony'),('v3','balcony','V3 / balcony')]):
            tile=Image.open(out/f'{role}-{year}-{part}.jpg');tile.thumbnail((panel_width,panel_height),Image.Resampling.LANCZOS)
            x=10+246*col
            canvas.paste(tile,(x+(panel_width-tile.width)//2,y+20+(panel_height-tile.height)//2))
            draw.text((x+5,y+314),label,fill='#2f3839')
    draw.text((18,724),'V3: diagonal grooves around the lower entrance; fanlight, two separately opened leaves and the dark recess above.',fill='#343b3d')
    dest=out/'registered-openings.jpg';canvas.save(dest,quality=95,subsampling=0,optimize=True)
    return sha(dest)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mesh',type=Path)
    parser.add_argument('output',type=Path)
    parser.add_argument('--previous',type=Path)
    parser.add_argument('--role',choices=['v2','v3'],default='v3')
    parser.add_argument('--width',type=int,default=1100)
    a=parser.parse_args()
    outputs={}
    if a.previous:outputs['v2']=frames(a.previous,a.output,a.width,'v2')
    outputs[a.role]=frames(a.mesh,a.output,a.width,a.role)
    for key,item in outputs.items():
        (a.output/(key+'-registered-renders.json')).write_text(json.dumps(item,ensure_ascii=False,indent=2)+'\n')
    if all((a.output/('v2-'+yr+'-'+name+'.jpg')).is_file() and (a.output/('v3-'+yr+'-'+name+'.jpg')).is_file() for yr in STATIONS for name in ('gate','balcony')):
        digest=sheet(a.output)
        (a.output/'registered-renders.json').write_text(json.dumps({'camera_sha256':sha(HERE/'two-photo-cameras.json'),'render_source_sha256':sha(Path(__file__).absolute()),'sheet_sha256':digest,'comparison_frozen_reports':{s:sha(a.output/(s+'-registered-renders.json')) for s in ('v2','v3')},'illumination':'Solar azimuth/height at each dated exposure plus 18-direction diffuse sky. Building shadows are computed on the input mesh. Site vegetation and cloud cover are undocumented.','image_sources':'Rendered pixels exclusively from the two input GLBs. The Commons JPEGs supply registration and EXIF; authors and source URLs are recorded per view.'},ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    main()
