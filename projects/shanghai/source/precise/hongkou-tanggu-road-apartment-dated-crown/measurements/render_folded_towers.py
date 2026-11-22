"""Make a study sheet from a supplied decoded crown GLB and the ordinary proof views."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).resolve().parent
PROJECT=next(x for x in HERE.parents if (x/'tools/package_architectural_model.py').is_file())
AUDIT=PROJECT/'data/audit/tanggu-road-apartment-dated-crown-v1'
BG='#f6f3ed';INK='#2d2826';MUTED='#645951';RULE='#bca48f';ACCENT='#834829'

def font(size,bold=False):
    return ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+('Bold'if bold else'Regular')+'.ttc',size,index=2)
def caption(draw,pos,title,note):
    x,y=pos;draw.text((x,y),title,font=font(24,True),fill=INK);draw.text((x,y+38),note,font=font(16),fill=MUTED)
def pane(sheet,file,rect):
    src=Image.open(file).convert('RGB')
    # Crop the neutral renderer margin, keep every visible edge of the model.
    import numpy as np
    pixels=np.asarray(src).astype(int);bg=pixels[0,0]
    sy,sx=np.nonzero(np.max(abs(pixels-bg),axis=2)>25)
    if len(sx):src=src.crop((max(0,sx.min()-10),max(0,sy.min()-12),min(src.width,sx.max()+11),min(src.height,sy.max()+13)))
    x,y,w,h=rect
    tile=Image.new('RGB',(w,h),tuple(int(c)for c in bg));src.thumbnail((w,h),Image.Resampling.LANCZOS)
    tile.paste(src,((w-src.width)//2,(h-src.height)//2));sheet.paste(tile,(x,y))

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mesh',type=Path);p.add_argument('views',type=Path);p.add_argument('work',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();a.work.mkdir(exist_ok=True,parents=True)
    report=runpy.run_path(AUDIT/'render-with-stone-mips.py')['render'](a.mesh,a.work,[
      ('upward',[3.5,-18.5,-5.7],[0.,0.,2.8],18.4),
      ('capital',[-3.1,-4.5,3.32],[-3.88,-.31,3.5],1.74),
      ('blind',[9.2,-8.5,1.46],[6.1,-.79,.96],4.78)],920,530)
    runpy.run_path(AUDIT/'sunlight.py')['cast_shadows'](a.mesh,a.work,report)
    sheet=Image.new('RGB',(1380,1090),BG);d=ImageDraw.Draw(sheet);x=48
    d.text((x,26),'上海建筑细部研究　／　虹口 · 塘沽路',font=font(19),fill=ACCENT)
    d.text((x,65),'公安大楼的折角楼冠',font=font(47,True),fill=INK)
    d.text((x,142),'两塔各有三面向前的折面。浅色竖肋沿前方两个折角上升，在灰色檐帽下方分别收头。',font=font(23),fill=MUTED)
    d.line((x,198,1332,198),fill=RULE,width=2)
    pane(sheet,a.work/'upward.jpg',(48,220,800,340))
    pane(sheet,a.views/'above.jpg',(866,220,466,340))
    caption(d,(48,568),'仰看两侧塔冠','独立模型从下方观看；中央匾额和两侧浅色端柱帽完整保留。')
    caption(d,(866,568),'上缘与折面','俯视能分辨灰色压边和展品后方的剖切边。')
    pane(sheet,a.work/'capital.jpg',(48,661,593,286))
    pane(sheet,a.work/'blind.jpg',(659,661,673,286))
    caption(d,(48,952),'端柱冠石','冠石有浅槽，下缘外挑成一道窄托。')
    caption(d,(659,952),'塔身凹板','三块折面分别开浅槽，凹底与边面有真实高差。')
    d.line((x,1040,1332,1040),fill=RULE)
    d.text((x,1050),'据 2015 年人民网上海与 2016 年建筑组照绘制。图中均为模型渲染；尺寸以年份匾全宽为一个比例单位。',font=font(16),fill=MUTED)
    a.output.parent.mkdir(parents=True,exist_ok=True);sheet.save(a.output,quality=90,subsampling=0)
    meta={'mesh_sha256':hashlib.sha256(a.mesh.read_bytes()).hexdigest(),'three_detail_views':report['views'],
          'sheet_sha256':hashlib.sha256(a.output.read_bytes()).hexdigest(),'embedded_reference_photographs':False}
    a.output.with_suffix('.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
