"""Generate a small original seamless mineral render, with deterministic grain."""
from pathlib import Path
from random import Random
from PIL import Image
def write_texture(path):
 r=Random(1887);width=448;height=224;pixels=[]
 for y in range(height):
  for x in range(width):
   grain=r.gauss(0,7.3)+(13 if r.random()<.055 else 0)-r.choices([0,11,24],[92,6,2])[0]
   pixels.append(tuple(round(max(0,min(255,base+grain)))for base in (220,210,191)))
 im=Image.new('RGB',(width,height));im.putdata(pixels);im.save(path,optimize=True)
if __name__=='__main__':write_texture(Path(__file__).with_name('wall-aggregate.png'))
