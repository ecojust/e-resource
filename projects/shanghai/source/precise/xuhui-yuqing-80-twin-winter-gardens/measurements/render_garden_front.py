"""Render the delivered model from the two recorded garden views, including each camera's original roll."""
import argparse
import ctypes
import math
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
from unittest.mock import patch

import numpy as np
from PIL import Image, ImageDraw
from register_garden import Camera

HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
backend=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))

def illumination(number):
    if number==6:
        sun=np.array([.13,-.71,.69])
        sun/=np.linalg.norm(sun)
        return sun, [], 'Illustrative diffuse garden daylight. This photograph has no verified time.'
    # NOAA fractional-year approximation, local China Standard Time and the measured garden axis.
    hour=15+35/60+54/3600;lat=math.radians(31.2042);lon=121.4342
    phase=2*math.pi/365*(257-1+(hour-12)/24)
    e=229.18*(.000075+.001868*math.cos(phase)-.032077*math.sin(phase)-.014615*math.cos(2*phase)-.040849*math.sin(2*phase))
    dec=.006918-.399912*math.cos(phase)+.070257*math.sin(phase)-.006758*math.cos(2*phase)+.000907*math.sin(2*phase)-.002697*math.cos(3*phase)+.00148*math.sin(3*phase)
    ha=math.radians((60*hour+e+4*lon-480)/4-180)
    east=-math.cos(dec)*math.sin(ha)
    north=math.sin(dec)*math.cos(lat)-math.cos(dec)*math.cos(ha)*math.sin(lat)
    height=math.sin(lat)*math.sin(dec)+math.cos(lat)*math.cos(dec)*math.cos(ha)
    axis=math.radians(50.85)
    local=np.array([east*math.sin(axis)+north*math.cos(axis),-east*math.cos(axis)+north*math.sin(axis),height])
    return local,[round(math.degrees(math.atan2(east,north))%360,2),round(math.degrees(math.asin(height)),2)],'Solar direction computed for EXIF 2013-09-14 15:35:54, UTC+8.'

def render(mesh,output,width=720):
    output.mkdir(exist_ok=True,parents=True)
    renderer=backend['renderer'];parts=renderer.read_glb(mesh)
    views=[];records={}
    with tempfile.TemporaryDirectory() as tmp:
        binary=Path(tmp)/'garden.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(binary)],check=True)
        native=ctypes.CDLL(str(binary))
        for number in [4,6]:
            sun,angles,source=illumination(number)
            camera=Camera(number);projection=camera.projection();crop=(0,0,*camera.size)
            clipped=backend['projected_parts'](parts,projection)
            with patch.object(renderer,'read_glb',return_value=clipped):
                picture,records[number]=renderer.raster(mesh,native,width,projection,crop,sun,angles)
            records[number]['illumination']=source
            picture=picture.convert('RGB');views.append(picture)
            picture.save(output/f'garden-photo-{number}-model.jpg',quality=94,optimize=True)
    height=max(p.height for p in views);sheet=Image.new('RGB',(2*width+8,height+27),'#f4f3ed')
    draw=ImageDraw.Draw(sheet)
    for i,(picture,label) in enumerate(zip(views,['Northeast view | 14 September 2013','Southwest view | open lower terrace'])):
        x=i*(width+8);sheet.paste(picture,(x,0));draw.text((x+8,height+6),label,fill='#332e27')
    sheet.save(output/'garden-elevation-model.jpg',quality=93,optimize=True)
    (output/'registered-garden-renders.json').write_text(json.dumps(records,indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mesh',type=Path);parser.add_argument('directory',type=Path)
    parser.add_argument('--width',type=int,default=720);args=parser.parse_args();render(args.mesh,args.directory,args.width)
