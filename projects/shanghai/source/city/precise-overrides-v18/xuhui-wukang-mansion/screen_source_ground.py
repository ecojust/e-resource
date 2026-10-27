#!/usr/bin/env python3
"""Bounded preliminary exterior-navigation review. No final acceptance or install."""
import hashlib, importlib.util, json, math, sys, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent; BASE=HERE.parent; MAIN=Path('/workspace/shanghai_project')

def desc(path):
    path=Path(path).resolve();data=path.read_bytes()
    return {'path':str(path),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
def read(path): return json.loads(Path(path).read_text())
def save(path,data):
    with Path(path).open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def main():
    for n in ['navigation-proposal.json','candidate-screen.json','source-ground-review.json','context.png']:
        assert not (HERE/n).exists(), 'Retain existing evidence '+n
    frozen=BASE/'freeze-v1/xuhui-wukang-mansion/geometry-input.json';g=read(frozen)
    neighborhood_path=BASE/'source-neighborhood-v1.json';neighbors=read(neighborhood_path)
    owner=shape(g['model_geometry_local_east_north_m'])
    lon0,lat0=g['anchor'];R=6378137.;c=math.cos(math.radians(lat0));merc0=math.asinh(math.tan(math.radians(lat0)))
    def project(lon,lat,z=None):return (R*math.radians(lon-lon0)*c,R*(math.asinh(math.tan(math.radians(lat)))-merc0)*c)
    def geographic(xy):return [lon0+math.degrees(xy[0]/(R*c)),math.degrees(math.atan(math.sinh(merc0+xy[1]/(R*c))))]
    draft=BASE.parents[1]/'model/wukang-mansion/spatial-v1/wukang-mansion-spatial.glb'
    decoder_path=BASE/'owner-tools-v1/screen_draft_neighborhood.py'
    spec=importlib.util.spec_from_file_location('draft_screen',decoder_path);decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    parts,doc=decoder.raw_triangles(draft);projection,projections,counts=decoder.projected_parts(parts)
    triangle_count=sum(len(p['triangles']) for p in parts)
    context=HERE/'osm-navigation-context.osm';receipt=read(HERE/'fetch.json')
    assert receipt['status']==200 and desc(context)['sha256']==receipt['sha256']
    xml=ET.parse(context).getroot();node_elements=xml.findall('node')
    nodes={n.attrib['id']:project(float(n.attrib['lon']),float(n.attrib['lat'])) for n in node_elements}
    ways=[];incomplete=[];invalid=[]
    for w in xml.findall('way'):
        tags={t.attrib['k']:t.attrib['v'] for t in w.findall('tag')};refs=[n.attrib['ref'] for n in w.findall('nd')]
        if not refs or any(r not in nodes for r in refs):incomplete.append(w.attrib['id']);continue
        xy=[nodes[r] for r in refs]
        geometry=Polygon(xy) if len(xy)>3 and refs[0]==refs[-1] else LineString(xy) if len(xy)>1 else Point(xy[0])
        if not geometry.is_valid:invalid.append(w.attrib['id']);continue
        ways.append({'id':w.attrib['id'],'version':w.attrib.get('version'),'tags':tags,'geometry':geometry})
    water=lambda tags: tags.get('natural')=='water' or 'waterway' in tags or 'water' in tags or tags.get('landuse') in ('reservoir','basin') or tags.get('leisure')=='swimming_pool' or tags.get('amenity')=='fountain'
    waters=[w for w in ways if water(w['tags'])];water_relations=[]
    for rel in xml.findall('relation'):
        tags={t.attrib['k']:t.attrib['v'] for t in rel.findall('tag')}
        if water(tags):water_relations.append({'id':rel.attrib['id'],'tags':tags,'requires_member_geometry_review':True})
    buildings=[w for w in ways if 'building' in w['tags'] or 'building:part' in w['tags']]
    roads=[w for w in ways if w['tags'].get('highway') not in (None,'footway','path','pedestrian','steps','cycleway')]
    highway=[w for w in ways if 'highway' in w['tags']]
    source_neighbors=[(r,shape(r['geometry_local_east_north_m'])) for r in neighbors['features']]
    def probes_for(start,bearing):
        rad=math.radians(bearing);u=(math.sin(rad),math.cos(rad));at=lambda d:[start[i]+u[i]*d for i in (0,1)]
        end=at(5);target=at(2.8);eye=at(2.8-math.sin(math.radians(82))*14)
        probes={'avatar':(Point(start),.38),'forward_5m':(LineString([start,end]),.38),'camera':(Point(eye),.12),'camera_boom':(LineString([target,eye]),.12)}
        controller={'pitch_degrees':82,'camera_distance_m':14,'ahead_m':2.8,'target_ground_projection_local_enu_m':target,'camera_ground_projection_local_enu_m':eye,'target_altitude_above_ground_m':3,'camera_altitude_above_ground_m':3+math.cos(math.radians(82))*14,'ground_fallback_m':.075}
        return probes,controller,end
    candidates=[]
    for name,start,bearing in [('sw-tip-wukang-side',[-28.5,-26],25),('wukang-side-further-north',[-27.5,-24],25),('sw-tip-west-offset',[-28,-24],25)]:
        probes,controller,end=probes_for(start,bearing);checks={}
        for name_,(p,radius) in probes.items():
            nearest=sorted([{'key':row['key'],'local_id':row['local_id'],'clearance_m':geom.distance(p)-radius} for row,geom in source_neighbors],key=lambda v:v['clearance_m'])
            checks[name_]={'radius_m':radius,'source_owner_clearance_m':owner.distance(p)-radius,'actual_draft_projection_clearance_m':projection.distance(p)-radius,'neighbor_intersections':[r for r in nearest if r['clearance_m']<=0],'nearest_neighbors':nearest[:3]}
        candidates.append({'id':name,'spawn_local_enu_m':start,'walkStart':geographic(start),'bearing':bearing,'first_5m_endpoint_local_enu_m':end,'controller_default':controller,'checks':checks,'preliminary_geometry_passed':all(v['source_owner_clearance_m']>0 and v['actual_draft_projection_clearance_m']>0 and not v['neighbor_intersections'] for v in checks.values()),'precise_public_sidewalk_membership_verified':False})
    selected=candidates[0];probes,controller,end=probes_for(selected['spawn_local_enu_m'],selected['bearing'])
    limitations=['This is an unaccepted outdoor navigation candidate checked against a spatial preview; final detailed raw geometry, final navigation/camera tests and actual browser movement remain pending.',
       'OSM only maps road centerlines here. It contains no sidewalk polygon or explicit footway at the candidate; line clearance is not carriageway-edge or curb clearance.',
       '2022 photographs support a narrow paved strip around the southwest rounded tip, not an open forecourt. They are not georegistered to this coordinate and do not prove current clear width.',
       'The candidate is along the Wukang Road side away from the intersection, with finite first 5 m tangent movement. Its exact curb-side membership and traffic separation remain unverified.',
       'Signal posts are visible in photographs but lack reliable local coordinates; no full furniture, tree-pit or pedestrian obstacle inventory is claimed.',
       'The default camera extends in air toward the intersection. Its projection is checked for mapped buildings, not road-surface pedestrian support or a surveyed overhead-wire inventory.',
       'Online building/building_part/water polygons provide runtime collision. An ordinary detailed GLB does not automatically register accurate interior, arcade-column, wall, curb, stair or local ground collisions.',
       'The runtime 0.075 m fallback ground elevation is not a surveyed curb/pavement height. No accessible interior or free navigation through arcades is claimed.',
       'No water tags in this bounded response means no mapped water was found, not physical proof of absence.']
    proposal={'schema':'wukang-mansion-v18-preliminary-exterior-navigation-v1','building_id':g['id'],'status':'PRELIMINARY_NOT_ACCEPTED','navigation':{'listed':True,'overviewZoom':18,'walkStart':selected['walkStart'],'bearing':selected['bearing']},'candidate_id':selected['id'],'spawn_local_enu_m':selected['spawn_local_enu_m'],'controller_default':controller,'final_model_accepted':False,'browser_passed':False,'precise_public_sidewalk_membership_verified':False,'coordinate_contract':desc(frozen),'draft_model':desc(draft),'limitations':limitations}
    save(HERE/'navigation-proposal.json',proposal)
    screen={'schema':'wukang-mansion-v18-actual-spatial-preview-navigation-screen','accepted':False,'final_model_accepted':False,'browser_passed':False,'tool':desc(__file__),'raw_decoder':desc(decoder_path),'actual_draft_model':desc(draft),'actual_draft_triangles':triangle_count,'projection_triangle_types':counts,'coordinate_contract':desc(frozen),'effective_neighborhood':desc(neighborhood_path),'effective_neighbors_checked':len(source_neighbors),'candidate_binding':desc(HERE/'navigation-proposal.json'),'candidates':candidates,'limitations':limitations}
    save(HERE/'candidate-screen.json',screen)
    building_checks={}
    for name,(p,radius) in probes.items():
        near=sorted([{'osm_way':w['id'],'version':w['version'],'name':w['tags'].get('name'),'clearance_m':w['geometry'].distance(p)-radius} for w in buildings],key=lambda x:x['clearance_m'])
        building_checks[name]={'nearest':near[:3],'intersections':[x for x in near if x['clearance_m']<=0]}
    water_checks=[{'osm_way':w['id'],'version':w['version'],'tags':w['tags'],'geometry_type':w['geometry'].geom_type,'probe_clearance_m':{name:w['geometry'].distance(p)-r for name,(p,r) in probes.items()}} for w in waters]
    start=Point(selected['spawn_local_enu_m']);forward=probes['forward_5m'][0]
    highways=sorted([{'osm_way':w['id'],'version':w['version'],'tags':w['tags'],'distance_to_start_centerline_m':w['geometry'].distance(start),'distance_to_first5m_centerline_m':w['geometry'].distance(forward),'distance_is_not_curb_or_lane_edge':True} for w in highway],key=lambda x:x['distance_to_start_centerline_m'])
    tagged_nodes=[]
    for n in node_elements:
        tags={t.attrib['k']:t.attrib['v'] for t in n.findall('tag')}
        if tags and Point(nodes[n.attrib['id']]).distance(start)<40:
            tagged_nodes.append({'osm_node':n.attrib['id'],'tags':tags,'local_east_north_m':nodes[n.attrib['id']],'distance_to_start_m':Point(nodes[n.attrib['id']]).distance(start)})
    bounds=xml.find('bounds').attrib
    bbox=Polygon([project(float(bounds['minlon']),float(bounds['minlat'])),project(float(bounds['maxlon']),float(bounds['minlat'])),project(float(bounds['maxlon']),float(bounds['maxlat'])),project(float(bounds['minlon']),float(bounds['maxlat']))])
    in_bounds=all(bbox.covers(p.buffer(r)) for p,r in probes.values())
    source_pass=not(incomplete or invalid or water_relations) and in_bounds and all(not v['intersections'] for v in building_checks.values()) and all(min(x['probe_clearance_m'].values())>0 for x in water_checks)
    report={'schema':'wukang-mansion-v18-bounded-source-ground-review','passed_source_screen_only':source_pass,'scope_of_pass':'Only complete bounded mapped building/water context and finite probe nonintersection; not precise sidewalk, traffic, final mesh or browser acceptance.',
      'final_model_accepted':False,'browser_passed':False,'main_written':False,'precise_public_sidewalk_membership_verified':False,'current_clear_pedestrian_width_verified':False,
      'candidate_binding':desc(HERE/'navigation-proposal.json'),'candidate_id':selected['id'],'candidate_navigation':{k:proposal['navigation'][k] for k in ('walkStart','bearing')},'coordinate_contract':desc(frozen),'effective_neighborhood':desc(neighborhood_path),'osm_input':desc(context),'fetch':receipt,'osm_counts':{k:len(xml.findall(k)) for k in ('node','way','relation')},'query_bbox':bounds,'all_probe_buffers_inside_requested_bbox':in_bounds,'incomplete_way_node_refs':incomplete,'invalid_way_geometries':invalid,'mapped_water_or_fountain_ways':water_checks,'water_relations_pending':water_relations,'live_osm_building_checks':building_checks,'nearest_highways':highways[:9],'nearest_explicit_footway':next((r for r in highways if r['tags'].get('highway')=='footway'),None),'tagged_nodes_within40m':tagged_nodes,
      'source_land_at_start':[{'osm_way':w['id'],'tags':w['tags']} for w in ways if w['geometry'].geom_type=='Polygon' and any(k in w['tags'] for k in ('landuse','surface','leisure','area:highway')) and w['geometry'].covers(start)],
      'visual_ground_review':desc(HERE/'visual-ground-notes.json'),'runtime_source_inputs':[desc(MAIN/p) for p in ('src/map-scene.js','src/street-interaction.js','src/walk-controller.js')],'runtime_scope_review':desc(BASE/'runtime-collision-scope-v1.json'),'tool':desc(__file__),'limitations':limitations}
    save(HERE/'source-ground-review.json',report)
    import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,8))
    for row,geom in source_neighbors:
        if geom.distance(start)>75:continue
        polys=[geom] if geom.geom_type=='Polygon' else list(geom.geoms)
        for poly in polys:
            if poly.geom_type=='Polygon':x,y=poly.exterior.xy;ax.fill(x,y,color='#d3d8da',edgecolor='#8a959b',lw=.6)
    x,y=owner.exterior.xy;ax.fill(x,y,color='#d6bd94',edgecolor='#775b39',lw=1.3,label='Frozen building footprint')
    for w in highway:
        if w['geometry'].distance(start)>85:continue
        if w['geometry'].geom_type not in ('LineString','Polygon'):continue
        xy=list(w['geometry'].exterior.coords if w['geometry'].geom_type=='Polygon' else w['geometry'].coords)
        isfoot=w['tags'].get('highway') in ('footway','path','pedestrian')
        ax.plot(*zip(*xy),color='#598b67' if isfoot else '#bd6f65',ls='-' if isfoot else '--',lw=1.5)
    sx,sy=selected['spawn_local_enu_m'];tx,ty=end;ex,ey=controller['camera_ground_projection_local_enu_m'];cx,cy=controller['target_ground_projection_local_enu_m']
    ax.scatter([sx],[sy],color='#183c79',s=45,zorder=10,label='Provisional player start')
    ax.annotate('',xy=(tx,ty),xytext=(sx,sy),arrowprops={'arrowstyle':'->','color':'#183c79','lw':2.5})
    ax.plot([ex,cx],[ey,cy],color='#6f49a1',lw=2,label='Default airborne camera boom')
    ax.scatter([ex],[ey],marker='x',color='#6f49a1',s=50)
    ax.text(-18,-40,'Huaihai Road centerline',fontsize=8,rotation=35,color='#99554c')
    ax.text(-46,-12,'Wukang Road\ncenterline',fontsize=8,color='#99554c')
    ax.text(15,-29,'Mapped footway\nacross road',fontsize=8,color='#3a6948')
    ax.set_xlim(-70,65);ax.set_ylim(-65,55);ax.set_aspect('equal');ax.grid(alpha=.2)
    ax.set_xlabel('East from frozen anchor (m)');ax.set_ylabel('North from frozen anchor (m)')
    ax.set_title('Preliminary only: southwest-tip exterior candidate\nDashed road lines do NOT show lane edges or sidewalks',fontsize=11)
    ax.legend(loc='upper left',fontsize=8);fig.tight_layout();fig.savefig(HERE/'context.png',dpi=120);plt.close(fig)
    print(json.dumps({'source_screen_only':source_pass,'draft_screen_only':selected['preliminary_geometry_passed'],'candidate':proposal['navigation'],'draft_min_clearances_m':{k:v['actual_draft_projection_clearance_m'] for k,v in selected['checks'].items()},'effective_neighbors':len(source_neighbors),'osm_counts':report['osm_counts'],'footway_distance_m':report['nearest_explicit_footway']['distance_to_start_centerline_m'],'source_report':desc(HERE/'source-ground-review.json'),'candidate_report':desc(HERE/'candidate-screen.json')},ensure_ascii=False))
if __name__=='__main__':main()
