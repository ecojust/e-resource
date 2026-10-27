"""Read-only metrics and proxy helpers adapted from scoped V13 acceptance."""
import hashlib, math, os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, unquote

def need(value,message):
    if not value: raise AssertionError(message)

def utc(): return datetime.now(timezone.utc).isoformat()

def descriptor(path):
    b=Path(path).read_bytes()
    return {'file':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}

def metres(a,b):
    return math.hypot(math.radians(a['lng']-b['lng'])*6378137*math.cos(math.radians(b['lat'])),
                      math.radians(a['lat']-b['lat'])*6378137)

def offset(record,east,north,alt):
    return {'lng':record['lng']+math.degrees(east/(6378137*math.cos(math.radians(record['lat'])))),
            'lat':record['lat']+math.degrees(north/6378137),'alt':alt}

def proxy_options():
    name=next((n for n in ('HTTPS_PROXY','HTTP_PROXY') if os.environ.get(n)),None)
    need(name,'--use-env-proxy requires HTTPS_PROXY or HTTP_PROXY')
    value=urlsplit(os.environ[name]);need(value.scheme in ('http','https') and value.hostname,'Unsupported proxy URL')
    host=('['+value.hostname+']') if ':' in value.hostname else value.hostname
    config={'server':value.scheme+'://'+host+((':'+str(value.port)) if value.port else ''),'bypass':'localhost,127.0.0.1'}
    if value.username is not None:config['username']=unquote(value.username)
    if value.password is not None:config['password']=unquote(value.password)
    return config,{'enabled':True,'source_environment':name,'bypass':config['bypass'],
                   'credentials_supplied':value.username is not None or value.password is not None,
                   'scope':'Transport only; no URLs or response bytes rewritten.'}

def source_check(value,record):
    """Independent metric geometry comparison; MVT quantization is not surveying."""
    from shapely.geometry import shape
    from shapely.ops import transform
    lat0=record['lat'];lon0=record['lng'];scale=6378137*math.cos(math.radians(lat0))
    def project(x,y,z=None):
        # shapely 2 first offers sequences; both forms are supported.
        try:return [(v-lon0)*math.pi/180*scale for v in x],[(v-lat0)*math.pi/180*6378137 for v in y]
        except TypeError:return (x-lon0)*math.pi/180*scale,(y-lat0)*math.pi/180*6378137
    target=transform(project,shape(value['targetBoundary']))
    need(value['readiness']['ready'],'Actual source replacement still pending')
    need(value['sourcePresent'] and value['sourceLoaded'],'Actual building source is not loaded')
    rows=[];seen=set()
    for row in value['components']:
        poly=transform(project,shape(row['geometry']))
        need(poly.is_valid,'Actual source component is invalid')
        key=(str(row['id']),poly.normalize().wkb_hex)
        if key in seen:continue
        seen.add(key)
        intersection=poly.intersection(target).area
        union=poly.union(target).area
        rows.append((intersection/union if union else 0,row,poly))
    rows.sort(key=lambda r:r[0],reverse=True)
    need(rows,'No actual MVT component overlaps the target footprint')
    score,chosen,poly=rows[0]
    result={'passed':False,'mode':value['readiness']['buildingSource'],'source':value['source'],
            'source_layer':value['sourceLayer'],'unique_candidate_components':len(rows),
            'selected_id':chosen['id'],'selected_component_index':chosen['componentIndex'],
            'selected_iou':score,'target_area_m2':target.area,'component_area_m2':poly.area,
            'feature_state':chosen['featureState'],'minimum_iou':.80,
            'scope':'Actual current MVT component compared with frozen owner footprint in local metric coordinates; not a survey, no injected outage, no cross-session source fixture assumption.'}
    need(score>=.80,'Actual source component does not sufficiently match the frozen individual building owner')
    need(chosen['featureState'].get('localModel') is True,'Actual source component is not hidden by local-model ownership')
    if value['readiness']['osm']['active']:
        need(value['residualCurrent'] and value['residualValid'],'Current OSM residual source is unavailable')
        intersections=[transform(project,shape(row['geometry'])).intersection(poly).area for row in value['residualComponents']]
        area=sum(intersections)
        result.update(residual_overlap_m2=area,residual_overlap_limit_m2=.01)
        need(area<=.01,'Target source geometry remains in the current OSM residual')
    else:
        expected=record['owner']['feature_key'].split(':',1)[1]
        result['expected_gers_id']=expected
        need(str(chosen['id'])==expected,'Actual Overture source ID differs from the frozen GERS owner')
    result['passed']=True
    return result

