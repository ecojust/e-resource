"""Render the street frontage using the 2018 photograph and its 28 mm-equivalent lens."""
import argparse,ctypes,json,runpy,subprocess,sys,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent
PRECISE=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'source'))
def projection(name=None):
    # H maps the (X,Z) plane of the long masonry wall to native-aspect photo pixels.
    h=np.linalg.inv(np.array(json.loads((HERE/'primary-front-control.json').read_text())['photo_to_local_metres']))
    w=1300; ht=w*2988/5312; f=w*28/36
    k=np.array([[f,0,w/2],[0,f,ht/2],[0,0,1.]])
    a,b=np.linalg.solve(k,h[:,:2]).T;normal=np.cross(a,b);normal*=np.sqrt(np.linalg.norm(a)*np.linalg.norm(b))/np.linalg.norm(normal)
    p=np.column_stack([h[:,0],k@normal,h[:,1],h[:,2]])
    if (-np.linalg.solve(p[:,:3],p[:,3]))[1]>0:p[:,1]*=-1
    if (p@[0,0,0,1])[2]<0:p=-p
    return p
backend=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
def render(mesh,out):
    engine=backend['renderer'];parts=engine.read_glb(mesh);out.mkdir(parents=True,exist_ok=True)
    light=np.array([-.46,-.66,.61],dtype=np.float32);light/=np.linalg.norm(light)
    angles=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    survey={'street-front':('commons',[0,0,1300,690]),'gable-and-arch':('commons',[920,-5,1300,665]),'brick-and-sashes':('commons',[227,141,876,564])}
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
