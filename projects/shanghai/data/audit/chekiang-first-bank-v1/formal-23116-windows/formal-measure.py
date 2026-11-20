from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
import json,hashlib,sys
p=Path(sys.argv[1]);r=json.loads((p/'browser.json').read_bytes());assert r['completed'] and r['closed']and not r['pageErrors']
views={}
for name,v in r['views'].items():
 polygons=json.loads((p/(name+'-projection.json')).read_bytes())
 assert len(polygons)==12
 shapes={k:Polygon(x)for k,x in polygons.items()};total=unary_union(list(shapes.values()));bloc=[]
 for s in v['labels']:
  x,y,w,h=[s[k]for k in ('x','y','width','height')];bloc.append(box(x-w/2,y-h/2,x+w/2,y+h/2))
 mask=unary_union(bloc);occlusion=total.intersection(mask).area
 views[name]=dict(windows=12,area_px2=total.area,occluded_px2=occlusion,per_window_px2={k:shape.intersection(mask).area for k,shape in shapes.items()},labels=len(v['labels']),rendered_label_picks=sum(sum(h['picked']==l['id']for h in l['hits'])for l in v['labels']),screenshot_sha256=v['sha256'])
 assert total.area>200
(p/'window-coverage.json').write_text(json.dumps({'site':r['base'],'actual':True,'views':views},indent=2)+'\n')
print([(k,v['area_px2'],v['occluded_px2']) for k,v in views.items()])
