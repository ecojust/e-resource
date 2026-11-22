"""Inspect the decoded pixels of ten real screenshots and their same-camera baseline registration."""
import json,hashlib,sys
from pathlib import Path
from PIL import Image
import numpy as np
w=Path(__file__).parent;e=w/'isolated-evidence';stages=json.loads((w/'isolated-inputs.json').read_bytes())['stage_order']
from importlib.machinery import SourceFileLoader
read_supplement=SourceFileLoader('desktop_photo',str(w/'confirm-destination-picture.py')).load_module().read
results={};matches={}
for name in stages:
 d=e/name;rc=json.loads((d/'closed.json').read_bytes());r=json.loads(Path(rc['report']).read_bytes());sc,=r['screenshots']
 if name=='desktop-pin':d,rc,r,sc=read_supplement(w)
 p=d/sc['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==sc['sha256'];im=Image.open(p).convert('RGB');a=np.asarray(im);h,x,a3=a.shape;css=r['inputDevice']['viewport'];native=abs(r['captureProfile']['pixelRatio']) if name=='distant' else 1
 expected=[round(value*native) for value in css] if name=='distant' else sc.get('pixelSize',css)
 assert all(abs(a0-b0)<=1 for a0,b0 in zip([x,h],expected)) or (name=='distant' and [x,h]==css),(name,[x,h],expected)
 assert not sc.get('pixelSize') or sc['cameraAtRead']['cssViewport']==r['inputDevice']['viewport'];cx=a[h//5:h*7//10,x//5:x*4//5];light=np.dot(cx[::2,::2],[.2126,.7152,.0722]);std=float(np.std(light));palette=len(np.unique((cx[::4,::4]//16).reshape(-1,3),axis=0));assert std>4 and palette>12,(name,std,palette)
 results[name]=dict(path=str(p),sha256=sc['sha256'],width=x,height=h,css_viewport=css,physical_pixel_ratio=r['captureProfile']['pixelRatio'],map_centre_luminance_sd=std,map_centre_12bit_colours=palette)
 if name in ('control','street'):matches[name]=im
first,second=matches['control'],matches['street'];assert first.size==second.size
a,b=(np.asarray(p,dtype=np.int16)for p in (first,second));h,x=a.shape[:2];d=np.max(abs(a-b),axis=2);region=d[h//5:h*7//10,x//4:x*3//4];changed=int((region>16).sum());assert changed>200
out=dict(passed=True,observed_images=results,registered_street_view=dict(region_pixels=region.size,changed_by_over_16_rgb=changed,first=results['control']['sha256'],second=results['street']['sha256']),method='Executed after all real screenshots are closed. The centre sample excludes top menu and bottom card. Visual review checks architectural details and obstructions independently.')
(w/'pixel-inspection.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
