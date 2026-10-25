"""OSM-backed Bund road surfaces and explicitly estimated construction details.

No grid, random tree, invented road or at-grade tunnel geometry is generated.
All returned ground coordinates are local X east / Z south metres.
"""
import math,re
import numpy as np
from shapely.geometry import LineString,Point,Polygon,GeometryCollection
from shapely.ops import unary_union,linemerge,substring


def pieces(g,kind):
 if g.is_empty:return []
 if g.geom_type==kind:return [g]
 return [p for c in g.geoms for p in pieces(c,kind)] if hasattr(g,'geoms') else []


def numeric(text):
 match=re.match(r'^\s*([0-9]+(?:\.[0-9]+)?)\s*(?:m)?\s*$',str(text))
 return float(match.group(1)) if match else None


def assemble(elements,metric,crop,buildings,water,walk_surface,crossings):
 records=[];skipped=[]
 for element in elements:
  if element['type']!='way' or 'geometry' not in element:continue
  tags=element.get('tags',{})
  original=metric(LineString([(p['lon'],p['lat']) for p in element['geometry']]))
  if not original.intersects(crop):continue
  if tags.get('tunnel') in ['yes','building_passage'] or float(tags.get('layer','0'))<0:
   skipped.append({'osm_way':element['id'],'reason':'underground/tunnel','tags':tags});continue
  if tags.get('bridge')=='yes' or float(tags.get('layer','0'))>0:
   skipped.append({'osm_way':element['id'],'reason':'above ground, needs explicit bridge height','tags':tags});continue
  lane_count=numeric(tags.get('lanes'))
  measured_width=numeric(tags.get('width'))
  if measured_width:
   width=measured_width;basis='OSM width tag'
  elif lane_count:
   lane_width=2.9 if tags.get('highway')=='secondary' else 3.0
   width=lane_count*lane_width+.3
   if tags.get('cycleway')=='opposite_lane':width+=1.5
   basis='OSM lane count × estimated lane width + 0.3m edge clearance'
  else:
   width=4.0 if tags.get('highway')=='service' else 5.8
   basis='class-based width estimate; no OSM lanes/width'
  for line in pieces(original.intersection(crop),'LineString'):
   if line.length<.2:continue
   records.append({'id':element['id'],'line':line,'tags':tags,'width':width,'width_basis':basis,'lanes':int(lane_count) if lane_count else None})
 raw=unary_union([r['line'].buffer(r['width']/2,cap_style=2,join_style=1,quad_segs=6) for r in records])
 road=raw.intersection(crop).difference(buildings).difference(water).difference(walk_surface)
 # The outside of the complete network has no curbs across junction mouths.
 boundary=road.boundary.difference(crop.boundary.buffer(.3)).difference(buildings.buffer(.3)).difference(water.buffer(.3))
 crossing_cuts=unary_union([line.buffer(2.5,cap_style=2) for _,line in crossings])
 boundary=boundary.difference(crossing_cuts)
 # A buffer OUTSIDE the carriageway gives the visible curb face and narrow stone edge.
 curb=boundary.buffer(.12,cap_style=2,quad_segs=3).difference(road.buffer(-.01)).difference(buildings).difference(water)
 gutter=boundary.buffer(.28,cap_style=2,quad_segs=3).intersection(road)
 main=[r for r in records if r['tags'].get('name')=='中山东一路']
 mainlines=unary_union([r['line'] for r in main])
 # Paint yellow only on the building-side main-road curb documented in 2025 photos.
 yellow_edges=[]
 for line in pieces(boundary,'LineString'):
  for a,b in zip(line.coords,list(line.coords)[1:]):
   segment=LineString([a,b]);middle=segment.interpolate(.5,normalized=True)
   nearest=mainlines.interpolate(mainlines.project(middle))
   if middle.distance(mainlines)<5.3 and middle.x<nearest.x:
    yellow_edges.append(segment)
 yellow=unary_union(yellow_edges).buffer(.105,cap_style=2,quad_segs=2).intersection(curb)
 # Road labels never invent lane count. Dashed separators are limited to tagged lanes.
 node_use={}
 for r in records:
  for p in (r['line'].coords[0],r['line'].coords[-1]):node_use.setdefault((round(p[0],1),round(p[1],1)),[]).append(r)
 junctions=[]
 for p,group in node_use.items():
  if len(group)>1 and len({r['tags'].get('name',r['id']) for r in group})>1:junctions.append(Point(p).buffer(max(r['width'] for r in group)*.55+2))
 for r in records:
  if r['tags'].get('name')!='中山东一路' and r['tags'].get('highway')!='service':
   for p in (r['line'].coords[0],r['line'].coords[-1]):
    if Point(p).distance(mainlines)<3:junctions.append(Point(p).buffer(8))
 paint_mask=road.buffer(-.24).difference(crossing_cuts.buffer(.5)).difference(unary_union(junctions))
 lane_paint=[];lane_segments=0
 for r in records:
  if not r['lanes'] or r['lanes']<2:continue
  for i in range(1,r['lanes']):
   offset=r['width']*(i/r['lanes']-.5)
   for line in pieces(r['line'].offset_curve(offset,join_style=1),'LineString'):
    for distance in np.arange(1.5,line.length,9):
     segment=substring(line,float(distance),min(float(distance+3),line.length))
     if segment.length<.2:continue
     mark=segment.buffer(.065,cap_style=2).intersection(paint_mask)
     if not mark.is_empty:lane_paint.append(mark);lane_segments+=1
 # Opposite OSM carriageways provide the physical central separation curve.
 # A subdued 0.12m single line is a reconstruction assumption, not an observed survey.
 east=unary_union([r['line'] for r in main if r['id'] in (40301368,1298040465)])
 west=unary_union([r['line'] for r in main if r['id'] not in (40301368,1298040465)])
 median_lines=[]
 for line in pieces(east,'LineString'):
  run=[]
  for d in np.linspace(0,line.length,max(2,int(line.length/2)+1)):
   p=line.interpolate(d);q=west.interpolate(west.project(p))
   if 4<p.distance(q)<13:run.append(((p.x+q.x)/2,(p.y+q.y)/2))
   elif len(run)>1:median_lines.append(LineString(run));run=[]
  if len(run)>1:median_lines.append(LineString(run))
 median=unary_union(median_lines).buffer(.06,cap_style=2).intersection(paint_mask)
 # Zebra axes are independently mapped crossing ways. Clip paint to the road.
 zebra=[];crossing_ids=[]
 for osm_id,line in crossings:
  count=0
  for d in np.arange(.3,line.length-.25,1.15):
   p=np.array(line.interpolate(d).coords[0]);a=np.array(line.interpolate(max(0,d-.15)).coords[0]);b=np.array(line.interpolate(min(line.length,d+.15)).coords[0]);t=b-a;t/=np.linalg.norm(t);n=np.array([-t[1],t[0]])
   stripe=Polygon([p-t*.24-n*1.75,p+t*.24-n*1.75,p+t*.24+n*1.75,p-t*.24+n*1.75]).intersection(road.buffer(-.05))
   if not stripe.is_empty:zebra.append(stripe);count+=1
  if count:crossing_ids.append({'osm_way':osm_id,'stripes':count})
 # Simple gutter slots. Locations at 18m estimated intervals, documented as such.
 # Only the photo-verified building-side arterial curb gets grates.
 drains=[]
 drain_paths=unary_union(yellow_edges)
 if drain_paths.geom_type=='MultiLineString':drain_paths=linemerge(drain_paths)
 for line in pieces(drain_paths,'LineString'):
  for d in np.arange(6,line.length,18):
   p=np.array(line.interpolate(d).coords[0]);a=np.array(line.interpolate(max(0,d-.1)).coords[0]);b=np.array(line.interpolate(min(line.length,d+.1)).coords[0]);t=b-a;t/=np.linalg.norm(t);n=np.array([-t[1],t[0]])
   if not road.contains(Point(p+n*.2)):n=-n
   p=p+n*.19
   shape=Polygon([p-t*.4-n*.14,p+t*.4-n*.14,p+t*.4+n*.14,p-t*.4+n*.14]).intersection(road)
   if shape.area>.1:drains.append({'polygon':shape,'center':p,'tangent':t,'inward':n})
 # Sidewalk infill is a 1.4m shoulder outside mapped vehicular edges; it is
 # explicitly inferred and clipped out of buildings, river and crossing ramps.
 shoulder=raw.buffer(1.4,quad_segs=3).difference(raw).intersection(crop).difference(buildings).difference(water).difference(crossing_cuts)
 audit={'source_way_count':len({r['id'] for r in records}),'rendered_way_ids':sorted({r['id'] for r in records}),
        'roads':[{'osm_way':r['id'],'name':r['tags'].get('name'),'tags':r['tags'],'width_m':r['width'],'width_basis':r['width_basis'],'length_m':round(r['line'].length,3)} for r in records],
        'skipped_ways':skipped,'road_area_m2':round(road.area,3),'surface_building_overlap_m2':road.intersection(buildings).area,
        'surface_water_overlap_m2':road.intersection(water).area,'lane_dash_segments':lane_segments,'mapped_zebras':crossing_ids,
        'estimated_drain_grates':len(drains),'added_trees':0,
        'inferred_dimensions_m':{'tagged_secondary_lane_width':2.9,'other_tagged_lane_width':3.0,'road_edge_clearance':.3,'unknown_residential_width':5.8,'service_width':4.,'curb_width':.12,'curb_height':.14,'gutter_width':.28,'lane_line_width':.13,'lane_dash_length':3.,'lane_dash_gap':6.,'central_separation_line_width':.12,'zebra_stripe':.48,'zebra_pitch':1.15,'zebra_width':3.5,'drain_length':.8,'drain_width':.28,'drain_spacing':18.,'sidewalk_infill_width':1.4},
        'assumptions':['Centerlines, lane counts, travel direction and named crossings follow OSM. No width tag is fabricated.','Lane width and painted markings are reconstruction estimates. Single central separation line is inferred from opposing mapped carriageways; paint placement is not a contemporary traffic survey.','Road junctions remain open; line paint and curb are cut at mapped crossings.','Yellow building-side arterial curb, dark asphalt and gutter slots are verified by 2025 photographs; exact grate spacing is estimated.','No vegetation is added because mapped/photo evidence does not locate trunks within this crop.','Private service ways retain source tags and are not newly declared accessible.'],
        'passed':road.intersection(buildings).area<1e-6 and road.intersection(water).area<1e-6}
 return {'surface':road,'curb':curb,'gutter':gutter,'yellow_curb':yellow,'lane_paint':unary_union(lane_paint),'median_paint':median,'zebras':unary_union(zebra),'drains':drains,'shoulder':shoulder,'audit':audit,'records':records}
