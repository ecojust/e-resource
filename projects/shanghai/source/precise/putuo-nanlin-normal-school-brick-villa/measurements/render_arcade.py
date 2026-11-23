"""Make model-only renderings at the three registered historical photograph viewpoints."""
import argparse, ctypes, hashlib, json, runpy, subprocess, sys, tempfile
from pathlib import Path
from unittest.mock import patch
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).absolute().parent
sys.path.insert(0,str(HERE.parent/'source'))
from fabric import PROJECT, metric


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('model',type=Path);ap.add_argument('output',type=Path);args=ap.parse_args()
    d=json.loads((HERE/'arcade-photograph-registration.json').read_bytes());layout=json.loads((HERE.parent/'source/building-layout.json').read_bytes())
    precise=PROJECT/'source/precise';shared=runpy.run_path(precise/'changning-hongji-yuyuan-garden-houses-8-and-9/measurements/render-garden-stations.py')
    renderer=shared['renderer']; parts=renderer.read_glb(args.model);z=layout['arcade_storey_m'];width=layout['arcade_outer_width_m'];span=width/(1.+.245/7.); pitch=span/7
    chart=np.array([[0,pitch,0,metric(119,452)[0]],[-pitch,0,0,width-(width-span)/2],[0,0,z,0],[0,0,0,1]])
    light=np.array([-.84,-.28,.55],dtype=np.float32);light/=np.linalg.norm(light);azel=[float(np.degrees(np.arctan2(light[0],light[1]))%360),float(np.degrees(np.arcsin(light[2])))]
    args.output.mkdir(parents=True,exist_ok=True);survey={'mesh':hashlib.sha256(args.model.read_bytes()).hexdigest(),'views':{}}
    with tempfile.TemporaryDirectory(dir=args.output) as t:
        so=Path(t)/'r.so';subprocess.run(['cc','-shared','-fPIC','-O2',str(precise/'huangpu-old-jiefu-nanjing-road-shopfront/measurements/northwest_raster.c'),'-lm','-o',so],check=True)
        for name,view in d['views'].items():
            P=np.array(view['positive_inward_camera']['P_s_inward_z_fraction'])@np.linalg.inv(chart)
            # Denominator at front points is positive; normalize the metre-scale depth for the shared renderer.
            P/=np.linalg.norm(P[2,:3])
            projected=shared['projected_parts'](parts,P);crop=[0,0,*view['original_dimensions']]
            with patch.object(renderer,'read_glb',return_value=projected):
                im,record=renderer.raster(args.model,ctypes.CDLL(str(so)),730,P,crop,light,azel)
            dest=args.output/(name+'.jpg');im.save(dest,quality=90)
            survey['views'][name]=dict(sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),**record)
    (args.output/'render-record.json').write_text(json.dumps(survey,indent=2)+'\n')
    from PIL import ImageFont, ImageOps
    sheet=Image.new('RGB',(1100,800),(242,239,232))
    draw=ImageDraw.Draw(sheet)
    try:
        font=ImageFont.truetype('DejaVuSans.ttf',18)
    except OSError:
        font=ImageFont.load_default()
    def frame(im,bounds,title):
        x,y,w,h=bounds
        im=ImageOps.contain(im,(w,h),Image.Resampling.LANCZOS)
        sheet.paste(im,(x+(w-im.width)//2,y+(h-im.height)//2))
        draw.text((x,y-27),title,fill=(49,48,44),font=font)
    complete=Image.open(args.output/'restored-complete.jpg').convert('RGB')
    oblique=Image.open(args.output/'restored-oblique.jpg').convert('RGB')
    early=Image.open(args.output/'earlier-oblique.jpg').convert('RGB')
    frame(complete,(20,40,586,339),'Seven bays seen from the restored arcade')
    frame(oblique,(625,40,455,339),'Restored arcade from the side')
    frame(early,(20,430,586,345),'South arcade and its west return')
    xscale=early.width/1280;yscale=early.height/960
    crop=early.crop((int(355*xscale),int(200*yscale),int(660*xscale),int(563*yscale)))
    frame(crop,(625,430,455,345),'Brick blind arch on the west wall')
    sheet.save(args.output/'registered-arcade.jpg',quality=92)
if __name__=='__main__':main()
