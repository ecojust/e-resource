"""Check each X11 viewport and its independent WebGL raster against the real closed phase."""
import argparse,hashlib,json
from pathlib import Path
from PIL import Image
def sha(path):
 with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def rgb(path):
 with Image.open(path)as image:return image.convert('RGB')
def verify(root,report):
 d=json.loads(report.read_bytes());cal=d['viewportCalibration'];p=root/cal['image'];assert sha(p)==cal['sha256']
 x,y,w,h=(cal[k]for k in ('x','y','width','height'));a=rgb(p)
 assert a.getpixel((x,y))==(207,43,171) and a.getpixel((x+w-1,y+h-1))==(31,211,93)
 rows=[]
 for view,screen,display,canvas in zip(d['views'],d['screenshots'],d['displayCaptures'],d['webglCaptures'],strict=True):
  sp,dp,cp=root/screen['file'],root/display['displayImage'],root/canvas['file']
  assert sha(sp)==screen['sha256'] and sha(dp)==display['displayImageSha256'] and sha(cp)==canvas['sha256']
  outer,cut,pixels=rgb(dp),rgb(sp),rgb(cp)
  assert cut.size==(w,h) and outer.crop((x,y,x+w,y+h)).tobytes()==cut.tobytes() and display['rectangle']==f'{w}x{h}+{x}+{y}'
  assert pixels.size==(canvas['width'],canvas['height']) and cp.stat().st_size==canvas['bytes'] and sp.stat().st_size==screen['bytes']
  assert all(high>low for low,high in pixels.getextrema()) and not view['contextLost'] and view['glError']==0
  rows.append(dict(view=view['view'],sha256=sha(sp),webgl_sha256=sha(cp),x11_sha256=sha(dp),raster=list(pixels.size),calibrated_crop=[x,y,w,h]))
 assert len(set(z['webgl_sha256']for z in rows))==len(rows)
 return dict(report_sha256=sha(report),calibration_sha256=sha(p),frames=rows)
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('report',type=Path);ap.add_argument('output',type=Path);a=ap.parse_args()
 a.output.write_text(json.dumps(verify(a.report.parent,a.report),ensure_ascii=False,indent=2)+'\n')
