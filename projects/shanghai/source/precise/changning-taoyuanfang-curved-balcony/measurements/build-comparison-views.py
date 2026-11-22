"""Pair licensed photo details with views rendered from the already decoded near model."""
from pathlib import Path
import argparse,hashlib,json
from PIL import Image,ImageDraw,ImageFont,ImageOps

here=Path(__file__).absolute().parent
catalog=[('balcony-end-in-2018','street',[391,61,846,419],'端部浅色隔墙、折弧板边与中央深色花铁在同一开间。'),
 ('scrolled-centre-panel','scroll',[522,241,588,339],'矩形格片内三枝斜叶，两边各有上下回卷，铁饰在上下栏杆之间构成插片。'),
 ('folding-steel-carrier','carrier',[383,251,466,326],'四根亮杆放在交叉扁钢架上，交叉处和端点有圆头铆钉。'),
 ('balcony-edge-in-oblique-light','moulding',[410,267,742,403],'下部两道浅色线脚随楼板先缓转外凸，再收回端部。')]
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
        d=ImageDraw.Draw(board);d.text((12,403),'Antigng | 10 February 2018 | CC BY-SA 4.0',fill='#2c3337',font=font);d.text((472,403),'Model | '+view,fill='#2c3337',font=font)
        target=out/(name+'.jpg');board.save(target,quality=91,optimize=True)
        records.append(dict(file=target.name,comparison_sha256=sha(target),source_sha256=m['sha256'],crop_source_sha256=m['crop_sha256'],local_crop=region,
                            model_view=view,model_view_sha256=sha(model),decoded_geometry_sha256=six['decoded-full.glb']['sha256'],observation=observation))
    (here/'photographic-comparisons.json').write_text(json.dumps(dict(signed_views=records),ensure_ascii=False,indent=2)+'\n')
