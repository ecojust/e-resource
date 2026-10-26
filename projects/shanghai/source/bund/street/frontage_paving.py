"""v4.5 bounded western frontage paving, on the existing road/sidewalk datum.

This module adds only missing surface between verified source facade edges and
existing arterial road edges. Plan envelope is a reconstruction bounded by two
sources, not a surveyed sidewalk polygon. It never fills inter-building blocks.
"""
import hashlib
import json
import math
from pathlib import Path
from shapely.geometry import LineString, Point, Polygon, mapping
from shapely.geometry.polygon import orient
from shapely.ops import unary_union
from connector_paving import shortest_outer_chain

MATERIAL = 'BundFrontagePaving'
TOP_M = .075
BASE_M = .003
MAX_ENVELOPE_WIDTH_M = 24
# Only actual east-facing edges of the verified front facade, in source order.
EDGE_SELECTION = {
    'bund02':[0], 'bund03':[0], 'bund12':[0], 'bund13':[0,1,2],
    'bund15':[0], 'bund17':[0], 'bund18':[0], 'bund19':[0],
    'bund20':[0,1], 'bund23':[0],
}

def assemble_frontage(ns):
    metric, geographic = ns['metric'], ns['geographic']
    roots = Path(ns['ROOT'])
    existing = unary_union([ns['promenade'], ns['walk_surface'],
        ns['pedestrian_paving'],ns['connector'],ns['roads']['shoulder']])
    holes = unary_union([Polygon(ring) for poly in ns['polygons'](ns['pedestrian_footprint']) for ring in poly.interiors])
    source = json.loads((roots/'bund18-connector-source.json').read_text())
    relation = next(e for e in source['elements'] if e['type']=='relation' and e['id']==2142077)
    original_holes = [metric(Polygon([(p['lon'],p['lat']) for p in m['geometry']]))
        for m in relation['members'] if m.get('role')=='inner' and m.get('geometry')]
    holes = unary_union([holes,*original_holes])
    beds = unary_union([p['footprint'] for p in ns['planting'].values()])
    exclusions = {'existing_paving':existing, 'road_surface':ns['roads']['surface'],
        'road_curb':ns['roads']['curb'], 'candidate_footprints':ns['buildings'],
        'water':ns['water'], 'source_pedestrian_holes':holes, 'retained_planting_beds':beds}
    records=[];features=[];patches=[];envelopes=[]
    candidates = {c['id']:c for c in ns['source_candidates']}
    for building,indices in EDGE_SELECTION.items():
        for index in indices:
            source_edge=candidates[building]['streetfront']['candidate_edges'][index]
            assert source_edge['road_distance_m']<30
            edge=metric(LineString(source_edge['endpoints_wgs84']))
            ends=[Point(c) for c in edge.coords]
            road_edge=shortest_outer_chain(ns['roads']['surface'],ends)
            envelope=Polygon(list(edge.coords)+list(road_edge.coords)[::-1])
            assert envelope.is_valid, (building,index,'invalid bounded envelope')
            assert road_edge.length<edge.length+30,(building,index,'road edge wrapped a side street')
            max_width=max(Point(c).distance(edge) for c in road_edge.coords)
            assert max_width<MAX_ENVELOPE_WIDTH_M,(building,index,max_width)
            patch=envelope.intersection(ns['crop'])
            for excluded in exclusions.values():patch=patch.difference(excluded)
            if patches:patch=patch.difference(unary_union(patches))
            patch=unary_union([orient(p,sign=1) for p in ns['polygons'](patch) if p.area>1e-6])
            overlaps={name:patch.intersection(g).area for name,g in exclusions.items()}
            outside=patch.difference(envelope).area
            assert max([outside,*overlaps.values()])<1e-6
            record={'id':f'{building}-frontage-{index}','building':building,
                'facade_edge_index':index,'facade_endpoints_wgs84':source_edge['endpoints_wgs84'],
                'envelope_area_m2':envelope.area,'new_paving_area_m2':patch.area,
                'maximum_distance_to_facade_m':max_width,'outside_envelope_m2':outside,
                'overlap_m2':overlaps,'top_height_world_m':TOP_M,'base_height_world_m':BASE_M,
                'classification':'source-bounded estimated public sidewalk infill',
                'surface_observation':'Continuous grey paving between the street facade and curb visible in 2010 located aerial; 2025 frontage photos corroborate stone paving and curb.',
                'height_basis':'Join existing modeled west sidewalk at 0.075m; estimated construction datum, not surveyed elevation.'}
            records.append(record);patches.append(patch);envelopes.append(envelope)
            for role,g in [('source_facade',edge),('existing_road_edge',road_edge),('bounded_envelope',envelope),('new_frontage_paving',patch)]:
                features.append({'type':'Feature','properties':{'role':role,'id':record['id'],'building':building,'height_world_m':TOP_M},'geometry':mapping(geographic(g))})
    geometry=unary_union(patches)
    audit={'version':'bund-frontage-v4.5','passed':True,'source_candidates':'../bund-candidates.json',
        'source_candidates_sha256':hashlib.sha256((roots.parent/'bund-candidates.json').read_bytes()).hexdigest(),
        'existing_street_baseline_raw_sha256':'ec298f3be5f8a819cc6aaf1350745d83e3be1a523d42cb794bda72d2931ed931',
        'official_reference':{'url':'https://ghzyj.sh.gov.cn/ghgs/20191231/0032-174998.html','title':'外滩滨水区城市设计','date':'2008-05-27','observed_text':'适当加宽西侧人行道，增加沿历史建筑的公共活动和观景空间。','role':'planned function only; extents checked against located 2010 aerial'},
        'photo_reference':'references/bund17-18-19-aerial-2010-original.jpg (Gary Lee Todd, CC0-1.0), unchanged original and metadata in planting-evidence.json',
        'recent_photos':'street-reference-evidence.json (2025 CC0 frontage images)',
        'edge_selection':EDGE_SELECTION,'new_surface_area_m2':geometry.area,'parts':records,
        'two_v4_3_planting_beds_unchanged':True,'original_material_geometry_unchanged':True,
        'inter_building_gaps_filled':False,'unknown_holes_filled':False,
        'platform_elevation_claimed':False,'construction_dimensions_estimated':True,
        'limits':['Envelopes interpolate between verified facade edges and existing estimated carriageway edges, not surveyed curb polygons.',
            'Widths depend on existing OSM centerline and lane-based road reconstruction.',
            'No newly inferred building forecourt, internal courtyard, raised platform or underground stair is filled.',
            'The 2008 design is corroborating design intent, not an as-built survey.']}
    return geometry,audit,{'type':'FeatureCollection','features':features}

def add_frontage_paving(ns):
    geometry,audit,geojson=assemble_frontage(ns)
    ns['COLORS'][MATERIAL]=(.34,.355,.36,1)
    ns['M'][MATERIAL]=ns['Mesh']()
    render_geometry=geometry.simplify(.0001,preserve_topology=True)
    audit['render_precision']={'simplification_tolerance_m':.0001,'hausdorff_distance_m':geometry.hausdorff_distance(render_geometry),'symmetric_difference_m2':geometry.symmetric_difference(render_geometry).area,'reason':'Remove sub-0.1mm near-collinear vertices before float32 triangulation; prevents microscopic triangle inversion. Original street geometry is untouched.'}
    for poly in ns['polygons'](render_geometry):ns['solid'](MATERIAL,orient(poly,sign=1),BASE_M,TOP_M)
    root=Path(ns['ROOT'])
    (root/'bund-streets-frontage-check.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    (root/'bund-streets-frontage-check.geojson').write_text(json.dumps(geojson,ensure_ascii=False,separators=(',',':'))+'\n')
    return render_geometry,audit
