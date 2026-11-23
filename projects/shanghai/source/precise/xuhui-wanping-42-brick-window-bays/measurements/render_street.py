"""Render the 42 Wanping Road brick elevation from the February 2019 photograph."""
import argparse,ctypes,json,runpy,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'source'))
def projection(name=None):
    from build_model import SCALE
    ref=json.loads((HERE/'registered-street-camera.json').read_bytes())
    K,R,C=(np.array(ref[k]) for k in ('intrinsic','world_to_camera','camera_centre'))
    return K@R@np.column_stack([np.diag(1/np.asarray(SCALE)),-C])
backend=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
def render(mesh,out):
    engine=backend['renderer'];parts=engine.read_glb(mesh);out.mkdir(parents=True,exist_ok=True)
    light=np.array([-.46,-.66,.61],dtype=np.float32);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    survey={'street-front':('commons',[234,0,902,787]),'central-stair':('commons',[397,165,505,753]),
            'leaf-panels':('commons',[475,167,802,550]),'entrance':('commons',[392,560,513,763])}
    with tempfile.TemporaryDirectory() as temp:
        lib=Path(temp)/'garden.so';subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(lib)],check=True)
        dll=ctypes.CDLL(str(lib));report={}
        for tag,(key,crop) in survey.items():
            p=projection(key);clipped=backend['projected_parts'](parts,p)
            with patch.object(engine,'read_glb',return_value=clipped):image,stats=engine.raster(mesh,dll,1160,p,crop,light,angles)
            image.thumbnail((840,740),Image.Resampling.LANCZOS);image.save(out/(tag+'.jpg'),quality=93,optimize=True);report[tag]=stats
    (out/'model-projection-renders.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path);a=p.parse_args();render(a.mesh,a.output)
