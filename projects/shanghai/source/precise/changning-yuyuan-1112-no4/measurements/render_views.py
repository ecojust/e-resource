"""Render the three dated photographic stations from actual model triangles and their surface materials."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
raster=runpy.run_path(str(PROJECT/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'))['raster']
NAMES={'corner-2011':'2011年12月 · 弧形墙头及门牌','corner-2015':'2015年11月 · 公告箱与院门','street-2020':'2020年2月 · 南凸翼三窗面'}
def render(model,out):
    out.mkdir(exist_ok=True,parents=True)
    cameras=json.loads((HERE/'registered-stations.json').read_bytes())
    sheet=Image.new('RGB',(1200,455),'#f2eee7')
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',15,index=2)
    pen=ImageDraw.Draw(sheet);views={}
    for i,(name,label)in enumerate(NAMES.items()):
        camera=cameras[name];w,h=camera['size']
        image=raster(model,camera,(0,0,w,h),w);target=out/(name+'-model.jpg')
        image.save(target,quality=93)
        views[name]=dict(frame=[w,h],width=image.width,height=image.height,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        image.thumbnail((390,389))
        sheet.paste(image,(i*400+(400-image.width)//2,(393-image.height)//2))
        pen.text((i*400+12,405),label,font=font,fill='#303631')
    sheet.save(out/'registered-views.jpg',quality=92)
    (out/'rendered-views.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),views=views),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('model',type=Path);cli.add_argument('out',type=Path)
    args=cli.parse_args();render(args.model,args.out)
