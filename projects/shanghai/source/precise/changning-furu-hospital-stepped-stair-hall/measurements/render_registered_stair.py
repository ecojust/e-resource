"""Render three original photograph views from the model and the camera measurements, without the source photos."""
import argparse, hashlib,json,runpy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
SHARED=HERE.parents[3]/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'
raster=runpy.run_path(str(SHARED))['raster']
LABELS={'district-archive':'区规资局档案斜照','press-archive':'周到上海旧院正照','road-centre':'2020年2月街面复测'}
def render_crop(mesh,camera,crop,width):
    scale=width/(crop[2]-crop[0])
    height=round((crop[3]-crop[1])*scale)
    frame=Image.new('RGB',(width,height))
    for y in range(0,height,48):
        bottom=min(height,y+48)
        clipped=(crop[0],crop[1]+y/scale,crop[2],crop[1]+bottom/scale)
        stripe=raster(mesh,camera,clipped,width)
        assert stripe.size==(width,bottom-y)
        frame.paste(stripe,(0,y))
    return frame

def render(mesh,d,width):
    d.mkdir(parents=True,exist_ok=True);stations=json.loads((HERE/'registered-stair-stations.json').read_text())['stations']
    report={'mesh_sha256':hashlib.sha256(mesh.read_bytes()).hexdigest(),'source_photo_pixels_loaded':False,'views':{}}; images=[]
    for k in LABELS:
        cam=stations[k]
        crop=cam['crop'];im=render_crop(mesh,cam,crop,2*width)
        im=im.resize((width,im.height//2),Image.Resampling.LANCZOS)
        fn=d/(k+'-model.jpg');im.save(fn,quality=92)
        report['views'][k]={'crop':crop,'file':fn.name,'sha256':hashlib.sha256(fn.read_bytes()).hexdigest()};images.append((k,im))
    h=max(p.height for _,p in images)+38;out=Image.new('RGB',(len(images)*(width+12),h),(241,239,230));dr=ImageDraw.Draw(out)
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',14,index=2)
    for i,(key,img) in enumerate(images):
        out.paste(img,(i*(width+12)+6,(h-30-img.height)//2));dr.text((i*(width+12)+7,h-25),LABELS[key],font=font,fill=(49,46,41))
    out.save(d/'registered-stair-hall.jpg',quality=93)
    (d/'registered-renders.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('out',type=Path);p.add_argument('--width',type=int,default=420)
    a=p.parse_args();render(a.mesh,a.out,a.width)
