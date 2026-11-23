"""Compare two orthophoto roof extents against original city polygons. Units are local WGS84 metres."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from shapely.affinity import translate
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union

def features(file):
    decoder = json.JSONDecoder()
    with gzip.open(file, 'rt') as stream:
        buf = stream.read(32768).split('"features":[', 1)[1]
        while True:
            buf = buf.lstrip(', \n')
            if buf.startswith(']'):
                return
            try:
                row, end = decoder.raw_decode(buf)
            except ValueError:
                more = stream.read(32768)
                if not more:
                    raise
                buf += more
                continue
            yield row
            buf = buf[end:]

def sha(path):
    with path.open('rb') as fp:
        return hashlib.file_digest(fp,'sha256').hexdigest()

def frame(x, y):
    lat = math.radians(y)
    a, ecc = 6378137, 0.0066943799901413165
    k = 1-ecc*math.sin(lat)**2
    mx = math.pi/180*a*math.cos(lat)/math.sqrt(k)
    my = math.pi/180*a*(1-ecc)/k**1.5
    return lambda p: ((p[0]-x)*mx,(p[1]-y)*my), lambda e,n:(x+e/mx,y+n/my)

def local_polygon(row, local):
    g = row['geometry']
    parts = [g['coordinates']] if g['type']=='Polygon' else g['coordinates']
    return unary_union([Polygon([local(p) for p in ring[0]],[[local(p) for p in r] for r in ring[1:]]) for ring in parts])

def georings(local, localinv, record):
    p,q = [local(pt) for pt in record['long_axis']]
    a,b = [local(pt) for pt in record['cross_axis']]
    dx,dy=q[0]-p[0],q[1]-p[1]
    size=math.hypot(dx,dy)
    u,v=(dx/size,dy/size),(-dy/size,dx/size)
    dot=lambda f,g:sum(x*y for x,y in zip(f,g))
    start,end=sorted([dot(p,u),dot(q,u)])
    lo,hi=sorted([dot(a,v),dot(b,v)])
    corners=[(t*u[0]+s*v[0],t*u[1]+s*v[1]) for t,s in [(start,lo),(end,lo),(end,hi),(start,hi)]]
    return Polygon(corners),dict(axis_length_m=size,projected_width_m=hi-lo,bearing_deg=math.degrees(math.atan2(*u))%360,corners_wgs84=[localinv(*x) for x in corners],cross_axis_points_wgs84=record['cross_axis'],long_axis_points_wgs84=record['long_axis'])

def quote_owner(row, g, roof, inv):
    a=g.intersection(roof).area
    return dict(localId=row['localId'],key=row['key'],source_height_m=row['height'],source_area_m2=g.area,
                source_centroid=inv(g.centroid.x,g.centroid.y),roof_area_m2=roof.area,overlap_m2=a,
                roof_coverage=a/roof.area,source_coverage=a/g.area,iou=a/(roof.area+g.area-a),
                separation_m=g.distance(roof),original_geometry=row['geometry'])

def main():
    cli=argparse.ArgumentParser()
    cli.add_argument('table',type=Path);cli.add_argument('axes',type=Path);cli.add_argument('out',type=Path)
    cli.add_argument('--point-query',nargs=2,type=float);cli.add_argument('--point-out',type=Path)
    cfg=cli.parse_args()
    controls=json.loads(cfg.axes.read_bytes());p=next(iter(controls.values()))['long_ridge_midpoint']
    local,inv=frame(*p);sites={}
    regions=[p]
    if cfg.point_query:regions.append(cfg.point_query)
    count=0
    for row in features(cfg.table):
        count+=1
        bb=row['geometry']['coordinates']
        while isinstance(bb[0][0],list):bb=bb[0]
        if any(abs(pt[0]-x)<.002 and abs(pt[1]-y)<.002 for pt in bb for x,y in regions):
            sites[row['localId']]=(row,local_polygon(row,local))
    assert count==4157,count
    out=dict(source_url='https://raw.githubusercontent.com/ecojust/e-resource/ae55637ce1d7cbc4d21fd94934c8309aca1dcd09/projects/shanghai/assets/city-detail/macros/14-13718-6695/feature-table.json.gz',table_sha256=sha(cfg.table),feature_count=count,control_sha256=sha(cfg.axes),method='Use two lines perpendicular to the long-axis through its endpoints and two parallel lines through the measured ends of the transverse span. These four lines bound the measured roof rectangle. Heights on existing meshes are approximate. Absolute imagery accuracy is 8.47 m. Translation sensitivity samples the full radius every 5 degrees and a 1 m interior grid. Axis lengths and overlaps use local WGS84 metres.',dates={})
    for station,r in controls.items():
        roof,axes=georings(local,inv,r)
        err=r['provider_abs_m'];near={k:v for k,v in sites.items() if v[1].distance(roof)<=25}
        measured=sorted([quote_owner(v[0],v[1],roof,inv) for v in near.values()],key=lambda a:(-a['overlap_m2'],a['separation_m']))
        moved=[(0,0)]+[(i,j) for i in range(-8,9) for j in range(-8,9) if 0<i*i+j*j<=err**2]+[(err*math.cos(math.radians(i)),err*math.sin(math.radians(i))) for i in range(0,360,5)]
        sensitivity={k:[]for k in near};winners={}
        for dx,dy in moved:
            t=translate(roof,dx,dy);areas={k:t.intersection(v[1]).area for k,v in near.items()}
            win=max(areas,key=areas.get) if max(areas.values())>0 else 'no overlap'
            winners[win]=winners.get(win,0)+1
            for k,val in areas.items():sensitivity[k].append(val)
        out['dates'][station]=dict(date=r['date'],provider_abs_m=err,roof=axes,owners=measured,displacement_samples=len(moved),owner_max_overlap_counts=winners,
            sampled_overlap_m2_bounds={k:[min(vals),max(vals)]for k,vals in sensitivity.items() if max(vals)>0},owners_within_uncertainty_radius=[m['localId']for m in measured if m['separation_m']<=err])
    cfg.out.write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
    if cfg.point_query:
        point=Point(*local(cfg.point_query))
        rr=[dict(localId=r['localId'],key=r['key'],area_m2=g.area,point_to_boundary_m=g.boundary.distance(point),point_to_polygon_m=g.distance(point),covers=g.covers(point),height_m=r['height'],centroid=inv(g.centroid.x,g.centroid.y),geometry=r['geometry'])for r,g in sites.values() if g.distance(point)<25]
        cfg.point_out.write_text(json.dumps(dict(center=cfg.point_query,georef_uncertainty_m=[10,15],radius_m=25,source_sha256=out['table_sha256'],owners=sorted(rr,key=lambda r:(r['point_to_polygon_m'],r['point_to_boundary_m']))),indent=2)+'\n')
    print([(r['date'],[(t['localId'],round(t['roof_coverage'],3),round(t['iou'],3),round(t['separation_m'],1))for t in r['owners'][:5]],r['owner_max_overlap_counts'])for r in out['dates'].values()])
if __name__=='__main__':main()
