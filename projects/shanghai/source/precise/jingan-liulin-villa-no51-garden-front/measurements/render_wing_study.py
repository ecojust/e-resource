"""Assemble four garden-façade views rendered from one delivered mesh."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
def draw(folder,out,mesh,role):
    data=json.loads((folder/'views.json').read_text());views={v['view']:v for v in data['views']}
    canvas=Image.new('RGB',(1400,1054),'#f6f2e9');pen=ImageDraw.Draw(canvas)
    font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
    title=ImageFont.truetype(font,34);body=ImageFont.truetype(font,21);small=ImageFont.truetype(font,16)
    pen.text((35,14),'柳林别墅51号  /  两翼凸窗与花园',fill='#292b28',font=title)
    pen.text((36,69),'愚园路532弄  ·  '+('近景模型' if role=='full'else'远景模型')+'  ·  依据高参88于2014年拍摄的院内、院外两幅照片重建',fill='#53554d',font=small)
    plates={}
    for i,(key,label) in enumerate([('street','两翼三层凸窗与退入柱廊'),('right-bay','右凸窗三面与水平灰檐'),('woodwork','左翼二层开启的木扇与帘片'),('frontage','花园门牌、石柱与院内视线')]):
        row=views[key];file=folder/row['image'];signature=sha256(file.read_bytes()).hexdigest()
        assert signature==row['image_sha256']
        im=Image.open(file).convert('RGB');im.thumbnail((656,414),Image.Resampling.LANCZOS)
        c=i%2;r=i//2;x=35+c*682;y=115+r*460
        canvas.paste(im,(x+(656-im.width)//2,y));pen.text((x,y+418),label,fill='#343631',font=body)
        plates[key]={'image':file.name,'image_sha256':signature,'eye':row['eye'],'target':row['target']}
    pen.text((35,1020),'两翼的正面和斜面共取十五樘可辨的窗。几何、材质及本图均由本项目制作。',fill='#50554c',font=small)
    out.parent.mkdir(parents=True,exist_ok=True);canvas.save(out,quality=90)
    report=dict(model_sha256=sha256(mesh.read_bytes()).hexdigest(),board_sha256=sha256(out.read_bytes()).hexdigest(),role=role,views=plates,photographic_pixels_embedded=False)
    out.with_suffix('.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
    parser=ArgumentParser();parser.add_argument('views',type=Path);parser.add_argument('mesh',type=Path);parser.add_argument('role',choices=('full','lod'));parser.add_argument('output',type=Path)
    a=parser.parse_args();draw(a.views,a.output,a.mesh,a.role)
