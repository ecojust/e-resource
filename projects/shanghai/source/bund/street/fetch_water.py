"""Fetch the four Bund tiles and merge water before extracting a shoreline.

A vector-tile polygon boundary contains artificial tile-clipping edges. Union
removes internal seams; the four-tile outer boundary lies outside the Bund crop.
"""
from urllib.request import urlopen, Request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib, json, math
import mapbox_vector_tile
from shapely.geometry import shape, mapping
from shapely import make_valid
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parent
TILES=[(14,x,y) for x in (13720,13721) for y in (6693,6694)]
CROP=[121.4842,31.23545,121.4892,31.2419]

def fetch(url):
    request=Request(url,headers={'User-Agent':'ShanghaiExplorer/3.0 public map study'})
    with urlopen(request,timeout=40) as response:return response.read()

def latitude(y,n):return math.degrees(math.atan(math.sinh(math.pi*(1-2*y/n))))

def tile_bounds(z,x,y):
    n=2**z
    return [x/n*360-180,latitude(y+1,n),(x+1)/n*360-180,latitude(y,n)]

def decode_tile(item):
    tile,url,raw=item;z,x,y=tile;n=2**z;decoded=mapbox_vector_tile.decode(raw);features=[]
    for layer in ['water','transportation','landcover','landuse']:
        data=decoded.get(layer,{});extent=data.get('extent',4096)
        def project(coords):
            if isinstance(coords[0],(int,float)):
                px,py=coords[:2]
                return [(x+px/extent)/n*360-180,latitude(y+1-py/extent,n)]
            return [project(child) for child in coords]
        for feature in data.get('features',[]):
            features.append({'type':'Feature','id':feature.get('id'),
                'properties':{'layer':layer,**feature.get('properties',{}),'source_tile':list(tile)},
                'geometry':{'type':feature['geometry']['type'],'coordinates':project(feature['geometry']['coordinates'])}})
    return features

def main():
    tilejson=json.loads(fetch('https://tiles.openfreemap.org/planet'))
    template=tilejson['tiles'][0]
    requests=[(tile,template.replace('{z}',str(tile[0])).replace('{x}',str(tile[1])).replace('{y}',str(tile[2]))) for tile in TILES]
    with ThreadPoolExecutor(max_workers=4) as pool:
        raw_tiles=list(pool.map(lambda item:(item[0],item[1],fetch(item[1])),requests))
    features=[feature for item in raw_tiles for feature in decode_tile(item)]
    water=[make_valid(shape(feature['geometry'])) for feature in features
        if feature['properties']['layer']=='water' and feature['geometry']['type'] in ['Polygon','MultiPolygon']]
    merged_water=unary_union(water)
    assert not merged_water.is_empty and merged_water.is_valid
    output=[feature for feature in features if feature['properties']['layer']!='water']
    output.append({'type':'Feature','id':'four-tile-water-union',
        'properties':{'layer':'water','merged':True,'source_tiles':[list(tile) for tile in TILES]},
        'geometry':mapping(merged_water)})
    records=[]
    for tile,url,raw in raw_tiles:
        name='bund-map.'+'.'.join(map(str,tile))+'.pbf';(ROOT/name).write_bytes(raw)
        records.append({'tile':list(tile),'url':url,'file':name,'bounds':tile_bounds(*tile),
            'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
    coverage=[min(r['bounds'][0] for r in records),min(r['bounds'][1] for r in records),
        max(r['bounds'][2] for r in records),max(r['bounds'][3] for r in records)]
    assert coverage[0]<CROP[0]<CROP[2]<coverage[2] and coverage[1]<CROP[1]<CROP[3]<coverage[3]
    source={'version':2,'tilejson':tilejson,'tiles':records,'coverage_bounds':coverage,'bund_crop':CROP,
        'water_merge':'Polygon union before shoreline extraction; internal tile-cut edges disappear.',
        'license':'ODbL-1.0','attribution':'© OpenStreetMap contributors; OpenFreeMap / OpenMapTiles'}
    (ROOT/'tile-source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2))
    (ROOT/'bund-map.geojson').write_text(json.dumps({'type':'FeatureCollection','features':output},ensure_ascii=False,separators=(',',':')))
    (ROOT/'bund-map.pbf').unlink(missing_ok=True)
    print(json.dumps({'tiles':len(records),'source_water_polygons':len(water),'water_geometry':merged_water.geom_type,
        'tile_bytes':sum(r['bytes'] for r in records),'coverage':coverage},ensure_ascii=False))

if __name__=='__main__':main()
