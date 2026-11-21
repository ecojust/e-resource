"""Original ochre facing-brick artwork and the grey dressed-stone surround."""
from pathlib import Path
import random
import numpy as np
from PIL import Image,ImageDraw
BRICK='Meifeng ochre brick strips'
STONE='Meifeng silver grey dressed stone'
TRIM='Meifeng dressed stone nosing'
JOINT='Meifeng recessed stone joints'
BASE='Meifeng grey granite base'
STEEL='Meifeng black steel glazing'
GLASS='Meifeng shaded upper window'
GROUND_GLASS='Meifeng shop and vestibule glass'
TIMBER='Meifeng weathered sign board'
IRON='Meifeng dark rainwater iron'
GOLD='Meifeng worn brass fixings'
TERRAZZO='Meifeng doorway floor'
FACING=Path(__file__).with_name('ochre-brick-fin.png')
MATERIALS={m:{'color':rgb,'roughness':rough}for m,rgb,rough in [
    (BRICK,[1.,1.,1.],.90),(STONE,[.55,.547,.508],.87),(TRIM,[.639,.628,.577],.80),
    (JOINT,[.366,.360,.334],.91),(BASE,[.42,.429,.409],.84),(STEEL,[.089,.101,.103],.50),
    (GLASS,[.254,.282,.284],.30),(GROUND_GLASS,[.132,.168,.167],.33),(TIMBER,[.493,.302,.144],.88),
    (IRON,[.17,.17,.152],.68),(GOLD,[.467,.337,.152],.57),(TERRAZZO,[.52,.52,.492],.78)]}
MATERIALS[BRICK]['texture']=str(FACING)
def make_original():
    # Build one whole fin as a clamped atlas. The vertical centre seam is the
    # darker red-brown strip visible in the district's detail photograph.
    width,height=160,1024
    rng=random.Random(495110049)
    image=Image.new('RGB',(width,height),(163,155,129));draw=ImageDraw.Draw(image)
    rows=84;brickw=32
    for row in range(rows):
        low=round(height*row/rows)+1;high=round(height*(row+1)/rows)-1
        offset=-(row%2)*brickw//2
        for start in range(offset,width,brickw):
            above=(start+brickw/2)/width
            base=(140,118,94)if .35<above<.64 else(158,147,116)
            shade=rng.randint(-12,12)
            color=tuple(max(0,min(255,k+shade))for k in base)
            draw.rectangle((start+1,low,start+brickw-1,high),fill=color)
            draw.line((start+2,low+1,start+brickw-2,low+1),fill=tuple(min(255,k+5)for k in color))
    pixels=np.asarray(image,dtype=np.int16)
    texture=np.random.default_rng(192004).integers(-3,4,(height,width,1),dtype=np.int16)
    Image.fromarray(np.clip(pixels+texture,0,255).astype('uint8')).save(FACING,optimize=True)
if __name__=='__main__':make_original()
