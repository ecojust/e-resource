"""Follow visible dark overlaps from each wreath's inner lip to its outer edge."""
import json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageDraw,ImageOps
w=Path(__file__).resolve().parents[1];data=json.loads((w/'measurements/four-photographed-wreaths.json').read_bytes());out=[]
with Image.open(w/'research/tram-original.jpg')as photo:upright=ImageOps.exif_transpose(photo)
sheet=Image.new('RGB',(760,235),'#e2ded4')
for rec in data['wreaths']:
 field=np.array(rec['normalized_relief']);inner=np.array(rec['inner']);outer=np.array(rec['outer']);stations=len(inner);radial=field.shape[1]
 # Follow the local displacement of each dark crease across the band. Search
 # remains narrower than the gap to adjacent folds; squared-change regularizes
 # parts where a narrow highlight interrupts the crease.
 paths=[];tile=upright.crop(rec['source_box']);d=ImageDraw.Draw(tile);box=np.array(rec['source_box'][:2])
 for i0 in rec['groove_stations']:
  offsets=np.arange(-9,10);a=(i0+offsets)%stations
  costs=gaussian_filter(field,(1.0,.6),mode=('wrap','nearest'))[a]
  penalties=.095*(offsets[:,None]-offsets[None,:])**2
  total=costs[:,0]+.032*offsets**2;previous=np.zeros((radial,len(a)),int)
  for k in range(1,radial):
   possible=total[:,None]+penalties
   prev=np.argmin(possible,axis=0);previous[k]=prev
   total=possible[prev,np.arange(len(a))]+costs[:,k]+.026*offsets**2
  idx=int(np.argmin(total));trace=[idx]
  for j in range(radial-1,0,-1):idx=previous[j,idx];trace.append(idx)
  path=i0+gaussian_filter1d(offsets[trace[::-1]].astype(float),.8)
  centre=np.rint(path).astype(int)%stations;t=np.linspace(0.,1.,radial)
  xy=(1-t[:,None])*inner[centre]+t[:,None]*outer[centre]-box
  d.line([tuple(u)for u in xy],fill='#68eac5',width=1)
  # Orientation of the casting lip follows the brighter adjacent side of the
  # observed edge at each station, predominantly constant within a fold.
  left=field[(centre-3)%stations,np.arange(radial)];right=field[(centre+3)%stations,np.arange(radial)]
  direction=1 if np.median(right[3:-3]-left[3:-3])>0 else -1
  paths.append({'station':i0,'trough_path':np.round(path,3).tolist(),'lip_direction':direction})
 out.append({'number':rec['number'],'folds':paths})
 tile.thumbnail((176,220));sheet.paste(tile,((rec['number']-1)*190,0))
(w/'measurements/observed-leaf-overlaps.json').write_text(json.dumps({'source_sha256':data['photo_sha256'],'method':'Dark crease traces and brighter adjacent lips follow the measured pixels through 15 radial samples of each red foliage band. The relief amplitude is inferred.','wreaths':out},separators=(',',':'))+'\n')
sheet.save(w/'wreaths/observed-overlaps.jpg',quality=90)
print([len(r['folds'])for r in out])
