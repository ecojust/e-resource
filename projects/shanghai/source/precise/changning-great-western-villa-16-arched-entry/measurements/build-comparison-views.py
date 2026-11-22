"""Pair four licensed architectural photographs or crops with the same features in the published near model."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).absolute().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
CATALOG=[('two-arched-openings','street',6,[0,0,1,1],'外侧红砖券、内层木拱门和门后楼梯共轴。'),
         ('radial-brick-face','brick',6,[.06,.02,.89,.61],'出挑拱砖之间的径向灰缝有别于券腹纵向错缝。'),
         ('letterbox-and-slate','relief',7,[.095,.022,.897,.865],'金色16号、圆形边框、花叶和凸出箱架的铸件彼此对应。'),
         ('stair-noses-and-post','stair',8,[.075,.12,.8,.997],'十六道踏步和右侧的红色起步柱可分别观察。')]
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('exports',type=Path);e=ap.parse_args().exports;out=HERE.parent/'study-views'
    s={a['index']:a for a in json.loads((HERE/'photographic-source.json').read_bytes())['photographs']}
    six=json.loads((e/'six-source-backed-exports.json').read_bytes());font=ImageFont.truetype('DejaVuSans.ttf',15);rows=[]
    for name,view,idx,limits,ob in CATALOG:
        a=s[idx];source=HERE/a['public_file'];assert sha(source)==a['public_file_sha256'];photo=Image.open(source)
        bounds=[round(x*(photo.width if i%2==0 else photo.height))for i,x in enumerate(limits)]
        board=Image.new('RGB',(930,435),'#f0ede4');m=e/'full-views'/(view+'.jpg')
        for x,im in [(12,photo.crop(bounds)),(472,Image.open(m))]:
            im.thumbnail((446,383),Image.Resampling.LANCZOS);board.paste(im,(x+(446-im.width)//2,8+(383-im.height)//2))
        d=ImageDraw.Draw(board);d.text((12,404),'WQL | 14 June 2018 | CC BY-SA 4.0',font=font,fill='#303638');d.text((472,404),'Model | '+view,font=font,fill='#303638')
        dst=out/(name+'.jpg');board.save(dst,quality=91,optimize=True)
        rows.append(dict(file=dst.name,comparison_sha256=sha(dst),source_sha256=a['sha256'],licensed_source_file=a['public_file'],reference_crop=bounds,model_view=view,model_view_sha256=sha(m),decoded_geometry_sha256=six['decoded-full.glb']['sha256'],observation=ob))
    (HERE/'photographic-comparisons.json').write_text(json.dumps(dict(signed_views=rows,license='CC BY-SA 4.0'),ensure_ascii=False,indent=2)+'\n')
