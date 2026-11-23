"""Render original courtyard geometry at the four camera stations. Published sheets contain only model output."""
import argparse,ctypes,json,runpy,subprocess,tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image,ImageDraw
from register_court import Camera
HERE=Path(__file__).resolve().parent;PRECISE=HERE.parents[1]
backend=runpy.run_path(str(PRECISE/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py'))
def render(mesh,out,reference_folder=None):
    out.mkdir(parents=True,exist_ok=True);engine=backend['renderer'];parts=engine.read_glb(mesh)
    sun=np.array([.22,-.86,.48]);sun/=np.linalg.norm(sun)
    angles=[float(np.degrees(np.arctan2(sun[0],sun[1]))%360),float(np.degrees(np.arcsin(sun[2])))]
    crop=(0,0,650,487);data={}
    overview=Image.new('RGB',(1308,1022),'#f6f4ee');d=ImageDraw.Draw(overview)
    if reference_folder:private=Image.new('RGB',(1308,1960),'#fff')
    with tempfile.TemporaryDirectory() as td:
        so=Path(td)/'court.so'
        subprocess.run(['cc','-O2','-shared','-fPIC',str(PRECISE/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',str(so)],check=True)
        dll=ctypes.CDLL(str(so))
        for j,tag in enumerate([17,18,19,20]):
            p=Camera(tag).projection();clip=backend['projected_parts'](parts,p)
            with patch.object(engine,'read_glb',return_value=clip):
                picture,data[tag]=engine.raster(mesh,dll,650,p,crop,sun,angles)
            picture=picture.convert('RGB').resize((650,487),Image.Resampling.LANCZOS)
            picture.save(out/f'2016-frame-{tag}-model.jpg',quality=94,optimize=True)
            x=(j%2)*658;y=(j//2)*511;overview.paste(picture,(x,y))
            label=['No. 6 | Rose canopy','No. 7 | Green glazed terrace','Unnumbered middle section | Twin casements','No. 9 | Open balconies'][j]
            d.text((x+8,y+489),label,fill='#303532')
            if reference_folder:
                image=Image.open(reference_folder/f'4travel-425044{tag}-650.jpg').convert('RGB')
                private.paste(image,(0,j*490));private.paste(picture,(658,j*490))
    overview.save(out/'2016-court-elevation-model.jpg',quality=93,optimize=True)
    if reference_folder:private.save(out.parent/'four-originals-and-model-private.jpg',quality=89)
    (out/'registered-court-renders.json').write_text(json.dumps(data,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('output',type=Path)
    p.add_argument('--private-references',type=Path,help='Optional local visual comparison; never publish reference photographs.')
    a=p.parse_args();render(a.mesh,a.output,a.private_references)
