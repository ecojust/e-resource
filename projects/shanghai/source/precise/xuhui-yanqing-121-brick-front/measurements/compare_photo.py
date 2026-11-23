"""Pair the attributed 2018 photograph with the matching street camera of the finished mesh."""
from pathlib import Path
import argparse
from PIL import Image,ImageFont,ImageDraw

def comparison(photo,render,out):
    frame=Image.open(render).convert('RGB');reference=Image.open(photo).convert('RGB')
    reference=reference.crop((0,0,reference.width,round(reference.width*690/1300))).resize(frame.size,Image.Resampling.LANCZOS)
    w,h=frame.size;pad=22;canvas=Image.new('RGB',(2*w+3*pad,h+138),(246,244,237));draw=ImageDraw.Draw(canvas)
    family='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';large=ImageFont.truetype(family,27);small=ImageFont.truetype(family,17)
    draw.text((pad,5),'延庆路121号住宅  ·  北侧临街立面',font=large,fill=(42,42,39))
    canvas.paste(reference,(pad,54));canvas.paste(frame,(2*pad+w,54))
    draw.text((pad,59+h),'Antigng 摄于2018年2月7日  ·  Wikimedia Commons  ·  CC BY-SA 4.0',font=small,fill=(51,50,47))
    draw.text((2*pad+w,59+h),'按同一视角渲染的临街砖墙、凸窗和券门',font=small,fill=(51,50,47))
    draw.text((pad,96+h),'对照图保留拍摄时可见的遮挡。模型采用街景估算尺度；北侧街面以外的住宅范围待核。',font=small,fill=(77,76,71))
    canvas.save(out,quality=91,optimize=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('original_photo',type=Path);ap.add_argument('render',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args();comparison(a.original_photo,a.render,a.output)
