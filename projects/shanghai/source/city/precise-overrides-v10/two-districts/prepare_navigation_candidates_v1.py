#!/usr/bin/env python3
"""Finite source-footprint observation proposals; no modeled mesh/browser acceptance."""
import argparse, gzip, hashlib, json, math, xml.etree.ElementTree as ET
from pathlib import Path
from shapely.geometry import Point, Polygon, LineString, shape
from shapely.ops import transform
from shapely.strtree import STRtree

HERE = Path(__file__).resolve().parent
R = 6378137.0

def desc(p):
    p=Path(p)
    return {'source':str(p.resolve()),'bytes':p.stat().st_size,
            'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest()}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--id',required=True)
    ap.add_argument('--context',type=Path,required=True)
    ap.add_argument('--project',type=Path,default=Path('/workspace/shanghai_project'))
    ap.add_argument('--envelope-half-width',type=float,required=True)
    ap.add_argument('--preferred-bearing-from-center',type=float,default=180)
    ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args(); assert a.output.resolve().is_relative_to(HERE) and not a.output.exists()
    inp=HERE/'inputs'/a.id/'geometry-input.json'; g=json.loads(inp.read_bytes())
    lon0,lat0=g['anchor']; scale=math.cos(math.radians(lat0)); mx=R*math.radians(lon0);my=R*math.log(math.tan(math.pi/4+math.radians(lat0)/2))
    def local(lon,lat):return ((R*math.radians(lon)-mx)*scale,(R*math.log(math.tan(math.pi/4+math.radians(lat)/2))-my)*scale)
    def geographic(x,y):return [math.degrees((mx+x/scale)/R),math.degrees(2*math.atan(math.exp((my+y/scale)/R))-math.pi/2)]
    target=transform(local,shape(g['geometry'])); envelope=Polygon([(-a.envelope_half_width,-a.envelope_half_width),(a.envelope_half_width,-a.envelope_half_width),(a.envelope_half_width,a.envelope_half_width),(-a.envelope_half_width,a.envelope_half_width)])
    mid=g['current_city_detail']['owner_macro_id']; zoom,x,y=map(int,mid.split('-'))
    # All effective features in owner+8 macro halo are read, not only same-near neighbors.
    sources=[]; neighbors=[]; seen={}; all_count=0
    for dx in (-1,0,1):
      for dy in (-1,0,1):
        path=a.project/'assets/city-detail/macros'/f'{zoom}-{x+dx}-{y+dy}'/'feature-table.json.gz'
        if not path.exists():continue
        table=json.loads(gzip.decompress(path.read_bytes()));sources.append(desc(path));all_count+=len(table['features'])
        for f in table['features']:
          if f['key']==g['current_city_detail']['frozen_effective_feature']['key']:continue
          geom=transform(local,shape(f['geometry']))
          if geom.distance(Point(0,0))>120:continue
          identity=(f['key'],geom.wkb)
          if identity in seen:continue
          seen[identity]=True;neighbors.append({'macro':f'{zoom}-{x+dx}-{y+dy}','local_id':f['localId'],'key':f['key'],'geometry':geom})
    tree=STRtree([n['geometry'] for n in neighbors])
    def hits(geometry,padding=0):
      query=geometry.buffer(padding) if padding else geometry
      return [{'macro':neighbors[int(i)]['macro'],'local_id':neighbors[int(i)]['local_id'],'key':neighbors[int(i)]['key']} for i in tree.query(query,predicate='intersects')]
    root=ET.fromstring(a.context.read_bytes());nodes={n.attrib['id']:local(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
    paths=[];barriers=[];waters=[]
    for w in root.findall('way'):
      tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')};refs=[n.attrib['ref'] for n in w.findall('nd')]
      if not all(i in nodes for i in refs) or len(refs)<2:continue
      pts=[nodes[i] for i in refs];line=LineString(pts)
      if tags.get('highway') in ('footway','path','pedestrian') and tags.get('layer','0')=='0' and tags.get('tunnel') not in ('yes','building_passage'):
        paths.append({'way_id':w.attrib['id'],'tags':tags,'geometry':line})
      if tags.get('barrier') in ('wall','fence','retaining_wall'):barriers.append({'way_id':w.attrib['id'],'tags':tags,'geometry':line})
      if refs[0]==refs[-1] and len(pts)>=4 and (tags.get('natural')=='water' or tags.get('waterway')=='riverbank'):
        p=Polygon(pts)
        if p.is_valid:waters.append({'way_id':w.attrib['id'],'tags':tags,'geometry':p})
    candidates=[]
    for path in paths:
      line=path['geometry']
      for i in range(int(math.ceil(line.length))+1):
        p=line.interpolate(min(i,line.length));radius=p.distance(Point(0,0))
        if 14<radius<50:candidates.append((p,{'kind':'mapped_surface_footway_candidate','way_id':path['way_id'],'tags':path['tags']}))
    if not candidates:
      # These angles are explicitly geometric proposals, not invented mapped paths.
      for radius in (20,24,28,32,36):
        for angle in range(0,360,10):
          theta=math.radians(angle);candidates.append((Point(radius*math.sin(theta),radius*math.cos(theta)),{'kind':'geometric_unmapped_observation_candidate'}))
    rows=[]
    for number,(p,basis) in enumerate(candidates):
      px,py=p.coords[0];length=math.hypot(px,py);direction=(-px/length,-py/length)
      ahead=(px+2.8*direction[0],py+2.8*direction[1]);eye=(ahead[0]-14*math.sin(math.radians(82))*direction[0],ahead[1]-14*math.sin(math.radians(82))*direction[1])
      boom=LineString([eye,ahead]);conservative=LineString([(px-14*direction[0],py-14*direction[1]),ahead]);rays=[LineString([eye,point]) for point in target.exterior.coords[:-1]]
      body_hits=hits(p,0.35);boom_hits=hits(conservative,0.12);ray_hits=[hits(ray,0) for ray in rays]
      barrier_hits=[x['way_id'] for x in barriers if conservative.buffer(.12).intersects(x['geometry']) or any(ray.intersects(x['geometry']) for ray in rays)]
      water_hits=[x['way_id'] for x in waters if p.buffer(.35).intersects(x['geometry']) or conservative.buffer(.12).intersects(x['geometry'])]
      envelope_gap=p.distance(envelope);target_gap=p.distance(target)
      clear=not body_hits and not boom_hits and not any(ray_hits) and not barrier_hits and not water_hits and envelope_gap>1 and target_gap>1
      fromcenter=math.degrees(math.atan2(px,py))%360;bearing=math.degrees(math.atan2(direction[0],direction[1]))%360
      angle_delta=abs((fromcenter-a.preferred_bearing_from_center+180)%360-180)
      min_neighbor=min([conservative.distance(n['geometry']) for n in neighbors],default=None)
      score=angle_delta*.10+abs(length-25)*.25-(min(min_neighbor,5) if min_neighbor is not None else 0)
      rows.append({'id':f'observation-{number}','basis':basis,'position_enu_m':[px,py],'walkStart':geographic(px,py),'bearing':bearing,'distance_to_anchor_m':length,'source_boundary_distance_m':target_gap,'estimated_model_envelope_distance_m':envelope_gap,'nominal_camera_eye_enu_m':list(eye),'nominal_camera_to_enu_m':list(ahead),'body_radius_hits':body_hits,'conservative_boom_radius_hits':boom_hits,'source_corner_ray_neighbor_hits':ray_hits,'mapped_barrier_hits':barrier_hits,'mapped_water_hits':water_hits,'minimum_conservative_boom_to_neighbor_m':min_neighbor,'finite_2d_clear':clear,'ranking_score':score})
    rows.sort(key=lambda r:(not r['finite_2d_clear'],r['ranking_score']))
    report={'schema':'v10-finite-exterior-observation-candidates-v1','id':a.id,'geometry_input':desc(inp),'osm_context':desc(a.context),'source_feature_tables':sources,'scanned_source_features':all_count,'nearby_other_source_features_120m':len(neighbors),'source_projection':'R6378137 WebMercator differences times cos(anchor latitude), identical frozen source convention.','model_envelope':{'estimated':True,'shape':'axis-aligned conservative square in source ENU','half_width_m':a.envelope_half_width,'not_actual_raw_geometry':True},'camera_convention':{'distance_m':14,'pitch_degrees':82,'ahead_m':2.8,'boom_radius_m':.12,'body_radius_m':.35,'conservative_rear_arm_m':14,'controller':desc(a.project/'src/walk-controller.js')},'mapped_surface_paths':len(paths),'mapped_barriers':len(barriers),'mapped_water_polygons':len(waters),'candidate_count':len(rows),'clear_candidates':sum(r['finite_2d_clear'] for r in rows),'candidates':rows,'navigation_installable':False,'model_or_browser_accepted':False,'limitations':['Finite 2D source-envelope checks only; no actual model GLB or browser image was examined.','OSM highway/barrier/area mapping is incomplete and is not a public-access, physical ground, stair, vegetation or entrance certification.','Mapped layer=-1 paths are not treated as ground-level walking positions.','The original source owner boundary is not proof of architectural wall or eave dimensions.','Tower full height may be cropped by the default walking camera; overview and actual browser composition remain pending.']}
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'report':desc(a.output),'candidates':len(rows),'clear':report['clear_candidates'],'preferred':rows[0] if rows else None},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
