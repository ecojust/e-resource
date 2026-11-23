from pathlib import Path
from hashlib import sha256
from PIL import Image
from io import BytesIO
import json,requests,numpy as np,math,sys
w=Path(__file__).parent
from urllib.parse import urlencode
sys.path.insert(0,str(w));from projection import wgs
def get(par):
 r=requests.get('https://mapsv0.bdimg.com/',params=dict(**par),timeout=15);r.raise_for_status();return r.content,dict(url=r.url,sha256=sha256(r.content).hexdigest(),bytes=len(r.content))
def meta(sid):
 f=w/('view-meta-'+sid+'.json')
 if f.is_file() and 'bearing' in json.loads(f.read_bytes()):return json.loads(f.read_bytes())
 b,r=get(dict(qt='sdata',sid=sid));d=json.loads(b)['content'][0];x,y=d['X']/100,d['Y']/100
 data=dict(id=sid,position=wgs(x,y),mc=[x,y],bearing=d['Heading'],height=d.get('DeviceHeight'),date=d.get('Date'),history=d.get('TimeLine'),ref=r)
 f.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');return data
def photo(station_id,bearing,pitch,hfov,tag,width=775,height=610,z=5):
 s=meta(station_id);wh=512*2**(z-1);f=width/(2*math.tan(math.radians(hfov)/2));ux=(np.arange(width,dtype='float32')-width/2)/f
 frame=Image.new('RGB',(width,height));tile={};refs=[]
 sp,cp=math.sin(math.radians(pitch)),math.cos(math.radians(pitch))
 for y in range(0,height,35):
  v=((height/2-np.arange(y,min(height,y+35),dtype='float32'))/f)[:,None];slope=cp-v*sp;az=bearing+np.degrees(np.arctan2(ux[None,:],slope));alt=np.degrees(np.arctan2(sp+v*cp,np.sqrt(ux[None,:]**2+slope**2)));xx=np.rint((.75+(az-s['bearing'])/360)*wh).astype(int)%wh;yy=np.rint((.25-alt/360)*wh).astype(int);buf=np.zeros((len(v),width,3),dtype='uint8');cc=yy//512*(wh//512)+xx//512
  for k in np.unique(cc):
   row,col=divmod(int(k),wh//512)
   if k not in tile:
    b,r=get(dict(qt='pdata',sid=s['id'],pos=f'{row}_{col}',z=z,**{'from':'PC'}));tile[k]=np.array(Image.open(BytesIO(b)).convert('RGB'));refs.append(r)
   mask=cc==k;buf[mask]=tile[k][yy[mask]%512,xx[mask]%512]
  frame.paste(Image.fromarray(buf),(0,y))
 outfile=w/(tag+'.jpg');frame.save(outfile,quality=87)
 (w/(tag+'.json')).write_text(json.dumps(dict(station=s,az=bearing,pitch=pitch,hfov=hfov,width=width,height=height,tiles=refs,photo_sha256=sha256(outfile.read_bytes()).hexdigest()),indent=1)+'\n')
if __name__=='__main__':
 photo(sys.argv[1],float(sys.argv[2]),float(sys.argv[3]),float(sys.argv[4]),sys.argv[5])
