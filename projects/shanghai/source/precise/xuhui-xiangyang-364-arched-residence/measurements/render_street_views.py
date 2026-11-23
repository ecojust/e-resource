"""Render the delivered mesh in its registered street cameras. Only model pixels are saved."""
import argparse
import ctypes
import json
from pathlib import Path
import runpy
import subprocess
import tempfile
from unittest.mock import patch
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
backend=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
def render(model,out):
    out.mkdir(parents=True,exist_ok=True)
    U=np.array([.0185,.99983]);U/=np.linalg.norm(U)
    frame=np.eye(4);frame[:2,0]=U;frame[:2,1]=[-U[1],U[0]]
    light=np.array([.65,-.38,.67],dtype=np.float32);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    survey=json.loads((HERE/'street-facade-dimensions.json').read_bytes())
    roof=json.loads((HERE/'roof-room-two-stations.json').read_bytes())
    entries=[(r['station'],r['P'],(0,0,720,534)) for r in survey['stations']]
    entries.extend(('high-'+r['station'],r['P'],(0,0,707,560)) for r in roof['projections'])
    engine=backend['renderer'];meshes=engine.read_glb(model)
    with tempfile.TemporaryDirectory() as temp:
        libpath=Path(temp)/'street.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(libpath)],check=True)
        lib=ctypes.CDLL(str(libpath));report={}
        for name,P,crop in entries:
            camera=np.array(P)@np.linalg.inv(frame)
            parts=backend['projected_parts'](meshes,camera)
            with patch.object(engine,'read_glb',return_value=parts):
                image,stats=engine.raster(model,lib,1100,camera,crop,light,angles)
            image.thumbnail((760,620),Image.Resampling.LANCZOS)
            image.save(out/(name+'.jpg'),quality=92,optimize=True)
            report[name]=stats
    (out/'render-verification.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args();render(args.model,args.output)
