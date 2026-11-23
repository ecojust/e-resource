"""Render the two No. 20 camera stations from original geometry, with no photographic texture."""
from pathlib import Path
import argparse,json,hashlib,runpy
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).absolute().parent
PROJECT=next(p for p in D.parents if (p/'tools/package_architectural_model.py').is_file())
raster=runpy.run_path(str(PROJECT/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'))['raster']
def render(model,out,width=520):
    out.mkdir(parents=True,exist_ok=True);s=json.loads((D/'two-stations.json').read_bytes())
    marks={};panels=[]
    for name in ['photo-lane','photo-stair']:
        q=s[name];pix=raster(model,q,[0,0,*q['size']],width*2)
        im=pix.resize((width,round(width*500/375)),Image.Resampling.LANCZOS)
        dest=out/(name[6:]+'-model.jpg');im.save(dest,quality=93,subsampling=0)
        marks[name]={'file':dest.name,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'pixels':list(im.size)};panels.append(im)
    sheet=Image.new('RGB',(width*2+40,panels[0].height+88),'#f3f1ea');pen=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',max(13,int(width*.045)),index=2)
    for j,(im,cap)in enumerate(zip(panels,['20号 · 巷面卷额与两层窗','20号 · 首跑石阶与梯口信箱'])):
        x=10+j*(width+20);sheet.paste(im,(x,10));pen.text((x,im.height+24),cap,font=font,fill='#3b443d')
    sheet.save(out/'registered-views.jpg',quality=93)
    (out/'rendered-views.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),views=marks,combined_sha256=hashlib.sha256((out/'registered-views.jpg').read_bytes()).hexdigest()),indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('model',type=Path);p.add_argument('out',type=Path);p.add_argument('--width',type=int,default=520);args=p.parse_args();render(args.model,args.out,args.width)
