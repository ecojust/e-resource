"""Compose a numeric control overlay from original gate renders and recorded source points."""
import argparse,json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

FONTS='/usr/share/fonts/opentype/noto/NotoSansCJK-'
def font(n,heavy=False):
    return ImageFont.truetype(FONTS+('Bold' if heavy else 'Regular')+'.ttc',n,index=2)
def panel(sheet,renders,name,crop,rect,source_points,centres):
    image=Image.open(renders/(name+'-model.jpg')).convert('RGB')
    image=image.crop((0,0,image.width,image.height-36))
    width,height=rect[2],rect[3]
    image=image.resize((width,height),Image.Resampling.LANCZOS)
    d=ImageDraw.Draw(image)
    def xy(uv):
        return (round((uv[0]-crop[0])*width/(crop[2]-crop[0])),round((uv[1]-crop[1])*height/(crop[3]-crop[1])))
    for uv in source_points:
        x,y=xy(uv);d.ellipse((x-4,y-4,x+4,y+4),outline='#58fcde',width=2)
    for uv in centres:
        x,y=xy(uv);d.line((x-3,y,x+3,y),fill='#ffca63',width=1);d.line((x,y-3,x,y+3),fill='#ffca63',width=1)
    sheet.paste(image,rect[:2])
def build(folder):
    renders=folder/'registered-renders';reg=folder/'registration'
    f=json.loads((reg/'raw-frieze.json').read_text())['views']
    h=json.loads((reg/'raw-gate-hardware.json').read_text())['samples']
    sheet=Image.new('RGB',(1256,900),'#f5f1e9');d=ImageDraw.Draw(sheet);ink='#202b2f';muted='#485a5c'
    d.text((30,18),'陕西南路222弄20号院门',font=font(35,True),fill=ink)
    d.text((32,72),'按2016年两幅实拍的相机位置渲染  ·  绿色圆圈为实拍测点，金色十字为模型卵饰中心',font=font(18),fill=muted)
    photo=[a['pixel'] for a in h if a['view']=='06']
    panel(sheet,renders,'2016-gate',[0,0,690,1038],(31,133,465,700),photo+[a['pixel']for a in f['06']['checks']],[])
    panel(sheet,renders,'2016-cornice',[45,76,606,290],(532,156,692,264),[a['pixel']for a in f['07']['checks']],[a['projected_egg_centre_px']for a in f['07']['checks']])
    d.text((532,115),'檐口三个正面区段',font=font(22,True),fill=ink)
    d.text((533,432),'左段5枚，中央13枚，右段6枚。两段内折面各另有1枚。',font=font(17),fill=muted)
    panel(sheet,renders,'2016-hardware',[140,640,597,900],(535,503,456,260),[a['pixel']for a in h if a['view']=='06' and a['pixel'][1]>640],[])
    d.text((532,464),'双门环及门铃',font=font(22,True),fill=ink)
    d.multiline_text((1013,545),'两枚兽面\n各有一只\n可透视的环。',font=font(21),fill=ink,spacing=10)
    d.text((535,784),'06号图的卵饰中心偏差中位数为9.5像素，07号图为1.5像素。',font=font(17),fill=muted)
    d.text((32,853),'模型及制图：e-resource　·　测点依据：高参88《陕西南路222弄优秀历史建筑》（2016年2月2日）',font=font(16),fill=muted)
    sheet.save(reg/'2016-gate-controls.jpg',quality=94,optimize=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    build(p.parse_args().folder)
