"""Original dark fired brick bond in street metres, registered continuously across the bays."""
from pathlib import Path
from random import Random

IMAGE = Path(__file__).with_name('taishan-brick.png')
MATERIAL = 'School dark red Taishan brick'
WEST = 16.0
WIDTH = 44.0
HEIGHT = 29.0

def uv(point):
    x,y,z=point
    return ((x+y-WEST)/WIDTH, 1.-(z+.20)/HEIGHT)

def draw(path=IMAGE):
    from PIL import Image, ImageDraw
    rng=Random(1928219)
    nx,ny=176,390
    w,h=1760,1560
    image=Image.new('RGB',(w,h),(121,104,96)); pen=ImageDraw.Draw(image)
    for j in range(ny):
        for i in range(-1,nx):
            a=10*i+5*(j%2); top=j*4
            shade=rng.randrange(-9,10)
            tint=rng.choice([-4,-2,0,1,2,3])
            chip=(100+shade+tint,74+shade,74+shade-tint)
            pen.rectangle((a,top,a+8,top+2),fill=chip)
            if i%7==j%7:
                pen.point((a+1,top),fill=(chip[0]+7,chip[1]+5,chip[2]+3))
    image.save(path,optimize=True)

def apply(builder):
    if not IMAGE.is_file():
        draw()
    builder.palette[MATERIAL]={'color':[1.,1.,1.],'metallic':0.,'roughness':.92,'texture':str(IMAGE)}
    for part in builder.parts:
        if part['material']==MATERIAL:
            mapped=[uv(v) for v in part['vertices']]
            assert all(0<=u<=1 and 0<=v<=1 for u,v in mapped),part['label']
            part['texcoords']=mapped

if __name__=='__main__':
    draw()
