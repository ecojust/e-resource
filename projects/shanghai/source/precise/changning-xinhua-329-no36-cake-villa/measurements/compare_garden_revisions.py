"""Document first/second geometry at a fixed registered viewing station using each actual render."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse,hashlib,json
cli=argparse.ArgumentParser(description=__doc__)
for n in ['first_directory','final_directory','output']:cli.add_argument(n,type=Path)
a=cli.parse_args();views=['historic-garden','district-2024'];out=Image.new('RGB',(880,394),'#eeeae0');pen=ImageDraw.Draw(out)
font=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',16,index=2)
pen.text((18,7),'首版　圆楼庭院窗门与开廊',fill='#25231d',font=font);pen.text((455,7),'细化版　实数玻璃砖、错层短栏与砖饰',fill='#25231d',font=font)
record={}
for i,v in enumerate(views):
 for j,d in enumerate([a.first_directory,a.final_directory]):
  p=d/(v+'-model.jpg');im=Image.open(p);im.thumbnail((420,169));out.paste(im,(11+j*440+(420-im.width)//2,35+i*175+(165-im.height)//2));record[f'{j}/{v}']=hashlib.sha256(p.read_bytes()).hexdigest()
out.save(a.output,quality=94,subsampling=0);print(json.dumps(record,indent=2))
