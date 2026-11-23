"""Render both facade photographs beside the delivered model in the measured cameras."""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from unittest.mock import patch
import numpy as np
from PIL import Image,ImageDraw

HERE=Path(__file__).resolve().parent
SOURCE=HERE.parent/'source'
PRECISE=HERE.parents[1]
sys.path.insert(0,str(SOURCE))
from build_model import placed_matrix
raster=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))

def render(mesh,photos,out):
    render_engine=raster['renderer']
    meshes=render_engine.read_glb(mesh)
    controls=[('314','314-open-casement.json','camera_matrix_from_model_to_working_half',[1072,712]),
              ('310','310-gate-and-gables-camera.json','display_camera_P_reference',[880,584])]
    placement=json.loads((SOURCE/'house-placements.json').read_bytes())
    evidence=json.loads((HERE/'registered-houses-and-photographs.json').read_bytes())
    expected={str(row['lane']):row['sha256']for row in evidence['photo_sources']}
    out.mkdir(exist_ok=True,parents=True)
    light=np.array([-.35,-.46,.817],dtype=np.float32)
    light/=np.linalg.norm(light)
    azel=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    with tempfile.TemporaryDirectory()as tmp:
        lib=Path(tmp)/'depth.so'
        c=PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(c),'-lm','-o',str(lib)],check=True)
        library=ctypes.CDLL(str(lib))
        for lane,file,key,size in controls:
            photo=photos/('jingxing-'+lane+'.jpg')
            if hashlib.sha256(photo.read_bytes()).hexdigest()!=expected[lane]:
                raise ValueError(f'Original image differs for lane {lane}')
            camera=np.array(json.loads((HERE/file).read_bytes())[key])@np.linalg.inv(placed_matrix(placement['house_'+lane]))
            visible=raster['projected_parts'](meshes,camera)
            with patch.object(render_engine,'read_glb',return_value=visible):
                image,_=render_engine.raster(mesh,library,1240,camera,[0,0,*size],light,azel)
            image.thumbnail((810,550),Image.Resampling.LANCZOS)
            photograph=Image.open(photo).convert('RGB').resize(image.size,Image.Resampling.LANCZOS)
            width,height=image.size
            board=Image.new('RGB',(2*width,height+28),'#f3eee4')
            board.paste(photograph,(0,28));board.paste(image,(width,28))
            draw=ImageDraw.Draw(board)
            draw.text((8,8),'Fayhoo | Wikimedia Commons | CC BY-SA 3.0 | 2015-04-06 | Lane '+lane,fill='#211d18')
            draw.text((width+8,8),'Registered mesh | Jingxing Road, Shanghai | 2015 photograph view',fill='#211d18')
            board.save(out/(lane+'-photograph-and-mesh.jpg'),quality=89,optimize=True)

if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('mesh',type=Path)
    cli.add_argument('photos',type=Path,help='Directory containing the original jingxing-310.jpg and jingxing-314.jpg')
    cli.add_argument('output',type=Path)
    a=cli.parse_args();render(a.mesh,a.photos,a.output)
