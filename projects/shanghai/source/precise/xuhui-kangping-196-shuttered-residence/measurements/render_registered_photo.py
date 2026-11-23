"""Render the released mesh in the measured 2019 camera, preserving perspective-correct plaster UVs."""
import argparse,ctypes,json,runpy,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'source'))
from photo_plane import P
backend=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
def render(mesh,out):
    engine=backend['renderer'];parts=engine.read_glb(mesh);out.mkdir(parents=True,exist_ok=True)
    light=np.array([-.46,-.66,.61],dtype=np.float32);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    survey={'2019-elevation':[0,83,800,535],'rear-windows':[218,87,700,326],'street-relief':[315,293,766,509]}
    with tempfile.TemporaryDirectory() as temp:
        lib=Path(temp)/'facade.so';subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(lib)],check=True)
        dll=ctypes.CDLL(str(lib));report={}
        for tag,crop in survey.items():
            p=P;clipped=backend['projected_parts'](parts,p)
            with patch.object(engine,'read_glb',return_value=clipped):image,stats=engine.raster(mesh,dll,1160,p,crop,light,angles)
            image.thumbnail((840,740),Image.Resampling.LANCZOS);image.save(out/(tag+'.jpg'),quality=93,optimize=True);report[tag]=stats
    (out/'model-projection-renders.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args();render(a.mesh,a.output)
