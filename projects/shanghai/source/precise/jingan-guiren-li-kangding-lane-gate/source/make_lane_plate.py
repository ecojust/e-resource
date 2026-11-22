"""Draw the two observed lines on the green address plate with an openly licensed typeface."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def draw_plate(output, font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'):
    img=Image.new('RGB',(512,154),(30,104,77))
    pen=ImageDraw.Draw(img)
    pen.rounded_rectangle((3,3,508,150),6,outline=(164,176,150),width=2)
    def line(text,y,size):
        face=ImageFont.truetype(font,size,index=2)
        pen.text((256,y),text,anchor='mm',font=face,fill=(233,231,201),stroke_width=0)
    line('3弄 3-14 号',49,49)
    line('康  定  东  路',110,33)
    img.save(output)
if __name__=='__main__':draw_plate(Path(__file__).with_name('guiren-address-plate.png'))
