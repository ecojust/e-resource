"""Render three original photograph views from the model and the camera measurements, without the source photos."""
import argparse, hashlib,json,runpy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
SHARED=HERE.parents[3]/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'
raster=runpy.run_path(str(SHARED))['raster']
LABELS={'courtyard-2014':'2014年·东侧临弄屋端','lane-first-position':'南口同站·首排位置假设','lane-second-position':'南口同站·次排位置假设'}
def render(mesh,d,width):
    d.mkdir(parents=True,exist_ok=True);stations=json.loads((HERE/'gable-photo-stations.json').read_text())['stations']
    report={'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'source_photo_pixels_loaded':False,'views':{}}; images=[]
    for k,cam in stations.items():
        crop=cam['crop'];im=raster(mesh,cam,crop,2*width)
        im=im.resize((width,im.height//2),Image.Resampling.LANCZOS)
        fn=d/(k+'-model.jpg');im.save(fn,quality=92)
        report['views'][k]={'crop':crop,'file':fn.name,'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()};images.append((k,im))
    h=max(p.height for _,p in images)+38;out=Image.new('RGB',(len(images)*(width+12),h),(241,239,230));dr=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14,index=2)
    for i,(key,img) in enumerate(images):
        out.paste(img,(i*(width+12)+6,(h-30-img.height)//2));dr.text((i*(width+12)+7,h-25),LABELS[key],font=font,fill=(49,46,41))
    out.save(d/'registered-gable.jpg',quality=93)
    (d/'registered-renders.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);p.add_argument('--width',type=int,default=420)
    a=p.parse_args();render(a.mesh,a.out,a.width)
