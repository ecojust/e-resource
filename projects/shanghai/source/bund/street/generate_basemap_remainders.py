"""Remove only the locally modeled portions of two verified MVT road features.

Tile buffers are discarded at nominal tile cores before union, preventing
near-coincident buffered duplicates from being counted or rendered twice.
No road geometry is widened or shifted. No network request is made.
"""
from pathlib import Path
import sys,json,math,hashlib
import mapbox_vector_tile
from shapely.geometry import shape,mapping,box,GeometryCollection
from shapely.ops import unary_union,linemerge,transform
ROOT=Path(__file__).resolve().parent
PROJECT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT.parents[2]
IDS=[403013682,4489314812]
LAYERS=['road_secondary_tertiary_casing','road_secondary_tertiary']
CROP=[121.4842,31.23545,121.4892,31.2419]
Z=14;EXTENT=4096;WORLD=2**Z*EXTENT;R=6378137.;SCALE=math.cos(math.radians(31.2385));METRES_PER_UNIT=2*math.pi*R*SCALE/WORLD

def geographic(x,y,z=None):return x/WORLD*360-180,math.degrees(math.atan(math.sinh(math.pi*(1-2*y/WORLD))))
def world(lng,lat):return (lng+180)/360*WORLD,(1-math.asinh(math.tan(math.radians(lat)))/math.pi)/2*WORLD

def lines(g):
 if g.is_empty:return []
 if g.geom_type=='LineString':return [g]
 return [line for part in g.geoms for line in lines(part)] if hasattr(g,'geoms') else []

def merge(geometries):
 merged=unary_union([line for g in geometries for line in lines(g)])
 return linemerge(merged) if merged.geom_type=='MultiLineString' else merged

west,north=world(CROP[0],CROP[3]);east,south=world(CROP[2],CROP[1]);crop=box(west,north,east,south)
raw={i:[] for i in IDS};cores={i:[] for i in IDS};properties={};source_tiles={i:[] for i in IDS};inputs=[]
for path in sorted(ROOT.glob('bund-map.*.pbf')):
 z,x,y=map(int,path.stem.split('.')[1:]);assert z==Z
 layer=mapbox_vector_tile.decode(path.read_bytes())['transportation'];extent=layer.get('extent',4096);assert extent==EXTENT
 core=box(x*EXTENT,y*EXTENT,(x+1)*EXTENT,(y+1)*EXTENT)
 for feature in layer['features']:
  fid=feature.get('id')
  if fid not in IDS:continue
  assert feature['geometry']['type'] in ('LineString','MultiLineString')
  # Preserve integer MVT vertices in one common Mercator grid until output.
  g=transform(lambda px,py,z=None:(x*EXTENT+px,(y+1)*EXTENT-py),shape(feature['geometry']))
  raw[fid].append(g);cores[fid].append(g.intersection(core));source_tiles[fid].append([z,x,y])
  if fid in properties:assert properties[fid]==feature['properties'], 'Conflicting attributes for one source feature'
  properties[fid]=dict(feature['properties'])
 inputs.append({'file':path.name,'tile':[z,x,y],'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
assert len(inputs)==4 and all(raw[i] for i in IDS)
output=[];records=[]
for fid in IDS:
 original=merge(cores[fid]);kept=merge([original.difference(crop)]);removed=merge([original.intersection(crop)])
 raw_outside=merge([g.difference(crop) for g in raw[fid]])
 original_m=original.length*METRES_PER_UNIT;kept_m=kept.length*METRES_PER_UNIT;removed_m=removed.length*METRES_PER_UNIT
 coverage_loss=raw_outside.difference(kept.buffer(.001)).length*METRES_PER_UNIT
 missing=original.difference(unary_union([kept,removed]).buffer(.000001)).length*METRES_PER_UNIT
 inside=kept.intersection(crop.buffer(-.000001)).length*METRES_PER_UNIT
 assert coverage_loss<.001 and missing<.001 and inside<.001
 assert abs(original_m-kept_m-removed_m)<.001
 for ordinal,line in enumerate(lines(kept)):
  output.append({'type':'Feature','id':f'bund-road-remainder-{fid}-{ordinal}',
   'properties':{**properties[fid],'source_mvt_id':fid,'mvt_id':fid,'source_layer':'transportation'},
   'geometry':mapping(transform(geographic,line))})
 records.append({'source_mvt_id':fid,'source_properties':properties[fid],'source_tiles':source_tiles[fid],
  'buffered_source_length_sum_m':sum(g.length for g in raw[fid])*METRES_PER_UNIT,
  'original_deduplicated_core_length_m':original_m,'retained_outside_crop_length_m':kept_m,'removed_inside_crop_length_m':removed_m,
  'retained_fragment_count':len(lines(kept)),'original_merged_piece_count':len(lines(original)),
  'outside_source_coverage_loss_m':coverage_loss,'missing_partition_length_m':missing,'retained_length_inside_crop_m':inside,
  'length_balance_error_m':abs(original_m-kept_m-removed_m)})
collection={'type':'FeatureCollection','features':output}
path=PROJECT/'data/bund/basemap-road-remainders-v4.geojson';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(collection,ensure_ascii=False,separators=(',',':'))+'\n')
metadata={'version':4,'suppressed_feature_ids':IDS,'layer_ids':LAYERS,'source_layer':'transportation','source_snapshot':'OpenFreeMap 20261018_080001_pt','geojson':'data/bund/basemap-road-remainders-v4.geojson','crop_wgs84_west_south_east_north':CROP,
 'crop':{'type':'Polygon','coordinates':[[[CROP[0],CROP[1]],[CROP[2],CROP[1]],[CROP[2],CROP[3]],[CROP[0],CROP[3]],[CROP[0],CROP[1]]]]},
 'units':'Lengths in local Mercator metres at latitude 31.2385, consistent with the street model.',
 'deduplication':'Clip each buffered source feature to its nominal tile core, then unary_union and linemerge. Tiny tile-seam roundoff is retained; no coordinate snapping or widening.',
 'source_inputs':inputs,'features':records,'totals':{key:sum(r[key] for r in records) for key in ['original_deduplicated_core_length_m','retained_outside_crop_length_m','removed_inside_crop_length_m']},
 'coverage_validation':{'passed':True,'all_requested_feature_ids_found':True,'only_two_requested_ids_used':True,'all_source_outside_crop_preserved':True,'no_retained_segment_inside_crop':True,'length_partition_balanced':True,'tolerance_m':.001,'no_geometry_widening':True},
 'activation':'Only while the local Bund street GLB is successfully visible, walk mode is active and zoom>=18. Restore original layer filters on disable/load failure; keep remainder layers hidden otherwise.',
 'geometry_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'geojson_bytes':path.stat().st_size,'attribution':'© OpenStreetMap contributors; OpenFreeMap / OpenMapTiles','license':'ODbL-1.0 derived line geometry; original generator MIT'}
(PROJECT/'data/bund/basemap-road-remainders-v4.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'features':records,'totals':metadata['totals'],'bytes':metadata['geojson_bytes']},ensure_ascii=False))
