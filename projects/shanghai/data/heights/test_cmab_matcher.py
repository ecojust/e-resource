"""Meaningful transfer guards: overlap, neighbor, split, ambiguity, and units."""
from pathlib import Path
import tempfile,json
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import Transformer
from shapely.geometry import box,mapping
from shapely.ops import transform
from building_height_sampler import CMABHeightMatcher
project=Transformer.from_crs(4326,3857,always_xy=True).transform
reverse=Transformer.from_crs(3857,4326,always_xy=True).transform
x,y=project(121.48,31.23)
target=box(x,y,x+20,y+20)
key=f'{int((x+10)//5000)}_{int((y+10)//5000)}'
def match(polygons,heights):
 with tempfile.TemporaryDirectory() as folder:
  p=Path(folder);pq.write_table(pa.table({'geometry':[g.wkb for g in polygons],'height_m':heights,'source_id':[str(i) for i in range(len(heights))]}),p/(key+'.parquet'))
  (p/'manifest.json').write_text(json.dumps({'shards':[{'file':key+'.parquet'}]}))
  return CMABHeightMatcher(p).sample_geometry(mapping(transform(reverse,target)))
r=match([target],[42.5]);assert r and r['height_m']==42.5 and r['height_match_iou']>.999
assert match([box(x+30,y,x+50,y+20)],[80]) is None
assert match([box(x,y,x+8,y+20)],[80]) is None
assert match([box(x,y,x+40,y+20)],[80]) is None
assert match([target,target],[40,70]) is None
assert match([target,target],[40,40]) is not None
print('PASS: same-building metre height, nearest-neighbor refusal, split refusal, merge refusal, conflicting ambiguity refusal, identical-duplicate acceptance')
