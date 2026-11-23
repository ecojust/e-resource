from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urlencode
from math import *
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from PIL import Image,ImageDraw
import json,hashlib,sys
w=Path(__file__).parent
from projection import wgs
def fetch(u):
 b=urlopen(Request(u,headers={'User-Agent':'Mozilla/5.0','Referer':'https://map.baidu.com/'}),timeout=15).read();return b,dict(url=u,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def call(qt,**kw):return fetch('https://mapsv0.bdimg.com/?'+urlencode(dict(qt=qt,**kw)))
def write(f,d):f.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n')
def nearest(xy):
 b,r=call('qsdata',x=xy[0],y=xy[1],l=19,action=0,radius=35);sid=json.loads(b).get('content',{}).get('id');return {**r,'xy':xy,'sid':sid}
def station(pid):
 f=w/('station-'+pid+'.json')
 if f.is_file():return json.loads(f.read_bytes())
 b,r=call('sdata',sid=pid);j=json.loads(b)['content'][0]
 keep={k:j.get(k)for k in ['ID','Date','NorthDir','Heading','DeviceHeight','X','Y','TimeLine','RoadName']}
 d={**keep,'url':r,'wgs':wgs(j['X']/100,j['Y']/100)};write(f,d);return d
def crop(a,az,el,hf,vf,tag,ww=810,hh=435,z=4):
 import numpy as np
 U=np.rint(((az+np.linspace(-hf/2,hf/2,ww)+a['NorthDir'])%360)*(2**(z-1)*512)/360).astype(int)%(2**(z-1)*512)
 V=np.rint((.5-(el+np.linspace(vf/2,-vf/2,hh))/180)*(2**(z-2)*512)).astype(int);V=V.clip(0,(2**(z-2)*512)-1)
 out=np.zeros((hh,ww,3),dtype=np.uint8);sources=[]
 for y in np.unique(V//512):
  for x in np.unique(U//512):
   b,r=call('pdata',sid=a['ID'],pos=f'{y}_{x}',z=z,**{'from':'PC'});im=np.array(Image.open(BytesIO(b)).convert('RGB'))
   uy=V//512==y;ux=U//512==x;out[np.ix_(uy,ux)]=im[np.ix_(V[uy]%512,U[ux]%512)];sources.append(r)
 f=w/(tag+'.jpg');Image.fromarray(out).save(f,quality=92);write(w/(tag+'-source.json'),dict(station=a['ID'],wgs=a['wgs'],north=a['NorthDir'],az=az,el=el,hf=hf,vf=vf,frame=[ww,hh],sources=sources,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
def main():
 # Huaihai Middle Road runs ENE, along the southern side of the two registered blocks.
 coords=[(13521888+14*i,3639517+7.2*i)for i in range(11)]+[(13521902,3639546),(13521994,3639575),(13522013,3639580)]
 with ThreadPoolExecutor(5)as ex:rows=list(ex.map(nearest,coords))
 write(w/'station-queries.json',rows)
 ids=list(dict.fromkeys(r['sid']for r in rows if r['sid']))
 with ThreadPoolExecutor(4)as ex:ss=list(ex.map(station,ids))
 print([(s['ID'],s['wgs'],s['RoadName'])for s in ss],flush=True)
 with ThreadPoolExecutor(3)as ex:
  def frame(t):
   i,s=t;crop(s,338,15,112,65,'road'+str(i),770,385,z=3)
  list(ex.map(frame,enumerate(ss)))
 out=Image.new('RGB',(980,((len(ss)+1)//2)*270),'white');dr=ImageDraw.Draw(out)
 for i,s in enumerate(ss):
  f=w/('road'+str(i)+'.jpg');img=Image.open(f);img.thumbnail((480,230));x=i%2*490;y=i//2*270;out.paste(img,(x,y));dr.text((x+1,y+234),str(i)+' '+s['ID']+' '+str(s['wgs'])[:32],fill='black')
 out.save(w/'road-sheet.jpg',quality=87)
if __name__=='__main__':main()
