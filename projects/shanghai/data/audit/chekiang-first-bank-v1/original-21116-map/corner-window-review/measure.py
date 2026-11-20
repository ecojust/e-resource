from pathlib import Path
from shapely.geometry import Polygon,box
from shapely.ops import unary_union
import json
p=Path(__file__).resolve().parent
layouts=json.loads((p/'label-positions.json').read_bytes())
shapes=json.loads((p/'screen-windows.json').read_bytes())
out={}
for version in ('old','new'):
 s=layouts[version]['views'];sc={}
 for name,polys in shapes.items():
  labels=s[name]['labels'];rects=[]
  for l in labels:
   xx,yy,w,h=[l[k] for k in ('x','y','width','height')];rects.append((l['id'],box(xx-w/2,yy-h/2,xx+w/2,yy+h/2)))
  polys1={k:Polygon(v)for k,v in polys.items()};surface=unary_union(list(polys1.values()));t=surface.intersection(unary_union([rr for _,rr in rects]));sc[name]={'windows':len(polys),'actual_projected_window_area_px2':surface.area,'covered_area_px2':t.area,'ratio':t.area/surface.area,'labels':[{'id':i,'covered_px2':g.intersection(surface).area}for i,g in rects if g.intersects(surface)],'per_window':{k:round(poly.intersection(t).area/poly.area,3)for k,poly in polys1.items()}}
 out[version]=sc
(p/'overlap.json').write_text(json.dumps(out,indent=2));print([(k,n,round(v['ratio'],3),v['labels'])for k,sc in out.items()for n,v in sc.items()])
