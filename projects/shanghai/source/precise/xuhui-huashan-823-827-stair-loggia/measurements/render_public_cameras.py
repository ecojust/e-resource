"""Render the ordinary-page cameras using the same measured eye and target as the WebGL viewer."""
from pathlib import Path
import argparse, ctypes, json, os, runpy, subprocess, tempfile
from unittest.mock import patch
import numpy as np
from PIL import Image,ImageDraw

S=Path(__file__).resolve().parents[1];P=S.parent
backend=runpy.run_path(str(P/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
engine=backend['renderer']
def camera(row):
    eye=np.array(row['eye']);target=np.array(row['target']);forward=target-eye
    dist=np.linalg.norm(forward);forward=forward/dist
    right=np.cross(forward,[0.,0.,1.]);right/=np.linalg.norm(right)
    down=np.cross(forward,right);down/=np.linalg.norm(down)
    axes=np.row_stack((right,down,forward))
    width,height=row['width'],row['height'];fx=dist*width/row['width_m']
    k=np.array([[fx,0,width/2],[0,fx,height/2],[0,0,1]])
    return k@np.column_stack((axes,-axes@eye))
def main(mesh,out,source):
    records=json.loads(source.read_bytes());parts=engine.read_glb(mesh);sun=np.array([-.46,-.66,.61],dtype=np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    out.mkdir(exist_ok=True,parents=True);library=out/'project.so';subprocess.run(['cc','-O2','-shared','-fPIC',str(P/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(library)],check=True);fd=os.memfd_create('arch-raster');os.write(fd,library.read_bytes());lib=ctypes.CDLL('/proc/self/fd/'+str(fd));os.close(fd)
    sheet=Image.new('RGB',(996,744),'#dedede');draw=ImageDraw.Draw(sheet)
    for idx,row in enumerate(records):
        matrix=camera(row);visible=backend['projected_parts'](parts,matrix)
        with patch.object(engine,'read_glb',return_value=visible):
            picture,stats=engine.raster(mesh,lib,600,matrix,[0,0,row['width'],row['height']],sun,angles)
        picture.save(out/(row['name']+'.jpg'),quality=88);picture.thumbnail((329,224));x=332*(idx%3);y=248*(idx//3);sheet.paste(picture,(x+(329-picture.width)//2,y+20));draw.text((x+2,y+2),row['name'],fill='black')
    sheet.save(out/'camera-sheet.jpg',quality=89)
if __name__=='__main__':
    arg=argparse.ArgumentParser(description=__doc__);arg.add_argument('mesh',type=Path);arg.add_argument('output',type=Path);arg.add_argument('--cameras',type=Path,default=S/'source/cameras.json');opt=arg.parse_args();main(opt.mesh,opt.output,opt.cameras)
