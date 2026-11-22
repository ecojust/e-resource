"""Typeset the published municipal inscription on an original plain ground."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import argparse
def draw(output,font_path):
    im=Image.new('RGB',(640,552),(232,230,213));d=ImageDraw.Draw(im)
    def put(y,text,size):
        f=ImageFont.truetype(str(font_path),size)
        d.text((320,y),text,font=f,anchor='mt',fill=(73,72,61))
    put(51,'优秀历史建筑',45);put(113,'HERITAGE ARCHITECTURE',23)
    put(207,'原南洋大楼，公寓建筑。1927年竣工。',26)
    put(257,'砖混结构，有哥特复兴风格特征。',25)
    put(304,'沿街为弧形转角，平屋顶。',24)
    put(421,'上海市人民政府',29);put(472,'2015年8月17日',20)
    im.save(output,optimize=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc'))
    p.add_argument('--output',type=Path,default=Path(__file__).with_name('204-protection-tablet.png'));args=p.parse_args();draw(args.output,args.font)
