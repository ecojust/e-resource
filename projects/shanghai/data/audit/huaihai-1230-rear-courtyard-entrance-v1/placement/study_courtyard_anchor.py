"""Estimate the photographed entrance and two camera positions from the rear-block footprint."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import Point, Polygon

BASELINE = '7176c274e6070017be5ae61fd1b9626a7a66f862'
FEATURES_SHA256 = 'd5239bdd08a99fb606ec0e553c91c2801400ee957378b4c05701b72c884b5786'
MACRO_URL = ('https://raw.githubusercontent.com/ecojust/e-resource/'+BASELINE+
             '/projects/shanghai/assets/city-detail/macros/14-13719-6695/feature-table.json.gz')
CONTEXT = {2018:'rear block',2264:'street block',3261:'west neighbour'}
def estimates(table,registration,local_left):
    payload = table.read_bytes()
    assert hashlib.sha256(payload).hexdigest() == FEATURES_SHA256
    records = {r['localId']:r for r in json.loads(gzip.decompress(payload))['features'] if r['localId'] in CONTEXT}
    # Choose the two endpoints of the southern long edge independently of ring order.
    ring = records[2018]['geometry']['coordinates'][0]
    lon_ref = sum(p[0] for p in ring[:-1])/(len(ring)-1)
    lat_ref = sum(p[1] for p in ring[:-1])/(len(ring)-1)
    phi=math.radians(lat_ref)
    lon_unit=111412.84*math.cos(phi)-93.5*math.cos(3*phi)+.118*math.cos(5*phi)
    lat_unit=111132.92-559.82*math.cos(2*phi)+1.175*math.cos(4*phi)-.0023*math.cos(6*phi)
    def en(p):return ((p[0]-lon_ref)*lon_unit,(p[1]-lat_ref)*lat_unit)
    edges=[(a,b) for a,b in zip(ring,ring[1:]) if math.dist(en(a),en(b))>25]
    southwest,southeast=sorted(min(edges,key=lambda pair:pair[0][1]+pair[1][1]))
    start,end=en(southwest),en(southeast)
    length=math.dist(start,end);ux=(end[0]-start[0])/length;uy=(end[1]-start[1])/length
    def local(p):
        x,y=en(p)
        return [(x-start[0])*ux+(y-start[1])*uy+local_left, -(x-start[0])*uy+(y-start[1])*ux]
    def wgs(p):
        x,y=p[0]-local_left,p[1]
        return [round(lon_ref+(start[0]+x*ux-y*uy)/lon_unit,8),round(lat_ref+(start[1]+x*uy+y*ux)/lat_unit,8)]
    features = []
    for k,r in records.items():
        features.append({'id':k,'role':CONTEXT[k],'osm':r['properties']['sources'][0]['record_id'],
                         'polygon_local_m':[[round(v,3) for v in local(xy)] for xy in r['geometry']['coordinates'][0]]})
    camera=json.loads(registration.read_bytes())['cameras']
    points={'door':(0,0),'2013 published view':camera['04']['C'][:2],'2016-01-20 view':camera['25']['C'][:2]}
    positions={}
    for name,p in points.items():
        pos=Point(*p);dist={str(f['id']):round(Polygon(f['polygon_local_m']).distance(pos),2) for f in features}
        positions[name]={'local_xy_m':p,'lon_lat_estimate':wgs(p),'plan_clearance_to_buildings_m':dist}
        if name!='door':assert min(dist.values())>1
    return {'method':'Conditional plan registration using the visible west brick edge in Masa 43034625 and the southwest end of OSM 1199411747. Coordinates are inferred in the local horizontal tangent plane. Photo stations were independently fitted in the entrance coordinate frame.',
            'building_data_url':MACRO_URL,'building_data_sha256':FEATURES_SHA256,'registered_cameras_sha256':hashlib.sha256(registration.read_bytes()).hexdigest(),
            'copyright':'© OpenStreetMap contributors via Overture Maps; ODbL 1.0. Schematic derived from those footprints.',
            'south_facade_bearing_deg':round(math.degrees(math.atan2(ux,uy)),3),'south_edge_m':round(length,2),'west_end_x_m':local_left,
            'photographed_x_extent_m':[local_left,9.93],'whole_building_estimated_height_m_from_city':records[2018]['height'],
            'sources_of_uncertainty':'The single oblique photograph gives 0.40 m spread for the west edge, relative lengths carry the conditional door scale (about seven percent). Geocoder and imagery centroids do not constrain the individual entrance. The 2021 and 2025 imagery metadata give 5 m and 8.47 m horizontal accuracy. Coordinates are unsuitable for a surveyed entrance pin.',
            'positions':positions,'footprints':features}
def plot(study,out):
    im=Image.new('RGB',(680,595),'#f8f8f4');draw=ImageDraw.Draw(im);font_dir=Path('/usr/share/fonts/opentype/noto')
    def font(size,bold=False):
        try:return ImageFont.truetype(str(font_dir/('NotoSansCJK-Bold.ttc' if bold else 'NotoSansCJK-Regular.ttc')),size,index=2)
        except OSError:return ImageFont.load_default(size=size)
    points=[xy for f in study['footprints'] for xy in f['polygon_local_m']]
    left,right=min(p[0] for p in points),max(p[0] for p in points)
    bottom,top=min(p[1] for p in points),max(p[1] for p in points)
    scale=min(810/(right-left),410/(top-bottom));ox=72;oy=90
    def screen(p):return (ox+(p[0]-left)*scale,oy+(top-p[1])*scale)
    draw.text((42,22),'淮海中路1230号内院与两个摄影位置',font=font(26,True),fill='#22272a')
    draw.text((42,60),'彩线为本次建模的院向立面，圆点为门牌所在入口。',font=font(16),fill='#495358')
    for f in study['footprints']:
        poly=[screen(p) for p in f['polygon_local_m']]
        draw.polygon(poly,fill='#d8cbb7' if f['id']==2018 else '#dedfdd',outline='#788081',width=2)
        label=Polygon(poly).representative_point()
        draw.text((label.x,label.y),{'rear block':'后排砖楼','street block':'临街白楼','west neighbour':'西邻建筑'}[f['role']],anchor='mm',font=font(15),fill='#2e3a40')
    a,b=study['photographed_x_extent_m'];draw.line((screen((a,0)),screen((b,0))),fill='#9d4e28',width=6)
    door=screen((0,0));draw.ellipse((door[0]-5,door[1]-5,door[0]+5,door[1]+5),fill='#763417')
    for idx,(key,row) in enumerate(list(study['positions'].items())[1:]):
        color=('#237489','#694395')[idx];v=screen(row['local_xy_m']);draw.line((v,door),fill=color,width=2)
        draw.ellipse((v[0]-4,v[1]-4,v[0]+4,v[1]+4),fill=color)
        x,y=(v[0]-15,v[1]+5) if not idx else (v[0]+18,v[1]+18)
        draw.text((x,y),('2013年发表照片' if not idx else '2016年1月20日'),anchor='rt' if not idx else 'lt',font=font(13),fill=color)
    draw.line((62,525,62+scale*10,525),fill='#28383f',width=3)
    draw.text((62,534),'10 米',font=font(14),fill='#28383f')
    draw.text((42,570),'位置为照片与轮廓配准估算。地图数据 © OpenStreetMap contributors，ODbL 1.0。',font=font(12),fill='#465053')
    im.save(out)
if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('macro',type=Path);a.add_argument('registration',type=Path);a.add_argument('west_windows',type=Path);a.add_argument('output',type=Path);args=a.parse_args()
    result=estimates(args.macro,args.registration,json.loads(args.west_windows.read_bytes())['adopted_west_edge_x_m'])
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/'courtyard-placement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    plot(result,args.output/'courtyard-plan.png')
