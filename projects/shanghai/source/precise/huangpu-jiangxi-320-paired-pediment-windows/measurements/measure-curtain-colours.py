"""Sample each photographed awning at equal intervals along its hanging fabric."""
import sys,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageOps
from scipy.signal import find_peaks
from scipy.ndimage import map_coordinates,gaussian_filter1d
s=Path(__file__).absolute().parents[1]/'source'
sys.path.insert(0,str(s))
from window_details import BAYS,bilinear
w=Path(__file__).parent
import argparse
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument('source_photo',type=Path,help='Original Antigng photograph as downloaded')
ap.add_argument('output',type=Path,help='Fitted band boundary JSON')
ap.add_argument('--holdout',type=Path,help='Write held-out blue and ochre sample locations')
args=ap.parse_args()
with Image.open(args.source_photo) as photograph:
    assert photograph.size==(5312,2988) and photograph.getexif().get(274)==6
    source=photograph.crop((1430,788,3040,1738)).transpose(Image.Transpose.ROTATE_270)
region=source.resize((610,1033),Image.Resampling.LANCZOS)
rgb=np.array(region,dtype=float)
del source,region
def sample(quad,ts):
 v=np.linspace(0,1,241);ch=[]
 for t in ts:
  line=np.asarray([bilinear(quad,t,z)for z in v]);u,y=line.T
  color=np.array([map_coordinates(rgb[:,:,j],[y,u],order=1)for j in range(3)]).T
  ch.append((color[:,2]-color[:,0])/(color.sum(axis=1)+2))
 return v,gaussian_filter1d(np.median(ch,axis=0),2)
def extrema(v,sig):
 ints=[]
 for sign,colors in [(1,'blue'),(-1,'ochre')]:
  ix,meta=find_peaks(sig*sign,prominence=.019,distance=8)
  ints.extend((v[i],colors,sig[i])for i in ix)
 return sorted(ints)

width_fractions=[.18,.38,.62,.82];produced={}
for bay in BAYS:
 for j,quad in enumerate(bay['drops']):
  v,sig=sample(quad,np.linspace(.32,.67,9));knots=[]
  for sign in [1,-1]:
   ids,_=find_peaks(sign*sig,prominence=.041,distance=10)
   knots.extend((int(i),sign)for i in ids)
  knots.sort();assert all(a[1]!=b[1]for a,b in zip(knots,knots[1:])),knots
  # End fragments are distinguished where the opposite colour reappears across the cropped hem.
  for edge in [0,len(v)-1]:
   anchor,sign=(knots[0] if edge==0 else knots[-1])
   if sign*(sig[anchor]-sig[edge])>.065:
    knots.append((edge,-sign))
  knots.sort()
  guides=[];polarity=[]
  for (a,sa),(b,sb) in zip(knots,knots[1:]):
   target=(sig[a]+sig[b])/2
   k=a+int(np.argmin(np.abs(sig[a:b+1]-target)))
   guides.append(float(v[k]));polarity.append(sb)
  profiles=[]
  for u in width_fractions:
   vv,s=sample(quad,[u-.025,u,u+.025]);grad=np.gradient(s);spots=[]
   for k,(t,sign) in enumerate(zip(guides,polarity)):
    # Permit skew across the cloth, with no possibility of reordering adjacent edges.
    lo=max(0.,t-.084,.5*(guides[k-1]+t)if k else .006)
    hi=min(1.,t+.084,.5*(guides[k+1]+t)if k+1<len(guides)else .994)
    ix=np.flatnonzero((vv>lo)&(vv<hi));score=sign*grad[ix]
    spot=float(vv[ix[np.argmax(score)]]) if len(ix) and np.max(score)>.0018 else t
    spots.append(round(spot,6))
   assert np.all(np.diff(spots)>0)
   profiles.append(spots)
  key=bay['name']+'/'+str(j)
  produced[key]=dict(first_blue=knots[0][1]==1,across=width_fractions,edge_v=np.transpose(profiles).tolist())
  print(key,produced[key]['first_blue'],len(produced[key]['edge_v'])+1)
args.output.write_text(json.dumps(produced,indent=2)+'\n')

if args.holdout:
    import hashlib
    res=[]
    for bay in BAYS:
     for index,quad in enumerate(bay['drops']):
      for t in [.27,.73]:
       v,sig=sample(quad,[t-.007,t,t+.007]);det=[]
       for sign,name in [(1,'blue'),(-1,'ochre')]:
        ii,prop=find_peaks(sign*sig,prominence=.078,distance=11)
        for k,pr in zip(ii,prop['prominences']):
         if not .06<v[k]<.94 or sign*sig[k]<.03:continue
         pt=bilinear(quad,t,v[k])
         det.append(dict(kind=name,position_t=round(float(v[k]),5),xy=np.asarray(pt).round(4).tolist(),prominence=round(float(pr),6)))
       det.sort(key=lambda q:q['position_t'])
       res.append(dict(curtain=bay['name']+' '+str(index)+' at '+str(t),across=t,extrema=det))
    args.holdout.write_text(json.dumps(dict(source_sha256=hashlib.sha256(args.source_photo.read_bytes()).hexdigest(),pixel_frame=[610,1033],full_upright_crop=[1250,1430,2200,3040],holdout_width_fractions=[.27,.73],boundary_training_widths=[.18,.38,.62,.82],minimum_prominence=.078,minimum_absolute_chroma=.03,v_interval=[.06,.94],track_method='Median of three subpixel colour traces (u +/- 0.007), 241 equally spaced samples, Gaussian sigma 2 longitudinal samples.',profiles=res),indent=2)+'\n')
