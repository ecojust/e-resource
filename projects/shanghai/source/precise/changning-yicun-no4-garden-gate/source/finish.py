"""Generate original materials for the photographed gate. No image pixels are copied."""
from PIL import Image,ImageDraw,ImageFilter
from io import BytesIO
from math import sin,cos,pi
import random
PALETTE={
 'render':('Warm lime-rendered gate pillars',(211,174,132)), 'pale':('Pale plaster on the photographed gable',(222,209,187)),
 'wing':('Pale rose render on side return',(217,188,163)), 'cap':('Dark weathered cement edge',(135,126,106)),
 'foot':('Weathered grey at base of gateposts',(152,151,140)),'paint':('Worn blue-green painted iron and irregular oxide',(61,109,97)),
 'oxide':('Red-brown iron oxide',(111,62,39)), 'edge':('Painted steel edge',(76,84,62)), 'hardware':('Blackened hardware',(65,71,69)),
 'plaque':('Blue green enamel house-number plaque',(28,70,70)), 'ivory':('Raised light numeral',(237,235,213)),
 'fastener':('Dull plated fixing',(170,167,147)), 'glass':('Blue-grey steel sash glass',(92,119,121)),
 'steel':('Dark painted glazing bars',(59,67,63)),'bead':('Edge of steel profiles',(99,109,102)),
 'case':('Air-conditioner exterior case',(193,192,177)), 'dark':('Shaded inside the three vent holes',(52,48,42)),
 'reveal':('Shadowed render returns',(172,156,137)), 'clay':('Aged dull red roof tiles',(125,76,57)),
 'clayedge':('Raised edges of roof tiles',(152,97,72))}
TEXTURES={'render','pale','paint','cap','clay'}
def make_png(mat):
 n=256 if mat=='paint' else 96;rng=random.Random(872+list(PALETTE).index(mat))
 def noise(side):
    src=Image.frombytes('L',(side,side),bytes(rng.randrange(256)for _ in range(side*side)))
    return src.resize((n,n),Image.Resampling.BICUBIC).load()
 coarse=noise(6);mid=noise(22);grit=noise(54); pic=Image.new('RGB',(n,n));pixels=pic.load();base=PALETTE[mat][1]
 for j in range(n):
    for i in range(n):
        grain=(rng.random()-.5)*9+(grit[i,j]-128)*.049+(coarse[i,j]-128)*.06
        if mat=='paint':
            u=i/(n-1);v=j/(n-1); c=.48*(coarse[i,j]/255)+.33*(mid[i,j]/255)+.19*(grit[i,j]/255)
            # Image top aligns to the corroded head of the leaves. A second narrow
            # corrosion band follows their bottom and the exposed perimeter.
            top=.40*(1-v)**2.6; edge=.22*max(0,1-min(u,1-u)*15); bottom=.22*max(0,1-(1-v)*12)
            p=max(0,min(1,(c+top+edge+bottom-.62)*10))
            rust=(123+.22*(mid[i,j]-120),65+.13*(coarse[i,j]-128),39)
            color=[base[k]*(1-p)+rust[k]*p for k in range(3)]
        else:
            color=base
            if mat=='clay':grain+=11*cos(pi*2*i/(n/6))+(8 if j%32<2 else 0)
        pixels[i,j]=tuple(max(0,min(255,round(q+grain)))for q in color)
 bio=BytesIO();pic.save(bio,'PNG',compress_level=7);return bio.getvalue()
