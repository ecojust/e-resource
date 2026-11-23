"""Make a credited comparison plate from Fayhoo's original image and the registered model rendering."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
SOURCE='https://commons.wikimedia.org/wiki/File:Shanghai_Jiaoyu_Pingguyuan.JPG'
SHA='7f9b00632cdaf14b9019f012839e5d20ba640431452943c29306154b7750fef8'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def generate(original,render,out):
    if sha(original)!=SHA:raise ValueError('The supplied Commons image differs from the observed original')
    actual=Image.open(original).convert('RGB');model=Image.open(render).convert('RGB')
    w,h=model.size
    actual=actual.resize((w,h),Image.Resampling.LANCZOS)
    canvas=Image.new('RGB',(2*w+12,h+92),'#f7f5ef')
    canvas.paste(actual,(0,0));canvas.paste(model,(w+12,0));draw=ImageDraw.Draw(canvas)
    bold=ImageFont.load_default(size=18);small=ImageFont.load_default(size=13)
    draw.text((12,h+9),'Fayhoo  |  7 February 2015',font=bold,fill='#322f29')
    draw.text((w+24,h+9),'Registered courtyard model',font=bold,fill='#322f29')
    draw.text((12,h+42),'Photo by Fayhoo, resized. Comparison plate: CC BY-SA 3.0  |  https://creativecommons.org/licenses/by-sa/3.0/',font=small,fill='#424038')
    draw.text((12,h+65),SOURCE,font=small,fill='#424038')
    canvas.save(out,quality=92,optimize=True)
    record={'photo_url':SOURCE,'photographer':'Fayhoo','photo_license':'CC BY-SA 3.0','photo_sha256':SHA,
            'photo_modifications':'Resized to the registered camera frame. Credit and source added below.',
            'plate_license':'https://creativecommons.org/licenses/by-sa/3.0/','model_render_sha256':sha(render),'plate_sha256':sha(out)}
    out.with_suffix('.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('original','render','output'):p.add_argument(k,type=Path)
    a=p.parse_args();generate(a.original,a.render,a.output)
