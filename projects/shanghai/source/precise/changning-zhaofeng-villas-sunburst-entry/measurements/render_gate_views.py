"""Render the delivered GLB from the measured road stations, preserving its original surface materials."""
import argparse,hashlib,json,sys,runpy
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).absolute().parent
PROJECT=next(p for p in HERE.parents if (p/'tools/package_architectural_model.py').exists())
RASTER=runpy.run_path(str(PROJECT/'source/precise/changning-st-johns-gezhi-science-hall/measurements/render_science_views.py'))['raster']
VIEWS={'street-station-7':'2021年1月 · 路南第7站','road-anniversary':'2021年10月报道 · 从街前望入','district-detail':'2021年5月报道 · 东墙近照','opposite-detail':'图册 · 另一侧的题名墙'}
def render(path,out,width):
 out.mkdir(parents=True,exist_ok=True);cams=json.loads((HERE/'registered-views.json').read_bytes());results={}
 sheet=Image.new('RGB',(900,662),'#f3efe6');d=ImageDraw.Draw(sheet);font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',17,index=2)
 for i,(name,caption) in enumerate(VIEWS.items()):
  cam=cams[name];w,h=cam['size'];im=RASTER(path,cam,(0,0,w,h),min(width,round(width*w/h)) if h>w else width)
  dest=out/(name+'-model.jpg');im.save(dest,quality=93);results[name]={'file':dest.name,'size':im.size,'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
  im.thumbnail((430,277));x=12+i%2*448;y=9+i//2*327;sheet.paste(im,(x+(430-im.width)//2,y));d.text((x,y+283),caption,font=font,fill='#363b35')
 sheet.save(out/'registered-views.jpg',quality=92)
 (out/'rendered-views.json').write_text(json.dumps({'mesh_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'views':results},ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 cli=argparse.ArgumentParser(description=__doc__);cli.add_argument('mesh',type=Path);cli.add_argument('output',type=Path);cli.add_argument('--width',type=int,default=650);a=cli.parse_args();render(a.mesh,a.output,a.width)
