"""Compare fixed photographic points on the No. 3 entrance and upstairs sash with a GLB."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import runpy
import sys
import numpy as np
p=argparse.ArgumentParser()
p.add_argument('mesh',type=Path);p.add_argument('out',type=Path)
p.add_argument('--scale',type=float,nargs=3,default=(1,1,1))
opts=p.parse_args();here=Path(__file__).resolve().parent;site=here.parent
sys.path.insert(0,str(site/'source'))
from court_three import BRICK, CAST, CREAM, CAP, ENAMEL, GLASS, GREEN, CHARCOAL, LETTER
cam=runpy.run_path(str(here/'register_court.py'))['Camera']()
mesh=runpy.run_path(str(site.parents[2]/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'](opts.mesh)
# Pixel coordinates on the two independent planar resamplings of the 2016 original.
# Upper window sample sites avoid laundry, wires and the foreground terrace rail.
rectified={
 'gate':[(190,157,ENAMEL),(226,136,ENAMEL),(205,147,LETTER),(208,200,CAST),(207,314,CAST),
 (209,440,CAST),(264,225,CAST),(150,306,CAST),(378,263,CHARCOAL),(420,365,CHARCOAL),
 (466,386,CHARCOAL),(338,306,CHARCOAL),(177,93,CAP)],
 'window':[(392,518,CREAM),(583,497,CREAM),(549,376,CREAM),(555,350,CREAM),
 (443,517,GLASS),(459,540,GLASS),(520,533,GLASS),(556,508,GLASS),
 (572,523,GREEN),(567,480,GREEN),(330,405,BRICK),(627,444,BRICK),(607,494,BRICK)]
}
report=[]
for wall,samples in rectified.items():
 for u,v,material in samples:
  if wall=='gate':xyz=[-.8+.004*u,0,2.94-.004*v]
  else:xyz=[-2.4+.005*u,.70,7.15-.005*v]
  pixel=cam.pixel(xyz)
  original=cam.ray(pixel);scale=np.array(opts.scale)
  hit=mesh.ray(cam.c*scale,original*scale,100)
  expected=material
  report.append({'region':wall,'rectified_pixel':[u,v],'native_photo_pixel':pixel.tolist(),'expected_material':expected,
     'first_hit':hit,'passed':bool(hit and hit['material']==expected)})
out={'reference':'Livelikerw. 上海第五批优秀历史建筑-大福里，2016-02-06. CC BY-SA 4.0. https://commons.wikimedia.org/wiki/File:Dafu_Li_Shanghai.JPG',
     'source_pixel_extent':[4912,3264],'mesh_sha256':sha256(opts.mesh.read_bytes()).hexdigest(),'model_scale_xyz':opts.scale,
     'scope':'Post, pink castwork, dark gate, green enamel, red wall, cast surround and the visible portion of the green upper window; narrow cast boundaries sensitive to oblique viewing and figure recognition.','samples':report,
     'passed':sum(a['passed']for a in report),'total':len(report)}
opts.out.parent.mkdir(parents=True,exist_ok=True);opts.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(out['passed'],len(report),[(r['rectified_pixel'],r['expected_material'],(r['first_hit'] or {}).get('material'))for r in report if not r['passed']])
