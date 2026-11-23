"""Render original inspection figures at the two recorded gate viewpoints."""
import argparse,ctypes,json,runpy,subprocess,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image,ImageDraw
from register_gate import Camera

HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
BACK=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
VIEWS={'2016-gate':('06',(0,0,690,1038)),'2016-cornice':('07',(45,76,606,290)),
       '2016-hardware':('06',(140,640,597,900)),'2016-number':('06',(185,395,417,503))}

def render(mesh,output):
    output.mkdir(parents=True,exist_ok=True)
    engine=BACK['renderer'];parts=engine.read_glb(mesh)
    sun=np.array([-.42,-.68,.6],dtype=np.float32);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    with tempfile.TemporaryDirectory() as temp:
        lib=Path(temp)/'gate.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(lib)],check=True)
        dll=ctypes.CDLL(str(lib));report={}
        for name,(view,crop) in VIEWS.items():
            cam=Camera(view);p=cam.projection()
            with patch.object(engine,'read_glb',return_value=BACK['projected_parts'](parts,p)):
                im,stats=engine.raster(mesh,dll,1060,p,crop,sun,angles)
            im.thumbnail((840,850),Image.Resampling.LANCZOS)
            sheet=Image.new('RGB',(im.width,im.height+36),'#f0eee8');sheet.paste(im,(0,0))
            ImageDraw.Draw(sheet).text((10,im.height+10),'No. 20, Lane 222 | Original model at reference camera '+view,fill='#292c31')
            sheet.save(output/(name+'-model.jpg'),quality=94,optimize=True);report[name]=stats
    (output/'model-renders.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path)
    args=p.parse_args();render(args.mesh,args.out)
