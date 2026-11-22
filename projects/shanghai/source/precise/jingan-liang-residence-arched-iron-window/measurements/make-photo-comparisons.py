"""Compose attributed comparisons between Aaron Zhu's source window photograph and model renders."""
from pathlib import Path
import os,json,hashlib
from PIL import Image,ImageDraw,ImageFont
HERE=Path(__file__).absolute().parent
study=HERE.parent/'study-views';photo=Path(os.environ.get('LIANG_WINDOW_PHOTO',HERE.parent/'61-window.jpg'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
font=lambda size:ImageFont.truetype('NotoSansCJK-Regular.ttc',size,index=2)
with Image.open(photo)as im:
    digest=sha(photo);assert digest==json.loads((HERE/'window-photo-source.json').read_bytes())['sha256']
    plates=[]
    for name,view,label,rect in [('window-source-and-model','courtyard','院窗、放射砖券与石窗台',None),('scroll-source-and-model','medallion','下窗环形花心与穿透的铁条',(136,431,392,568))]:
        if rect:
            ratio=im.width/510;ref=im.crop(tuple(round(x*ratio)for x in rect))
        else:ref=im.copy()
        can=Image.new('RGB',(1140,615),'#f4f0e8');dr=ImageDraw.Draw(can);dr.text((28,14),'梁氏民宅  /  '+label,font=font(28),fill='#2c3731')
        for i,(img,caption) in enumerate([(ref,'Aaron Zhu，2012年7月4日'),(Image.open(study/(view+'.jpg')),'项目近景模型')]):
            x=22+i*555;img.thumbnail((540,457),Image.Resampling.LANCZOS);can.paste(img,(x+(540-img.width)//2,74+(457-img.height)//2));dr.text((x+5,540),caption,font=font(18),fill='#39413c')
        dr.text((28,576),'照片和改作按 CC BY-SA 3.0 共享  ·  原图和许可链接见 SOURCES-LICENSE.md',font=font(16),fill='#595d55')
        f=study/(name+'.jpg');can.save(f,quality=90,optimize=True);plates.append(dict(name=name,file=f.name,sha256=sha(f),model_view=view,view_sha256=sha(study/(view+'.jpg')),photo_sha256=digest,photographer='Aaron Zhu',license='CC BY-SA 3.0',crop_working_px=rect))
(HERE/'study-plates.json').write_text(json.dumps(dict(plates=plates),ensure_ascii=False,indent=2)+'\n')
