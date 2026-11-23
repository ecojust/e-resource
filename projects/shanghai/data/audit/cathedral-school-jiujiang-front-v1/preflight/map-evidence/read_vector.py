"""Parse this original OSM-derived MVT, retaining the ring order of each numeric feature."""
from pathlib import Path
import ast,gzip,struct
from shapely.geometry import Polygon,MultiPolygon,mapping
# Load the repository's three isolated wire-format readers without its CLI's OpenCC dependency.
file=Path('/workspace/e-resource/projects/shanghai/tools/extract_bund_road_labels.py')
tree=ast.parse(file.read_bytes());tree.body=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in('varint','fields','tile_value')]
exec(compile(tree,str(file),'exec'),globals())
def packed(s):
 off=0
 while off<len(s):
  value,off=varint(s,off);yield value
def building(data):
 if data[:2]==bytes([31,139]):data=gzip.decompress(data)
 layer=next(raw for which,_,raw in fields(data)if which==3 and any(n==1 and v==b'building'for n,_,v in fields(raw)))
 vals=list(fields(layer));keys=[v.decode()for n,_,v in vals if n==3];values=[tile_value(v)for n,_,v in vals if n==4];extent=next(v for n,_,v in vals if n==5);features=[]
 for n,_,raw in vals:
  if n!=2:continue
  p=dict((a,c)for a,_,c in fields(raw));assert p[3]==3
  tags=list(packed(p.get(2,b'')));properties={keys[k]:values[j]for k,j in zip(tags[::2],tags[1::2])}
  coords=iter(packed(p[4]));x=y=0;polys=[];rings=[];ring=[]
  for pattern in coords:
   cmd,count=pattern&7,pattern>>3
   if cmd==7:
    assert count==1 and len(ring)>2
    area=sum(x1*y2-x2*y1 for (x1,y1),(x2,y2)in zip(ring,ring[1:]+ring[:1]))
    if area>0 and rings:polys.append(Polygon(rings[0],rings[1:]));rings=[]
    rings.append(ring);ring=[]
   else:
    assert cmd in (1,2)
    for i in range(count):
     a=next(coords);b=next(coords);x+=(a>>1)^-(a&1);y+=(b>>1)^-(b&1);ring.append((x,y))
  if rings:polys.append(Polygon(rings[0],rings[1:]))
  geom=polys[0]if len(polys)==1 else MultiPolygon(polys)
  features.append({'id':p.get(1,0),'geometry':mapping(geom),'properties':properties})
 return dict(extent=extent,features=features)
