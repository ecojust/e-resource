from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import json,hashlib
from scipy.ndimage import map_coordinates
import argparse
parser=argparse.ArgumentParser(description='Read four historic window fields from the original 323×450 scan')
parser.add_argument('scan',type=Path);parser.add_argument('output_json',type=Path);parser.add_argument('--comparison',type=Path)
args=parser.parse_args();source=args.scan
im=np.asarray(Image.open(source).convert('L'),float)
outline={
 'balcony_left':[[49.6,51.7],[82.8,55.0],[82.0,92.5],[49.3,90.4]],
 'balcony_right':[[106.6,59.9],[138.0,63.0],[136.4,97.8],[105.9,95.4]],
 'right_splay':[[159.0,63.6],[185.8,62.5],[185.9,108.2],[158.4,108.9]],
 'right_front':[[220.3,65.8],[239.4,69.4],[241.4,109.0],[220.0,107.0]]}
# Clear opening and exposed edge of sill in the historic source. The balcony obscures both lower casements.
cavities={
 'balcony_left':[[53.5,55.8],[77.8,58.3],[77.6,91.9],[52.0,90.8]],
 'balcony_right':[[110.1,63.3],[132.0,65.6],[131.1,96.7],[109.0,95.4]],
 'right_splay':[[163.3,66.8],[182.4,66.3],[182.0,99.45],[162.9,100.7]],
 'right_front':[[223.0,69.8],[237.0,72.2],[238.1,103.0],[222.8,101.9]]}
# Bright faces and open portions recorded independently of any 3D construction.
spec={
'balcony_left':dict(body='light on both leaves',split=.48,outer_lower='covered',rows='bright meeting stile, two shadowed upper lights, horizontal divisions faint'),
'balcony_right':dict(body='dark west half, light east leaf',split=.49,outer_lower='covered',rows='right-hand leaf retains visible small panes, opposite half falls into shade'),
'right_splay':dict(body='dark left half, bright right leaf',split=.54,outer_lower='visible',rows='upper right light has a horizontal rail, window projects above a separate dark-edged stone sill'),
'right_front':dict(body='small lights over bright solid lower face',split=.51,outer_lower='visible',rows='vertical bars visible in upper portion; far right jamb approaches tree occlusion')}
def remap(q):
 u=np.array([[0,0],[1,0],[1,1],[0,1]])
 A=[];b=[]
 for (a,c),(x,y) in zip(u,q):
  A.extend(([a,c,1,0,0,0,-x*a,-x*c],[0,0,0,a,c,1,-y*a,-y*c]));b.extend([x,y])
 H=np.r_[np.linalg.solve(A,b),1.].reshape(3,3);v,u=np.mgrid[0:1:97j,0:1:81j]
 t=H@np.vstack((u.ravel(),v.ravel(),np.ones(u.size)));t=t[:2]/t[2]
 return map_coordinates(im,t[::-1],order=1).reshape(u.shape)
rows=[];canvas=Image.new('RGB',(800,360),'white')
for j,(key,q) in enumerate(cavities.items()):
 tile=remap(q);v=tile[16:82];cols=np.round(np.median(v,axis=0)).astype(int)
 # Medians of the broad window fields tolerate the two dark overhead wires and uneven print grain.
 bands=[]
 for left,right in ((.10,.38),(.62,.90)):
  band=tile[17:83,round(left*80):round(right*80)];bands.append(round(float(np.median(band)),1))
 rows.append(dict(key=key,outer_surround_tl_tr_br_bl=outline[key],exposed_opening_tl_tr_br_bl=q,relative_light_fields_left_right=bands,**spec[key]))
 out=Image.fromarray(tile.astype('uint8')).resize((196,320));canvas.paste(out,(j*200,0));ImageDraw.Draw(canvas).text((j*200+4,328),key,fill='black')
if args.comparison:canvas.save(args.comparison)
data=dict(source_url='https://kknews.cc/zh-sg/history/yae3gmg.html',scan_url='https://i1.kknews.cc/zeyrBDYW5KvRi6QuEqQgj5EYp8MAU7KqblGbY8U/0.jpg',article='档案春秋｜地产大亨程氏家族的沪上浮沉记',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),whole_scan_native_px=[323,450],coordinates='Pixels from the top left of the whole plate; only the upper historical photograph enters this set.',reconstruction_scope='Historic second-floor windows and visible wall returns. Lower leaves of the two middle French windows are obscured by the balcony. Stile and rail thicknesses and material color are estimates; grayscale field levels reproduce relative contrast.',windows=rows)
args.output_json.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
for r in rows:print(r['key'],r['relative_light_fields_left_right'])
