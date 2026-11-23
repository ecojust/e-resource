"""Measure the round roof in the two unrotated, georeferenced source crops."""
import hashlib,json,math
from pathlib import Path
from shapely.geometry import Polygon,shape,Point
from shapely.ops import transform
p=Path(__file__).parent
# Digests identify the two privately inspected source crops. Their sampled coordinates are public.
SOURCE_IMAGE_SHA256={'8432': '84b4c0ab66bcb33a2adb38617e7b32be312af0f4400e211145ae0c68c172508a', '3692': 'e3fa369db34a74a494b326fee3208af4d4cadd5467ed220fb841ce59d03a1211'}
def read(q):return json.loads(q.read_bytes())
def wgs(x,y,meta):
 n=256*2**meta['zoom'];u,v=meta['crop_global_pixel_origin']
 return [(u+x)*360/n-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*(v+y)/n))))]
marks={'8432':[(103,222),(109,176),(142,139),(190,130),(234,140),(274,165),(293,203),(300,247),(283,293),(252,327),(204,344),(161,337),(124,303),(108,262)],
       '3692':[(70,183),(86,141),(121,104),(165,84),(205,85),(247,111),(277,150),(294,192),(281,239),(241,267),(205,291),(160,289),(117,267),(90,230)]}
doc=read(p/'original-owner-comparison.json');rows=doc['fixed_owners'];records={}
for k,clicks in marks.items():
 meta=read(p/('release-'+k+'.json'));pts=[(250+x/3,285+y/3)for x,y in clicks];world=[wgs(x,y,meta)for x,y in pts];cen=Polygon(pts).centroid;lon,lat=wgs(cen.x,cen.y,meta);m=meta['meters_per_pixel'];lonm=111319.49079*math.cos(math.radians(lat));latm=111319.49079
 def local(x,y,z=None):return ((x-lon)*lonm,(y-lat)*latm)
 roof=transform(local,Polygon(world));dists=[]
 for r in rows:
  poly=transform(local,shape(r['source_ring']))
  if roof.distance(poly)<17:
   inter=roof.intersection(poly).area
   dists.append({'id':r['id'],'source_key':r['key'],'source_height_m':r['height'],'area_m2':poly.area,'overlap_m2':inter,'roof_share':inter/roof.area,'roof_distance_m':poly.distance(roof),'centroid_spacing_m':roof.centroid.distance(poly.centroid)})
 dists.sort(key=lambda x:-x['overlap_m2'])
 xs,ys=zip(*pts);records[k]={'metadata':meta['metadata'][0]['records'][0],'imagery_sha256':SOURCE_IMAGE_SHA256[k],'pixel_points':pts,'polygon_center_wgs84':(lon,lat),'polygon_center_pixel':[cen.x,cen.y],'width_ew_m':(max(xs)-min(xs))*m,'length_ns_m':(max(ys)-min(ys))*m,'area_m2':roof.area,'equivalent_diameter_m':2*math.sqrt(roof.area/math.pi),'owners':dists,'roof_rim_wgs84':world}
print([(k,d['width_ew_m'],d['length_ns_m'],d['polygon_center_wgs84'],d['owners'][0]) for k,d in records.items()])
report={'identity':'新华路329弄36号双层圆形住宅（长宁3M014）','macro':doc['macro'],'fixed_source':doc['source'],'feature_table_sha256':doc['sha256'],'origin_note':'All pixels use the original 640×640 crop, origin top left. The auxiliary crop is [250,285,390,425] enlarged threefold. The visible roof perimeter is manually digitized, with particular uncertainty at shaded, planted and foreshortened edges. Two georeferenced releases show different roof covering colours.','pixel_pick_tolerance_px':3,'apparently_truncated_rim':'The SE edge is approximately straight in the red-roof image. Neither image alone locates an entrance or identifies the photographed garden elevation.','practical_diameter_m':[17,20.5],'address_context':'两个独立36号地名点落在圆屋北缘一带，原户411的C形轮廓与实际圆顶仅部分重合。周边红瓦矩形屋应各保其原户。','records':records}
(p/'round-roof-and-source-411.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
