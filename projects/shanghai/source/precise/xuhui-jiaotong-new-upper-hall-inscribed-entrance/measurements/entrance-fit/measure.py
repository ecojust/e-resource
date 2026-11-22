"""Project the south entrance's mesh onto the measured south wall and sample its centre doorway."""
from argparse import ArgumentParser
from pathlib import Path
from hashlib import sha256
import gzip,json,math,struct
parser=ArgumentParser(description=__doc__)
parser.add_argument('--city-table',type=Path,required=True)
parser.add_argument('--raw',type=Path,required=True)
parser.add_argument('--decoded-full',type=Path,required=True)
parser.add_argument('--decoded-lod',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
def checksum(data):return sha256(data).hexdigest()
city=args.city_table.read_bytes()
assert checksum(city)=='569470522f9d8f33822db9c3232a9ac523e1cc709f63cdceb8abd900bf350736'
features=json.loads(gzip.decompress(city))['features']
owner=next(row for row in features if row['localId']==2187);ring=owner['geometry']['coordinates'][0]
south=min((p for p in zip(ring,ring[1:])if abs(p[0][0]-p[1][0])>.00065),key=lambda ends:sum(p[1]for p in ends))
long,lat=(sum(p[i] for p in south)/2 for i in range(2));dx=(south[0][0]-south[1][0])*111195.08*math.cos(math.radians(lat));dy=(south[0][1]-south[1][1])*111195.08
def measure(path):
 data=path.read_bytes();size=struct.unpack_from('<I',data,12)[0];g=json.loads(data[20:20+size]);blob=memoryview(data)[28+size:]
 def unpack(index):
  acc=g['accessors'][index];view=g['bufferViews'][acc['bufferView']];code={5121:'B',5123:'H',5125:'I',5126:'f'}[acc['componentType']];n={'SCALAR':1,'VEC3':3}[acc['type']];shape=struct.Struct('<'+str(n)+code);start=acc.get('byteOffset',0)+view.get('byteOffset',0);stride=view.get('byteStride',shape.size)
  return [shape.unpack_from(blob,start+i*stride) for i in range(acc['count'])]
 triangles=[];points=[]
 assert all(not any(key in node for key in ('translation','rotation','scale','matrix'))for node in g['nodes'])
 for mesh in g['meshes']:
  for prim in mesh['primitives']:
   pp=unpack(prim['attributes']['POSITION']);indices=[i for i, in unpack(prim['indices'])];points.extend(pp);triangles.extend(tuple(pp[i]for i in indices[k:k+3])for k in range(0,len(indices),3))
 def crossings(x,z):
  found=[]
  for a,b,c in triangles:
   u1=b[0]-a[0];v1=b[1]-a[1];u2=c[0]-a[0];v2=c[1]-a[1];det=u1*v2-u2*v1
   if abs(det)<1e-8:continue
   u=((x-a[0])*v2-(z-a[1])*u2)/det;v=((z-a[1])*u1-(x-a[0])*v1)/det
   if min(u,v)>=-1e-7 and u+v<=1.0000001:found.append(round(-(a[2]+u*(b[2]-a[2])+v*(c[2]-a[2])),5))
  return sorted(set(found))
 central=[{'x_m':x,'z_m':z,'portal_north_depth_hits_m':crossings(x,z),'original_wall_depth_m':0}for x in (-.38,0,.38) for z in (1.16,1.43,1.84,2.21,2.66,3.00)]
 controls=[{'x_m':x,'z_m':z,'portal_north_depth_hits_m':crossings(x,z)}for x in (-4.2,4.2,-2.3,2.3)for z in (1.24,2.15,2.94)]
 return dict(decoded_sha256=checksum(data),triangles=len(triangles),x_bounds=[round(min(p[0]for p in points),5),round(max(p[0]for p in points),5)],height_bounds=[round(min(p[1]for p in points),5),round(max(p[1]for p in points),5)],north_depth_bounds=[round(-max(p[2]for p in points),5),round(-min(p[2]for p in points),5)],central_open_samples=sum(not r['portal_north_depth_hits_m']for r in central),central_rays=central,flanking_door_and_pier_controls=controls)
levels={k:measure(f) for k,f in [('raw',args.raw),('full',args.decoded_full),('lod',args.decoded_lod)]}
result=dict(order=373,model_id='xuhui-jiaotong-new-upper-hall-inscribed-entrance',source_table_sha256=checksum(city),retained_feature=2187,source_height_m=owner['height'],south_wall_endpoints=south,south_wall_length_m=round(math.hypot(dx,dy),5),hypothetical_portal_alignment='Midpoint of the long southern edge. X east, masonry pier face at the existing footprint boundary. The centreline is an alignment hypothesis, not a measured anchor.',levels=levels)
args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
