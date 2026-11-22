"""Draw the two roof windows from the released model with its actual glass transparency."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
sys.path[:0]=[str(BASE/'xuhui-pathe-records-office/measurements/city-contact'),
              str(BASE/'jingan-jkk-apartments-changle-street-front/measurements')]
from glb_triangles import load_triangles, material_appearance
from render_central_steel_views import draw_mesh


def label(draw,x,y,text,size,bold=False,color='#283c3b'):
    face='Bold' if bold else 'Regular'
    font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-'+face+'.ttc',size,index=2)
    draw.text((x,y),text,font=font,fill=color)


def render(asset,layout_file,out):
    layout=json.loads(layout_file.read_bytes())
    triangles,ids,names,signature=load_triangles(asset)
    appearances=material_appearance(asset)['materials']
    keep=np.isin(ids,[i for i,n in enumerate(names) if n.startswith('Shanyin dormer | ')])
    colors=[appearances[n]['baseColorFactor'] if n in appearances else [1,1,1,1] for n in names]
    blend=[appearances.get(n,{}).get('alphaMode')=='BLEND' for n in names]
    assert sum(keep)>900 and 'Shanyin dormer | dark eaves gutter' in names
    mesh=(triangles[keep],ids[keep],np.array(colors),np.array(blend))
    canvas=Image.new('RGB',(1280,1010),'#f8f5ed')
    pen=ImageDraw.Draw(canvas)
    label(pen,44,17,'山阴路209弄3号的两扇屋窗',39,True)
    label(pen,45,84,'2015年正面机位与另一幅具名照片的低机位　·　原模型投影',21)
    pen.line((45,128,1235,128),fill='#9faca4',width=2)
    rows=[]
    for name,key,y in [('2015年正面','camera_P',161),('街面仰视','second_camera_P',562)]:
        cam=np.asarray(layout[key])
        im,stats=draw_mesh(mesh,cam,{},(1440,626),'all')
        assert stats['glass_blended_pixels']>100
        canvas.paste(im.resize((720,313),Image.Resampling.LANCZOS),(42,y))
        label(pen,792,y+10,name,27,True)
        if key=='camera_P':
            labels=['左窗的白漆竖框承在红色山尖之下。','右窗前檐分黑色水槽、红檐板与浅色檐底。','斜向灰色收边上方有八段橘色瓦压顶，','其下露出一片三角形小瓦面。']
        else:
            labels=['街上仰望可见两处檐挑的底面。','左檐约挑出0.36米，右檐约0.35米。','原照下方的街檐遮住了两窗脚。','右窗斜边的后端只在2015年照可辨。']
        for i,t in enumerate(labels):label(pen,792,y+79+i*43,t,19)
        rows.append(dict(view=name,camera_key=key,source_native_px=layout[key],render=stats))
    pen.line((45,526,1235,526),fill='#a9b6ad',width=1)
    label(pen,44,898,'窗脚与坡屋顶的接缝由2015年照片约束。图中玻璃按模型的透明度叠绘。',20)
    label(pen,44,949,'照片测量据 Fayhoo（2015，CC BY-SA 3.0）及老房子爱好者《山阴路上的优秀历史保护建筑和名人故居》。',16,False,'#5b6763')
    out.parent.mkdir(exist_ok=True,parents=True)
    canvas.save(out,quality=91,subsampling=0)
    report=dict(source_mesh=signature,layout_sha256=sha256(layout_file.read_bytes()).hexdigest(),
                original_model_plate=out.name,plate_sha256=sha256(out.read_bytes()).hexdigest(),
                triangles_from_dormer_materials=int(keep.sum()),photo_pixels_included=False,views=rows)
    out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    args=argparse.ArgumentParser(description=__doc__)
    for k in ('asset','layout','plate'):args.add_argument(k,type=Path)
    opt=args.parse_args()
    print(render(opt.asset,opt.layout,opt.plate)['plate_sha256'])
