"""Check four X11 viewport crops, calibrated end markers, canvas raster sizes and sightline pixels."""
import argparse,hashlib,json
from pathlib import Path
import numpy as np
from PIL import Image
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('sessions',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
def rgb(p):return Image.open(p).convert('RGB')
def read(p):return json.loads(p.read_bytes())
result={}
for entry in read(a.sessions/'architecture-stage-exits.json'):
 assert entry['exit']==0 and entry['pid']>0
 d=a.sessions/entry['kind'];report=d/'main-browser.json';r=read(report);assert sha(report)==entry['reportSHA256']
 screen,=r['screenshots'];graph,=r['webglCaptures'];root,=r['displayCaptures'];cal=r['viewportCalibration']
 for f,k in [(screen['file'],screen['sha256']),(graph['file'],graph['sha256']),(root['displayImage'],root['displayImageSha256']),(cal['image'],cal['sha256'])]:
  assert sha(d/f)==k,(d,f)
 x,y,w,h=(cal[k] for k in ('x','y','width','height'));bounds=(x,y,x+w,y+h)
 markers=rgb(d/cal['image']);mouth=markers.getpixel((x+4,y+4));foot=markers.getpixel((x+w-5,y+h-5))
 assert sum(abs(i-j) for i,j in zip(mouth,(207,43,171)))<=8 and sum(abs(i-j) for i,j in zip(foot,(31,211,93)))<=8
 viewport=rgb(d/screen['file']);whole=rgb(d/root['displayImage']);assert viewport.size==(w,h) and whole.crop(bounds).tobytes()==viewport.tobytes()
 webgl=rgb(d/graph['file'])
 if 'width' in graph:assert webgl.size==(graph['width'],graph['height'])
 elif r.get('renderQuality'):assert list(webgl.size)==r['renderQuality']['after']['raster']
 gbox=(graph.get('x',0),graph.get('y',0),graph.get('w',w),graph.get('h',h))
 screenshot=np.asarray(viewport);gx,gy,gw,gh=map(round,gbox)
 assert gx>=0 and gy>=0 and gx+gw<=w+1 and gy+gh<=h+1
 matched=np.asarray(webgl.resize((gw,gh),Image.Resampling.BILINEAR));diff=np.max(np.abs(matched.astype(np.int16)-screenshot[gy:gy+gh,gx:gx+gw]),axis=2)
 observations=[]
 for stage in r.get('architecturalPixels',[]):
  for z in stage['attempts'][-1]['targets']:
   i,j=int(round(z['x'])),int(round(z['y']));assert z['clear'] and 0<=i<w and 0<=j<h
   pi,pj=(int((i-gx+.5)*webgl.width/gw),int((j-gy+.5)*webgl.height/gh))
   observations.append(dict(name=z['name'],viewport=[i,j],whole_display=[x+i,y+j],webgl=[pi,pj],screen_rgb=list(viewport.getpixel((i,j))),webgl_rgb=list(webgl.getpixel((pi,pj)))))
 result[entry['kind']]=dict(view=r['views'][0]['view'],sha256=sha(report),calibration=[x,y,w,h],calibration_centres=[mouth,foot],exact_x11_pixels=w*h,webgl_pixels=webgl.width*webgl.height,within_rgb_tolerance_8=float(np.mean(diff<=8)),chosen_detail_points=observations)
assert len(result)==4 and sum(len(v['chosen_detail_points']) for v in result.values())==8
a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
