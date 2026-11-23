from pathlib import Path
import json,argparse
import numpy as np
from scipy.optimize import least_squares
from scipy.ndimage import gaussian_filter1d
from PIL import Image,ImageDraw
ap=argparse.ArgumentParser();ap.add_argument('original_photo',type=Path);ap.add_argument('output',type=Path);options=ap.parse_args();options.output.mkdir(parents=True,exist_ok=True)
im=Image.open(options.original_photo).convert('L');scale=im.width/1300
# u,z are metres. A vertical line lies in the brick plane; local +u follows the wall to the photograph's right.
anchors=[(-3.12,4.40,823.5,297.),(-5.83,4.53,616.3,311.),(-3.12,.89,831.0,550.)]
levels=[[(76,247),(934,161)],[(265,331),(938,297)],[(254,421),(923,411)],[(271,531),(943,554)]]
verticals=[[(295,246),(292,324)],[(340,241),(337,322)],[(441,226),(438,313)],[(491,222),(490,310)],[(586,212),(582,307)],[(645,204),(646,305)],[(792,193),(792,290)],[(852,183),(850,290)],[(274,423),(269,530)],[(337,422),(335,530)],[(801,418),(799,551)],[(865,418),(862,552)]]
# Refine the two long masonry courses against the original scan. Occluding pipes and trees are downweighted.
G=np.asarray(im,dtype=np.float32)/255
Gy=np.abs(np.gradient(gaussian_filter1d(G,1.,axis=0),axis=0));
def fit_line(line):
 p,q=np.array(line);x=np.arange(p[0],q[0],.64);t=(x-p[0])/(q[0]-p[0]);row=np.zeros((25,25));ofs=np.linspace(-4,4,25)
 for i,l in enumerate(ofs):
  for j,r in enumerate(ofs):
   y=(p[1]+l)*(1-t)+(q[1]+r)*t
   val=Gy[np.rint(y*scale).astype(int),np.rint(x*scale).astype(int)];row[i,j]=np.quantile(val,.65)
 i,j=np.unravel_index(np.argmax(row),row.shape);return [[float(p[0]),float(p[1]+ofs[i])],[float(q[0]),float(q[1]+ofs[j])]]
levels=[fit_line(x) for x in levels];print('levels',levels)
def m(v):return np.r_[v,1.].reshape(3,3)
def position(v,px):
 p=m(v)@[*((np.array(px)-[800,300])/500),1];return p[:2]/p[2]
def losses(v):
 r=[]
 for x,z,a,b in anchors:r.extend((position(v,(a,b))-[x,z])*8)
 for p,q in levels:r.append(position(v,p)[1]-position(v,q)[1])
 for p,q in verticals:r.append(position(v,p)[0]-position(v,q)[0]);
 return r
v=least_squares(losses,[6.5,0,-3.4,0,-7.1,4.4,-.2,0],loss='soft_l1',f_scale=.025)
H=(m(v.x)@np.array([[1/500,0,-800/500],[0,1/500,-300/500],[0,0,1]]));H/=H[2,2];print('H',H,'res',np.array(losses(v.x)).round(4));I=np.linalg.inv(H)
def to_img(p):q=I@[*p,1];return tuple(q[:2]/q[2]);
canvas=Image.open(options.original_photo).convert('RGB');canvas.thumbnail((1300,1300));draw=ImageDraw.Draw(canvas)
for k in range(-19,1):
 a=to_img([k,.1]);b=to_img([k,7.6]);draw.line((a,b),fill='cyan',width=1);draw.text(b,str(k),fill='yellow')
for z in np.arange(0,8.5,.5):
 a=to_img([-19,z]);b=to_img([-.3,z]);draw.line((a,b),fill='yellow' if z%1==0 else 'orange',width=1)
canvas.save(options.output/'registered.jpg',quality=92)
(options.output/'primary-front-control.json').write_text(json.dumps(dict(source='Antigng, 2018-02-07; 延庆路121号住宅.jpg',pixel_scale='1300 px wide rendition of 5312x2988',anchors=anchors,horizontal_segments=levels,vertical_segments=verticals,photo_to_local_metres=H.tolist(),residuals_m=losses(v.x)),indent=2)+'\n');
for p in [(80,340),(121,340),(314,331),(464,318),(615,308),(826,295),(940,295),(29,252),(33,567),(944,161),(945,615)]:print(p,position(v.x,p).round(2))
