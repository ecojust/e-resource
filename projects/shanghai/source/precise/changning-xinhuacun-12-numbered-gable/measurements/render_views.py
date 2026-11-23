"""Render the numbered gable and its three garden arches from the three source-photo stations."""
import argparse,hashlib,json,runpy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').is_file())
raster=runpy.run_path(str(PROJECT/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'))['raster']
LABELS={'numbered-front':'2014年报道 · 数字12与山墙绿窗','archival-front':'旧照 · 左侧圆形12号牌所在的立面','garden-oblique':'2026年独立摄影 · 山墙转角和三跨院廊'}
def render(model,out):
    out.mkdir(parents=True,exist_ok=True);cams=json.loads((HERE/'three-photographic-stations.json').read_bytes());sheet=Image.new('RGB',(1200,540),'#f4f0e8');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',15,index=2);records={}
    for i,(k,label)in enumerate(LABELS.items()):
        q=cams[k];w,h=q['size'];scale=min(880/w,800/h);im=raster(model,q,(0,0,w,h),int(w*scale));p=out/(k+'-model.jpg');im.save(p,quality=92)
        records[k]=dict(frame=q['size'],image=im.size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
        im.thumbnail((384,475));x=i*400+(400-im.width)//2;sheet.paste(im,(x,12+(475-im.height)//2));draw.text((16+i*400,500),label,font=font,fill='#283727')
    sheet.save(out/'registered-views.jpg',quality=93);(out/'rendered-views.json').write_text(json.dumps(dict(model_sha256=hashlib.sha256(model.read_bytes()).hexdigest(),views=records),ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('out',type=Path);args=cli.parse_args();render(args.mesh,args.out)
