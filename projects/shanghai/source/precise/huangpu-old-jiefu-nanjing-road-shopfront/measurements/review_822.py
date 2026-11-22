"""Extract the register row, the named shell and two checked neighbour shells.

Pass the frozen gzipped macro and the optional original OSM JSON to rerun offline.
Metric north-front coordinates use the longitude/latitude scale at the western
end of the straight facade. Positive local X is west, positive local Y is inward.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,math
from shapely.geometry import Polygon,Point
from math import radians,cos,sin
MACRO="14-13720-6694"
URL="https://raw.githubusercontent.com/ecojust/e-resource/ae55637ce1d7cbc4d21fd94934c8309aca1dcd09/projects/shanghai/assets/city-detail/macros/"+MACRO+"/feature-table.json.gz"
def review(path):
 raw=path.read_bytes();features=json.loads(gzip.decompress(raw))['features']
 b=next(q for q in features if q['localId']==822)
 assert b['properties']['@name']=='南京大楼' and b['properties']['sources'][0]['record_id']=='w378107150@4'
 ring=b['geometry']['coordinates'][0];lon,lat=ring[2]
 # WGS84 radii of curvature in the local tangent plane.
 a=6378137.;e=.00669437999014;n=a/(1-e*sin(radians(lat))**2)**.5;m=n*(1-e)/(1-e*sin(radians(lat))**2)
 def en(p):return ((p[0]-lon)*math.pi/180*n*cos(radians(lat)),(p[1]-lat)*math.pi/180*m)
 ex,ey=en(ring[3]);width=math.hypot(ex,ey);wx=-ex/width;wy=-ey/width
 def local(p):
  x,y=en(p);return [round(x*wx+y*wy,4),round(-x*wy+y*wx,4)]
 poly=Polygon([en(p) for p in ring])
 address=[121.48089322681783,31.23931227614591]
 return {'macro':MACRO,'macro_sha256':hashlib.sha256(raw).hexdigest(),'url':URL,'owner':b,'register':'5A040 老介福绸缎局 南京东路257号','historical_name_match':'建筑档案原哈同大楼，1936年老介福绸缎局入住底楼，1956年改名南京大楼。','historical_address':'南京东路233–257号（单号）、河南中路382弄1–15号','north_origin_lonlat':ring[2],'local_x_positive':'west along north straight plane','local_y_positive':'south into building','ring_xy_m':[local(p) for p in ring],'straight_north_length_m':width,'wgs84_address_anchor':{'label':'南京商务楼，南京东路233号620（近河南中路）','gcj02':[121.485393,31.237354],'wgs84_approx':address,'inside_822':poly.contains(Point(en(address)))},'neighbors_retained':[dict(localId=q['localId'],name=q['properties'].get('@name'),height=q['height'])for q in features if q['localId'] in [695,1076,251,319]],'source_height_note':'The existing shell is 48 m, estimated from a global 15-floor tag. The 1935 street facade and the taller setback volume visible in photographs do not share a single eaves height.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('macro',type=Path);p.add_argument('output',type=Path);s=p.parse_args();s.output.write_text(json.dumps(review(s.macro),ensure_ascii=False,indent=2)+'\n')
