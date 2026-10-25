"""Bund v4 mapped roads, pavement, crossings and photo-proportioned waterside fittings.
Public OSM positions; dimensions and fitting spacing are reconstruction estimates.
No facade imagery is used as a texture. GLB has local metres, X east/Y up/Z south.
"""
from pathlib import Path
import sys,json,math,struct,subprocess,hashlib
import numpy as np
from shapely.geometry import shape,LineString,Polygon,box,Point,mapping
from shapely.ops import transform,unary_union,linemerge
ROOT=Path(__file__).resolve().parent
PROJECT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PROJECT/'source/city'))
from build_district_models import Mesh,local_coordinates
from road_geometry import assemble as assemble_roads
ORIGIN=(121.4862,31.2385)
local=lambda x,y,z=None:local_coordinates(x,y,ORIGIN)
def metric(g):return transform(local,g)
def geographic(g):
 scale=math.cos(math.radians(ORIGIN[1]));origin_y=math.asinh(math.tan(math.radians(ORIGIN[1])))
 def inverse(x,z):return ORIGIN[0]+math.degrees(x/(6378137*scale)),math.degrees(math.atan(math.sinh(origin_y-z/(6378137*scale))))
 return transform(inverse,g)
COLORS={'BundStonePaving':(.39,.40,.37,1),'BundGraniteCurb':(.48,.49,.46,1),'BundRoadPaint':(.82,.83,.76,1),'BundRoadSurface':(.065,.075,.080,1),'BundRoadYellowPaint':(.62,.43,.055,1),'BundRoadGutter':(.20,.21,.20,1),'BundDrainDark':(.025,.030,.028,1),'BundDrainSteel':(.13,.15,.14,1),'BundRailingSteel':(.12,.14,.14,1),'BundLampSilver':(.34,.36,.35,1),'BundLampGlass':(.80,.84,.76,1)}
M={name:Mesh() for name in COLORS}
TRACK_RAIL=False
RAIL_VERTICES=[]
def face(mesh,points):
 p=np.asarray(points,float);n=np.cross(p[1]-p[0],p[2]-p[0]);length=np.linalg.norm(n)
 if length<1e-10:return
 if TRACK_RAIL:RAIL_VERTICES.extend((float(v[0]),float(v[2])) for v in p)
 start=mesh.vertices([tuple(v) for v in p],tuple(n/length))
 for i in range(1,len(points)-1):mesh.indices.extend([start,start+i,start+i+1])
def cuboid(name,center,size):
 x,y,z=center;a,b,c=[v/2 for v in size]
 verts=[(x+aa*a,y+bb*b,z+cc*c) for aa,bb,cc in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
 for inds in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face(M[name],[verts[i] for i in inds])
def rod(name,start,end,radius,segments=10):
 a,b=np.array(start,float),np.array(end,float);n=b-a;n/=np.linalg.norm(n)
 u=np.cross(n,[0,1,0])
 if np.linalg.norm(u)<.01:u=np.array([1.,0.,0.])
 u/=np.linalg.norm(u);v=np.cross(n,u)
 rings=[[p+radius*(math.cos(i*math.tau/segments)*u+math.sin(i*math.tau/segments)*v) for i in range(segments)] for p in [a,b]]
 face(M[name],list(reversed(rings[0])));face(M[name],rings[1])
 for i in range(segments):j=(i+1)%segments;face(M[name],[rings[0][i],rings[0][j],rings[1][j],rings[1][i]])
def polygons(g):
 if g.is_empty:return []
 return [g] if g.geom_type=='Polygon' else [p for part in g.geoms for p in polygons(part)] if hasattr(g,'geoms') else []
def lines(g):
 if g.is_empty:return []
 return [g] if g.geom_type=='LineString' else [p for part in g.geoms for p in lines(part)] if hasattr(g,'geoms') else []
def solid(name,g,z0,z1):
 mesh=M[name]
 for poly in polygons(g):
  rings=[list(poly.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in poly.interiors]
  mesh.polygon(rings,z0,z1,mesh)
def vector_at(line,d):
 a=np.array(line.interpolate(max(0,d-.1)).coords[0]);b=np.array(line.interpolate(min(line.length,d+.1)).coords[0]);t=b-a;t/=np.linalg.norm(t);return t,np.array([-t[1],t[0]])
def lamp(x,z,road=False):
 material='BundRailingSteel' if road else 'BundLampSilver';height=5.6 if road else 4.3
 cuboid('BundGraniteCurb',(x,.15,z),(.35,.30,.35));rod(material,(x,.25,z),(x,height,z),.065,12)
 if road:
  pts=[(x,height-.55,z),(x+.15,height-.10,z),(x+.6,height+.15,z),(x+1.45,height+.25,z)]
  for a,b in zip(pts,pts[1:]):rod(material,a,b,.05,10)
  cuboid(material,(x+1.55,height+.22,z),(1.05,.13,.30));cuboid('BundLampGlass',(x+1.55,height+.145,z),(.84,.025,.23))
 else:
  rod(material,(x,height-.15,z),(x,height+.57,z),.17,16)
  rod('BundLampGlass',(x,height-.09,z),(x,height+.48,z),.14,16)
  # Four visible cage ribs and a shallow mushroom cap, as in the modern photo.
  for a in [0,math.pi/2,math.pi,math.pi*1.5]:
   dx,dz=.165*math.cos(a),.165*math.sin(a);rod(material,(x+dx,height-.15,z+dz),(x+dx,height+.55,z+dz),.016,6)
  rod(material,(x,height+.54,z),(x,height+.62,z),.24,16)

osm=json.loads((ROOT/'osm-street.json').read_text())['elements'];by_id={e['id']:e for e in osm}
ways={e['id']:metric(LineString([(p['lon'],p['lat']) for p in e['geometry']])) for e in osm if 'geometry' in e}
crop=metric(box(121.4842,31.23545,121.4892,31.2419))
sidewalk=ways[178412507].intersection(crop)
source_candidates=json.loads((ROOT.parent/'bund-candidates.json').read_text())['candidates']
buildings=unary_union([metric(shape(c['geometry'])) for c in source_candidates]).buffer(.08)
crossings=[]
for e in osm:
 if e.get('tags',{}).get('footway')!='crossing' or e['id'] not in ways:continue
 line=ways[e['id']].intersection(crop)
 for l in lines(line):
  if 5<l.length<70 and l.distance(sidewalk)<5:crossings.append((e['id'],l))
walk_surface=sidewalk.buffer(2.0,cap_style=2,join_style=2).difference(buildings)
# Crossing locations also anchor the retained photo-proportioned road lamps.
for _,line in crossings:
 ends=[Point(line.coords[0]),Point(line.coords[-1])];point=min(ends,key=lambda p:p.distance(sidewalk))
 x,z=sidewalk.interpolate(sidewalk.project(point)).coords[0];lamp(x+1.65,z+2.8,road=True)

map_features=json.loads((ROOT/'bund-map.geojson').read_text())['features']
water=unary_union([metric(shape(f['geometry'])) for f in map_features if f['properties']['layer']=='water' and f['geometry']['type'] in ['Polygon','MultiPolygon']])
tile_source=json.loads((ROOT/'tile-source.json').read_text())
expected_tiles={(14,x,y) for x in (13720,13721) for y in (6693,6694)}
assert {tuple(item['tile']) for item in tile_source.get('tiles',[])}==expected_tiles, 'Fetch all four Bund tiles before shoreline extraction.'
coverage=metric(box(*tile_source['coverage_bounds']))
assert coverage.contains(crop.buffer(5)), 'Bund crop must stay inside complete tile coverage.'
# Do not mistake polygon clipping edges for shore. Union the four water tiles
# first, then reject any remaining segment coincident with a nominal tile edge.
tile_edges=[]
for item in tile_source['tiles']:
 w,s,e,n=item['bounds']
 tile_edges.extend(metric(LineString(pair)) for pair in [((w,s),(w,n)),((e,s),(e,n)),((w,s),(e,s)),((w,n),(e,n))])
physical_segments=[];rejected_tile_edge_m=0.0
for line in lines(water.boundary.intersection(crop)):
 for a,b in zip(line.coords,list(line.coords)[1:]):
  segment=LineString([a,b])
  if segment.length<.001:continue
  cut=any(Point(a).distance(edge)<.005 and Point(b).distance(edge)<.005 for edge in tile_edges)
  if cut:rejected_tile_edge_m+=segment.length
  else:physical_segments.append(segment)
joined=unary_union(physical_segments)
joined=linemerge(joined) if joined.geom_type!='LineString' else joined
# An independent mapped promenade identifies the Puxi bank. A long artificial
# edge or the opposite bank must never win simply because it is the longest.
inner=ways[909084827].intersection(crop);inner=max(lines(inner),key=lambda l:l.length)
shore_candidates=[]
for line in lines(joined):
 if line.length<100:continue
 samples=[line.interpolate(d) for d in np.linspace(.5,line.length-.5,41)]
 western=sum(water.covers(Point(p.x+3,p.y)) and not water.covers(Point(p.x-3,p.y)) for p in samples)/len(samples)
 mean_distance=sum(p.distance(inner) for p in samples)/len(samples)
 if western>=.95 and mean_distance<70:shore_candidates.append((mean_distance,line,western))
assert shore_candidates, 'No verified west-bank shoreline near the mapped promenade.'
mean_inner_distance,shore,west_bank_fraction=min(shore_candidates,key=lambda item:item[0])
assert shore.bounds[1]<=crop.bounds[1]+1 and shore.bounds[3]>=crop.bounds[3]-1, 'Selected shore does not span the Bund crop.'
t,n=vector_at(shore,shore.length/2);mid=np.array(shore.interpolate(shore.length/2).coords[0]);land_side=1 if not water.contains(Point(mid+n)) else -1
rail_setback=.65  # .43m square granite posts also stay within 1m of the shoreline.
rail=shore.offset_curve(land_side*rail_setback,join_style=1)
rail=max(lines(rail),key=lambda l:l.length)
# Pavement between two mapped references. Its exact construction edge/altitude
# is not surveyed; it stays close to the existing map's level for walk controls.
a=list(rail.coords);b=list(inner.coords)
if a[0][1]>a[-1][1]:a.reverse()
if b[0][1]<b[-1][1]:b.reverse()
promenade=Polygon(a+b).buffer(0).difference(water).difference(buildings)
solid('BundStonePaving',promenade,.005,.035)
post_count=0;lamps=0
rail_breaks=[rail.project(Point(point)) for point in rail.coords]
def waterward(d):
 p=np.array(rail.interpolate(d).coords[0]);q=np.array(shore.interpolate(shore.project(Point(p))).coords[0]);v=q-p
 return v/np.linalg.norm(v)
TRACK_RAIL=True
for d0 in np.arange(0,rail.length,8.0):
 d1=min(d0+8.0,rail.length)
 p=np.array(rail.interpolate(d0).coords[0]);t,n=vector_at(rail,d0+.01)
 # Keep the leaning top toward water; OSM geometry determines the side.
 toward_water=waterward(d0)
 cuboid('BundGraniteCurb',(p[0],.51,p[1]),(.43,1.02,.43));post_count+=1
 for h,radius in [(.29,.022),(.52,.022),(.76,.022),(1.08,.055)]:
  # Follow every mapped bend; a single 8m chord can cut across a curved shore.
  knots=sorted(set([float(d0),float(d1)]+[d for d in rail_breaks if d0<d<d1]))
  for da,db in zip(knots,knots[1:]):
   pa=np.array(rail.interpolate(da).coords[0])+waterward(da)*(h/1.08*.24)
   pb=np.array(rail.interpolate(db).coords[0])+waterward(db)*(h/1.08*.24)
   rod('BundRailingSteel',(pa[0],h,pa[1]),(pb[0],h,pb[1]),radius,8)
 for d in np.arange(d0+.9,d1,.95):
  p=np.array(rail.interpolate(d).coords[0]);top=p+waterward(d)*.24
  rod('BundRailingSteel',(p[0],.12,p[1]),(top[0],1.08,top[1]),.035,8)
 if round(d0)%32==0:
  TRACK_RAIL=False
  p=p-waterward(min(d1,rail.length))*.75;lamp(p[0],p[1]);lamps+=1
  TRACK_RAIL=True
end=np.array(rail.interpolate(rail.length).coords[0])
cuboid('BundGraniteCurb',(end[0],.51,end[1]),(.43,1.02,.43));post_count+=1
TRACK_RAIL=False
# Validate both a densely sampled centreline and every emitted railing/post
# vertex against the merged real west shoreline, not against a tile rectangle.
sample_distances=[rail.interpolate(d).distance(shore) for d in np.linspace(0,rail.length,int(math.ceil(rail.length/.25))+1)]
vertex_distances=[Point(x,z).distance(shore) for x,z in set(RAIL_VERTICES)]
max_sample_distance=max(sample_distances);max_vertex_distance=max(vertex_distances)
assert max_sample_distance<1.0 and max_vertex_distance<1.0, (max_sample_distance,max_vertex_distance)
assert not any(water.contains(rail.interpolate(d)) for d in np.linspace(0,rail.length,1001)), 'Railing centreline entered the river.'
shoreline_audit={'passed':True,'source_tiles':[list(tile) for tile in sorted(expected_tiles)],
 'water_union_before_boundary':True,'selected_west_bank_fraction':west_bank_fraction,
 'mean_distance_to_mapped_promenade_m':mean_inner_distance,'shoreline_length_m':shore.length,
 'rail_setback_m':rail_setback,'centreline_sample_spacing_max_m':.25,'centreline_samples':len(sample_distances),
 'railing_and_post_vertices_tested':len(set(RAIL_VERTICES)),
 'max_centreline_distance_to_real_shore_m':max_sample_distance,
 'max_railing_vertex_distance_to_real_shore_m':max_vertex_distance,
 'remaining_tile_edge_segments_rejected_m':rejected_tile_edge_m,'rail_in_water':False}
(ROOT/'bund-streets-shoreline-check.json').write_text(json.dumps(shoreline_audit,ensure_ascii=False,indent=2))
(ROOT/'bund-streets-shoreline-check.geojson').write_text(json.dumps({'type':'FeatureCollection',
 'coordinate_system':'WGS84 longitude / latitude',
 'features':[{'type':'Feature','properties':{'role':role},'geometry':mapping(geographic(g))} for role,g in
 [('merged_water',water.intersection(crop)),('real_west_shoreline',shore),('railing_centerline',rail),('mapped_inner_promenade',inner)]]},separators=(',',':')))

# v4 actual OSM vehicular network, excluding all underground/raised ways.
road_elements=json.loads((ROOT/'osm-roads.json').read_text())['elements']
roads=assemble_roads(road_elements,metric,crop,buildings,water,walk_surface,crossings)
roads['audit']['building_validation_scope']={
 'source':'../bund-candidates.json',
 'geometry_field':'candidates[*].geometry',
 'candidate_count':len(source_candidates),
 'candidate_ids':[c['id'] for c in source_candidates],
 'candidates_intersecting_street_crop':[c['id'] for c in source_candidates if metric(shape(c['geometry'])).intersects(crop)],
 'geometry_sha256':hashlib.sha256(json.dumps({c['id']:c['geometry'] for c in source_candidates},sort_keys=True,separators=(',',':')).encode()).hexdigest(),
 'footprint_buffer_m':.08,
 'scope':'Only the ten listed Bund candidate ground footprints, clipped to this street crop. Not a check against all Shanghai buildings, neighboring generic buildings, detailed mesh projections, linked parts or related_geometries (including the Bank of China western wing).',
 'street_crop_wgs84':[121.4842,31.23545,121.4892,31.2419],
 'observed_overlap_m2':roads['audit']['surface_building_overlap_m2']}
# Fill the actual mapped pedestrian polygon left between the older path-based
# pavement strips. This is a real MVT polygon, never an invented rectangle.
pedestrian_features=[f for f in map_features if f.get('id')==21420773 and f['geometry']['type'] in ('Polygon','MultiPolygon')]
assert pedestrian_features, 'The mapped Bund pedestrian footprint is required.'
pedestrian_footprint=unary_union([metric(shape(f['geometry'])) for f in pedestrian_features]).intersection(crop)
existing_paving=promenade.union(walk_surface).union(roads['shoulder'])
pedestrian_paving=pedestrian_footprint.difference(water).difference(buildings).difference(roads['surface']).difference(existing_paving).difference(roads['curb'])
solid('BundStonePaving',pedestrian_paving,.005,.035)
paving_audit={'passed':True,'source':'bund-map.geojson / OpenFreeMap transportation polygon',
 'source_mvt_feature_id':21420773,'source_tiles':[list(tile) for tile in sorted(expected_tiles)],
 'source_geometry_is_mapped_polygon':True,'mapped_polygon_area_within_crop_m2':pedestrian_footprint.area,
 'new_paving_area_m2':pedestrian_paving.area,'top_height_m':.035,
 'water_overlap_m2':pedestrian_paving.intersection(water).area,
 'candidate_footprint_overlap_m2':pedestrian_paving.intersection(buildings).area,
 'road_surface_overlap_m2':pedestrian_paving.intersection(roads['surface']).area,
 'existing_paving_overlap_m2':pedestrian_paving.intersection(existing_paving).area,
 'area_outside_mapped_polygon_m2':pedestrian_paving.difference(pedestrian_footprint).area,
 'building_validation_scope':roads['audit']['building_validation_scope'],
 'note':'MVT feature 21420773 is a source feature identifier, not asserted to be an OSM way ID. Physical paving thickness/material are reconstruction estimates; plan geometry follows the actual mapped footprint.'}
assert all(paving_audit[key]<1e-6 for key in ('water_overlap_m2','candidate_footprint_overlap_m2','road_surface_overlap_m2','existing_paving_overlap_m2','area_outside_mapped_polygon_m2')), paving_audit
(ROOT/'bund-streets-paving-check.json').write_text(json.dumps(paving_audit,ensure_ascii=False,indent=2))
(ROOT/'bund-streets-paving-check.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[
 {'type':'Feature','properties':{'role':role,'source_mvt_feature_id':21420773},'geometry':mapping(geographic(g))}
 for role,g in [('mapped_pedestrian_footprint',pedestrian_footprint),('new_3d_paving',pedestrian_paving),('previous_3d_paving',existing_paving.intersection(crop))]]},separators=(',',':')))
solid('BundRoadSurface',roads['surface'],.002,.020)
solid('BundStonePaving',walk_surface.union(roads['shoulder']).difference(water),.003,.075)
solid('BundGraniteCurb',roads['curb'],.006,.14)
solid('BundRoadGutter',roads['gutter'],.020,.023)
solid('BundRoadYellowPaint',roads['yellow_curb'],.012,.143)
solid('BundRoadPaint',roads['lane_paint'].union(roads['zebras']),.025,.029)
solid('BundRoadYellowPaint',roads['median_paint'],.025,.029)
for drain in roads['drains']:
 solid('BundDrainDark',drain['polygon'],.024,.030)
 p,t,n=drain['center'],drain['tangent'],drain['inward']
 for offset in np.linspace(-.34,.34,9):
  a=p+t*offset-n*.115;b=p+t*offset+n*.115
  bar=LineString([a,b]).buffer(.013,cap_style=2).intersection(drain['polygon'])
  solid('BundDrainSteel',bar,.030,.035)
assert roads['audit']['passed'], 'Road/water/building geometric overlap validation failed.'
(ROOT/'bund-streets-road-check.json').write_text(json.dumps(roads['audit'],ensure_ascii=False,indent=2))
(ROOT/'bund-streets-road-check.geojson').write_text(json.dumps({'type':'FeatureCollection','features':[
 {'type':'Feature','properties':{'role':role},'geometry':mapping(geographic(roads[key]))}
 for role,key in [('asphalt_surface','surface'),('curb','curb'),('gutter','gutter'),('lane_paint','lane_paint'),('central_separation_estimate','median_paint'),('mapped_crossings','zebras'),('sidewalk_infill_estimate','shoulder')]]
 +[{'type':'Feature','properties':{'role':'OSM_centerline','osm_way':r['id'],'tags':r['tags'],'estimated_width_m':r['width']},'geometry':mapping(geographic(r['line']))} for r in roads['records']]},ensure_ascii=False,separators=(',',':')))

# Pack one primitive per material; no external texture or buffer dependency.
binary=bytearray();views=[];accessors=[];primitives=[];materials=[]
def append(data,target,component,type_,count,minimum=None,maximum=None):
 while len(binary)%4:binary.append(0)
 offset=len(binary);binary.extend(data);view=len(views);views.append({'buffer':0,'byteOffset':offset,'byteLength':len(data),'target':target})
 a={'bufferView':view,'componentType':component,'count':count,'type':type_}
 if minimum is not None:a['min']=minimum;a['max']=maximum
 accessors.append(a);return len(accessors)-1
triangles=0;discarded_zero_area_triangles=0
for name,mesh in M.items():
 if not mesh.indices:continue
 v=np.asarray(mesh.positions,dtype='<f4');n=np.asarray(mesh.normals,dtype='<f4');idx=np.asarray(mesh.indices,dtype='<u4').reshape(-1,3)
 # Float32 conversion can collapse sub-millimetre polygon slivers. Remove only
 # exact zero-area triangles, preserving every measurable construction face.
 tv=v[idx].astype(float);keep=np.linalg.norm(np.cross(tv[:,1]-tv[:,0],tv[:,2]-tv[:,0]),axis=1)>0
 discarded_zero_area_triangles+=int((~keep).sum());idx=idx[keep].reshape(-1)
 vi=append(v.tobytes(),34962,5126,'VEC3',len(v),v.min(axis=0).tolist(),v.max(axis=0).tolist());ni=append(n.tobytes(),34962,5126,'VEC3',len(n));ii=append(idx.tobytes(),34963,5125,'SCALAR',len(idx))
 mi=len(materials);materials.append({'name':name,'pbrMetallicRoughness':{'baseColorFactor':COLORS[name],'metallicFactor':.45 if 'Steel' in name or 'Silver' in name else .02,'roughnessFactor':.35 if 'Glass' in name else .94 if name=='BundRoadSurface' else .72}})
 primitives.append({'attributes':{'POSITION':vi,'NORMAL':ni},'indices':ii,'material':mi});triangles+=len(idx)//3
gltf={'asset':{'version':'2.0','generator':'Shanghai Bund street reconstruction v4'},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':'Bund mapped public streetscape','mesh':0}],'meshes':[{'primitives':primitives}],'materials':materials,'buffers':[{'byteLength':len(binary)}],'bufferViews':views,'accessors':accessors}
j=json.dumps(gltf,separators=(',',':')).encode();j+=b' '*((-len(j))%4);binary+=b'\0'*((-len(binary))%4)
output=ROOT/'bund-streets.glb';output.write_bytes(struct.pack('<III',0x46546c67,2,12+8+len(j)+8+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(binary),0x004e4942)+binary)
metadata={'id':'bund-streets','anchor':list(ORIGIN),'units':'metres, X east / Y up / Z south','triangles':triangles,'bytes':output.stat().st_size,'mapped_sidewalk_way':178412507,'mapped_inner_promenade_way':909084827,'mapped_crossing_ways':[i for i,_ in crossings],'shoreline_source':'bund-map.geojson / OSM water via OpenFreeMap','railing_length_m':round(rail.length,3),'granite_posts':post_count,'promenade_lamps':lamps,'dimensions_are_estimates':{'sidewalk_width_m':4.0,'curb_height_m':.14,'handrail_height_m':1.08,'lamp_spacing_m':32,'crossing_paint_width_m':3.5},'accuracy':'Mapped path/shoreline positions. Pavement width, construction heights, rail/lamp shape and spacing are photo-proportioned reconstruction, not a survey; current game ground level is retained.','reference':'Modern wide-granite promenade photo in promenade-photo-search.json (Bund Promenade panoramio, CC BY 3.0); older Promenade du Bund photograph was inspected only to distinguish former fittings.','license':'ODbL-1.0 derived street database; original fitting meshes/code MIT; reference photograph licensing retained separately.'}
metadata['shoreline_validation']=shoreline_audit
metadata['road_validation']=roads['audit']
metadata['paving_validation']=paving_audit
metadata['version']=4
metadata['source_roads']='osm-roads.json / OpenStreetMap ODbL-1.0'
metadata['reference_2025']='street-reference-evidence.json: Suicasmo CC0 street-level facade views, 2025-05-01'
metadata['accuracy']+=' Ground road centerlines/lane counts follow OSM; widths and paint/drain dimensions are estimated and itemized in road_validation.'
metadata['source_tiles']=[list(tile) for tile in sorted(expected_tiles)]
metadata['sha256']=hashlib.sha256(output.read_bytes()).hexdigest()
for name,mesh in M.items():
 assert np.isfinite(np.asarray(mesh.positions)).all(), 'Nonfinite vertices in '+name
 if mesh.indices:assert min(mesh.indices)>=0 and max(mesh.indices)<len(mesh.positions), 'Invalid indices in '+name
metadata['geometry_validation']={'finite_vertices':True,'indices_in_range':True,'zero_area_triangles_removed':discarded_zero_area_triangles,'exported_zero_area_triangles':0,'single_file_under_100MB':output.stat().st_size<100_000_000}
(ROOT/'bund-streets.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2));assert output.stat().st_size<100_000_000;print(json.dumps({'bytes':metadata['bytes'],'triangles':triangles,'sha256':metadata['sha256'],'roads':len(roads['records']),'shoreline':shoreline_audit},ensure_ascii=False))
