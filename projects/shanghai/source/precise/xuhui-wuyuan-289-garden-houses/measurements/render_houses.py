"""Render the delivered GLB in the two numbered photo stations and the overall view."""
from pathlib import Path
import argparse,ctypes,json,runpy,sys,tempfile,subprocess
from unittest.mock import patch
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;PRECISE=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'source'))
from placement import Facade
rendering=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
renderer=rendering['renderer']
def local_matrix(f):
    frame=np.eye(4)
    frame[:2,0]=f.u;frame[:2,1]=-f.out;frame[:2,3]=f.origin
    return np.linalg.inv(frame)
def camera(eye,look,w,h,width):
    eye=np.array(eye);look=np.array(look);direction=look-eye;dist=np.linalg.norm(direction);direction=direction/dist
    right=np.cross(direction,[0.,0.,1.]);right/=np.linalg.norm(right)
    down=np.cross(direction,right);R=np.array([right,down,direction]);focal=w*dist/width
    return np.array([[focal,0,w/2],[0,focal,h/2],[0,0,1]])@np.c_[R,-R@eye]
def raster(model,out):
    out.mkdir(exist_ok=True,parents=True)
    views=json.loads((HERE.parent/'source/cameras.json').read_bytes());stations={}
    for row in views[:3]:
        w,h=(900,585);stations[row['name']]=(camera(row['eye'],row['target'],w,h,row['width_m']),[0,0,w,h])
    s=json.loads((HERE/'north-numbered-camera.json').read_bytes())
    # This wider crop keeps the staircase, main roof and projecting bay in frame.
    stations['north-photo']=(np.array(s['native_P'])@local_matrix(Facade(None,'1-2')),[300,0,4247,3239])
    for i,r in enumerate(json.loads((HERE/'house-three-two-registered-views.json').read_bytes())['stations']):
        w,h=r['observed_image_size'];stations['south-photo-'+str(i+1)]=(np.array(r['P'])@local_matrix(Facade(None,'3-4')),[0,0,w,h])
    record=json.loads((HERE/'garden-1935-camera.json').read_bytes())
    stations['garden-1935']=(np.asarray(record['P'])@local_matrix(Facade(None,'3-4')),[0,0,760,460])
    light=np.array([.48,-.45,.75],dtype=np.float32);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))),float(np.degrees(np.arcsin(light[2])))]
    parts=renderer.read_glb(model);report={}
    with tempfile.TemporaryDirectory()as tmp:
        lib=Path(tmp)/'raster.so'
        subprocess.run(['cc','-shared','-fPIC','-O2',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(lib)],check=True)
        backend=ctypes.CDLL(str(lib))
        for name,(mat,crop)in stations.items():
            clipped=rendering['projected_parts'](parts,mat)
            with patch.object(renderer,'read_glb',return_value=clipped):
                image,stat=renderer.raster(model,backend,750,mat,crop,light,angles)
            image.save(out/(name+'.jpg'),quality=92);report[name]=stat
    (out/'raster-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('model',type=Path);cli.add_argument('out',type=Path)
    args=cli.parse_args();raster(args.model,args.out)
