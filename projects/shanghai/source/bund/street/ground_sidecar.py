"""Export local street ground and physical fittings for owner-scoped interaction.

Call after geometry is assembled/exported. No terrain is inferred in unknown
areas. In runtime this data is active only while the exact owner mesh is loaded
and visible. All Y values are world metres above the street asset datum.
"""
import hashlib,json,math
from pathlib import Path
import numpy as np
from shapely.geometry import Point,LineString,Polygon,box,mapping
from shapely.ops import unary_union

def export_ground_sidecar(ns, output, raw_path, web_path=None, extra_features=()):
    geographic=ns['geographic'];features=[]
    def feature(ident,geometry,role,base,top,blocks_walk,blocks_camera,**kwargs):
        if geometry.is_empty:return
        if role=='walk-surface':
            parts=ns['polygons'](geometry)
            if not parts:return
            geometry=unary_union(parts)
        props={'id':ident,'role':role,'base_world_m':float(base),'top_world_m':float(top),
               'blocks_walk':bool(blocks_walk),'blocks_camera':bool(blocks_camera),**kwargs}
        if role=='walk-surface':props['height_world_m']=float(top)
        features.append({'type':'Feature','properties':props,'geometry':mapping(geographic(geometry))})
    # The frozen relation contains exact source openings; retain them as
    # unavailable ground even where the older path-derived slab is coarse.
    frozen=json.loads((Path(ns['ROOT'])/'bund18-connector-source.json').read_text())
    relation=next(e for e in frozen['elements'] if e['type']=='relation' and e['id']==2142077)
    holes=[]
    for member in relation['members']:
        if member.get('role')=='inner' and member.get('geometry'):
            h=ns['metric'](Polygon([(p['lon'],p['lat']) for p in member['geometry']])).intersection(ns['crop'])
            if h.is_empty:continue
            holes.append(h)
            feature(f'protected-opening-{member["ref"]}',h,'obstacle',-1,2,True,False,
                kind='unmodeled-opening',source=f'OSM relation 2142077 inner way {member["ref"]}',
                evidence_class='mapped footprint; physical type/height unresolved',
                vertical_interval_is='runtime walking exclusion only, not an asserted wall or surveyed elevation')
    protected=unary_union(holes)
    beds=unary_union([p['footprint'] for p in ns['planting'].values()])
    for ident,g,base,top,source in [
        ('asphalt',ns['roads']['surface'],.002,.020,'osm-roads.json; lane-width estimates'),
        ('river-paving',ns['promenade'],.005,.035,'OSM inner footway + verified merged shoreline'),
        ('mapped-pedestrian-paving',ns['pedestrian_paving'],.005,.035,'OpenFreeMap feature 21420773'),
        ('mapped-west-footway',ns['walk_surface'],.003,.075,'OSM way 178412507; 4m estimated width'),
        ('road-shoulder-paving',ns['roads']['shoulder'].difference(ns['water']),.003,.075,'OSM road buffers; estimated shoulder'),
        ('bounded-connector',ns['connector'],.005,.035,'bund-streets-connector-check.json'),
        ('bounded-west-frontages',ns.get('frontage',Polygon()),.003,.075,'bund-streets-frontage-check.json'),
        ('road-curb',ns['roads']['curb'],.006,.140,'road_geometry.py estimated source road edge'),
        ('yellow-curb',ns['roads']['yellow_curb'],.012,.143,'photo-supported yellow curb; estimated road edge'),
        ('gutter',ns['roads']['gutter'],.020,.023,'photo-supported drainage; estimated road edge'),
        ('white-road-paint',ns['roads']['lane_paint'].union(ns['roads']['zebras']),.025,.029,'OSM crossing axes and estimated paint dimensions'),
        ('yellow-road-paint',ns['roads']['median_paint'],.025,.029,'OSM arterial centerline; estimated paint convention')]:
        feature(ident,g.difference(protected).difference(beds),'walk-surface',base,top,False,False,
                evidence_class='source-derived plan; estimated construction height',source=source)
    for ident,bed in ns['planting'].items():
        feature(ident,bed['footprint'],'obstacle',.005,.215,True,True,
                kind='planting-bed',source='planting-evidence.json; unchanged v4.3 footprint',
                evidence_class='photo-classified OSM recess; estimated shallow stone border',
                height_is='maximum modeled stone border; no platform elevation asserted')
    # Furniture uses the exact sibling furniture.interaction() primitive data.
    # Do not duplicate it with approximate envelopes in this ground sidecar.
    features.extend(extra_features)
    raw=Path(raw_path);web=Path(web_path) if web_path else None
    result={'type':'FeatureCollection','schema_version':1,'owner':'bund-streets',
       'origin':list(ns['ORIGIN']),'coordinate_system':'WGS84 geometry; world Y in metres, asset origin at ground datum 0',
       'raw_model_sha256':hashlib.sha256(raw.read_bytes()).hexdigest(),
       'web_model_sha256':hashlib.sha256(web.read_bytes()).hexdigest() if web else None,
       'activation':'Exact asset owner must be loaded and visible; verify configured owner model SHA. Unknown space returns null.',
       'height_status':'Construction heights are model estimates; no absolute Shanghai floodwall/road elevation is asserted.',
       'protected_openings':'Exact frozen inner rings are walk-only exclusion zones, not invented walls. Two 2010 photo-classified exterior recesses remain planting beds.',
       'features':features}
    Path(output).write_text(json.dumps(result,ensure_ascii=False,separators=(',',':'))+'\n')
    return result
