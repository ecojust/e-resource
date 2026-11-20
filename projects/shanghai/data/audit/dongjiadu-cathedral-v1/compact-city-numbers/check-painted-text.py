"""Measure digit ink separately from the gold border and teal sprite, in a real map frame."""
import json,sys,hashlib,math
from pathlib import Path
from PIL import Image,ImageDraw
p=Path(sys.argv[1]);report=json.loads((p/'capacity-browser.json').read_bytes());pic=p/report['frame']['file'];im=Image.open(pic).convert('RGB')
sx=im.width/320;sy=im.height/568;records=[]
for row in report['layout']['positions']:
 n=row['number'];x,y,w,h=[row[k]for k in ('x','y','width','height')]
 # Ignore the two edge pixels of the warm gold frame. Bright digit pixels
 # are close to neutral (small red-to-green distance) and brighter than the teal background.
 ink=[]
 for py in range(math.ceil((y-h/2+1.3)*sy),math.floor((y+h/2-1.3)*sy)):
  for px in range(math.ceil((x-w/2+1.3)*sx),math.floor((x+w/2-1.3)*sx)):
   r,g,b=im.getpixel((px,py))
   if r>=142 and g>=146 and b>=121 and abs(r-g)<=21 and 7<=g-b<=36:
    ink.append((px,py))
 assert ink,n
 bb=[min(t[k]for t in ink)for k in (0,1)]+[max(t[k]for t in ink)for k in (0,1)]
 records.append({'number':n,'digit_count':len(str(n)),'size':[w,h],'bright_ink_pixel_count':len(ink),'ink_bbox_xyxy':bb,'ink_width_css':(bb[2]-bb[0]+1)/sx,'ink_height_css':(bb[3]-bb[1]+1)/sy})
 if len(str(n))>=3:assert (bb[2]-bb[0]+1)/sx>=12 and (bb[3]-bb[1]+1)/sy>=5,(n,bb)
positions=report['layout']['positions'];x0=int(min((r['x']-r['width']/2)*sx for r in positions));y0=int(min((r['y']-r['height']/2)*sy for r in positions));x1=math.ceil(max((r['x']+r['width']/2)*sx for r in positions));y1=math.ceil(max((r['y']+r['height']/2)*sy for r in positions))
im.crop((x0,y0,x1,y1)).resize(((x1-x0)*3,(y1-y0)*3),resample=Image.Resampling.NEAREST).save(p/'numbers-closeup.png')
(p/'painted-text.json').write_text(json.dumps(dict(frame=pic.name,frame_sha256=hashlib.sha256(pic.read_bytes()).hexdigest(),method='RGB thresholds measured inside native sprite bounds, excluding the warm border. The crop is a 3× nearest-neighbour enlargement of the same frame.',positions=len(records),three_digit_count=len([r for r in records if r['digit_count']==3]),records=records),indent=2)+'\n')
print(len(records),min(r['bright_ink_pixel_count'] for r in records),min(r['ink_width_css']for r in records if r['digit_count']==3),min(r['ink_height_css']for r in records if r['digit_count']==3))
