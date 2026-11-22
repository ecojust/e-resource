"""Discard views in which a foreground roof covers a survey point with a flat colour."""
from PIL import Image,ImageStat
import sys,json
im=Image.open(sys.argv[1]).convert('L')
out=[]
for point in json.loads(sys.argv[2]):
    x,y=round(point['x']),round(point['y'])
    w=30
    rect=(x-w,y-w,x+w,y+w)
    crop=im.crop(rect)
    hist=crop.histogram()
    st=ImageStat.Stat(crop).stddev[0]
    out.append(dict(point=point['name'],rect=rect,standard_deviation=st,
                    shades=sum(1 for i in hist if i>2),passed=st>11 and max(hist)<.83*(2*w)**2))
print(json.dumps(out))
