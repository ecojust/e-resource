"""Pair licensed photo details with views rendered from the already decoded near model."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image,ImageDraw,ImageFont,ImageOps

here=Path(__file__).absolute().parent
catalog=[('street-gable-2018', 'street', [356, 14, 759, 440], '街照中曲边山墙、三联绿色拱窗与凸阳台上下共轴。'), ('attic-and-curve', 'attic', [420, 25, 684, 203], '绿色山墙绕上部大拱窗收窄，窗框坐进抹灰洞口。'), ('three-window-heads', 'arches', [470, 225, 691, 307], '三道近似半圆拱顶下保留深绿色横档和小分格。'), ('pierced-stone-balcony', 'balcony', [461, 301, 704, 392], '凸阳台左面斜向接入侧墙，两段栏板的圆环交叉斜撑都可以透空。')]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('export_directory',type=Path);args=ap.parse_args()
    m=json.loads((here/'photographic-source.json').read_bytes());source=Image.open(here/m['crop_file']).convert('RGB')
    assert sha(here/m['crop_file'])==m['crop_sha256']
    six=json.loads((args.export_directory/'six-source-backed-exports.json').read_bytes());records=[]
    out=here.parent/'study-views';font=ImageFont.truetype('DejaVuSans.ttf',15)
    for name,view,crop,observation in catalog:
        x0,y0,x1,y1=m['crop_original_pixels'];region=[round(crop[0]*5312/1062)-x0,round(crop[1]*2988/597)-y0,round(crop[2]*5312/1062)-x0,round(crop[3]*2988/597)-y0]
        assert 0<=region[0]<region[2]<=source.width and 0<=region[1]<region[3]<=source.height
        model=args.export_directory/'full-views'/(view+'.jpg');img=Image.open(model).convert('RGB');board=Image.new('RGB',(930,435),'#f1eee6')
        for x,frame in [(12,source.crop(region)),(472,img)]:
            frame.thumbnail((446,383),Image.Resampling.LANCZOS)
            board.paste(frame,(x+(446-frame.width)//2,9+(383-frame.height)//2))
        d=ImageDraw.Draw(board);d.text((12,403),'Antigng | 13 February 2018 | CC BY-SA 4.0',fill='#2c3337',font=font);d.text((472,403),'Model | '+view,fill='#2c3337',font=font)
        target=out/(name+'.jpg');board.save(target,quality=91,optimize=True)
        records.append(dict(file=target.name,comparison_sha256=sha(target),source_sha256=m['sha256'],crop_source_sha256=m['crop_sha256'],local_crop=region,
                            model_view=view,model_view_sha256=sha(model),decoded_geometry_sha256=six['decoded-full.glb']['sha256'],observation=observation))
    (here/'photographic-comparisons.json').write_text(json.dumps(dict(signed_views=records),ensure_ascii=False,indent=2)+'\n')
