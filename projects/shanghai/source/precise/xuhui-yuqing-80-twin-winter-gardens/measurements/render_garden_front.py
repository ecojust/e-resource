"""Render the delivered model from the two recorded garden views, including each camera's original roll."""
import argparse
import ctypes
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

def render(mesh,output,width=720):
    output.mkdir(exist_ok=True,parents=True)
    renderer=backend['renderer'];parts=renderer.read_glb(mesh)
    sun=np.asarray([-.33,-.78,.53]);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    views=[];records={}
    with tempfile.TemporaryDirectory() as tmp:
        binary=Path(tmp)/'garden.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(binary)],check=True)
        native=ctypes.CDLL(str(binary))
        for number in [4,6]:
            camera=Camera(number);projection=camera.projection();crop=(0,0,*camera.size)
            clipped=backend['projected_parts'](parts,projection)
            with patch.object(renderer,'read_glb',return_value=clipped):
                picture,records[number]=renderer.raster(mesh,native,width,projection,crop,sun,angles)
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
