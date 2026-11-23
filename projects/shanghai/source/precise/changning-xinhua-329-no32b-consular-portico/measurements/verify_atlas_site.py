"""Reproduce the planning-map address estimates from published numerical controls."""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

def fit(points):
    u0,v0,x0,y0 = [sum(row[i] for row in points)/len(points) for i in range(4)]
    residuals = [(u-u0,v-v0,x-x0,y-y0) for u,v,x,y in points]
    denom = sum(u*u+v*v for u,v,x,y in residuals)
    a = sum(u*x+v*y for u,v,x,y in residuals)/denom
    b = sum(u*y-v*x for u,v,x,y in residuals)/denom
    def transform(u,v):
        return x0+a*(u-u0)-b*(v-v0), y0+b*(u-u0)+a*(v-v0)
    return transform,math.hypot(a,b)

def read():
    record = json.loads((HERE/'atlas-site-review.json').read_bytes())
    lon,lat = record['fit']['centre_wgs84']
    rpd = math.pi/180
    eccentricity = 0.0066943799901413165
    w = math.sqrt(1-eccentricity*math.sin(lat*rpd)**2)
    east = 6378137*math.cos(lat*rpd)*rpd/w
    north = 6378137*(1-eccentricity)*rpd/w**3
    def metres(lonlat):
        return (lonlat[0]-lon)*east,(lonlat[1]-lat)*north
    controls = [(c['map_px'][0],-c['map_px'][1],*metres(c['wgs84'])) for c in record['controls']]
    predict,scale = fit(controls)
    u,v = record['source']['plan']['target_px']
    x,y = predict(u,-v)
    base = record['independent_check']
    u,v = base['observed_px']
    road_residual = math.dist(predict(u,-v),metres(base['wgs84']))
    holdouts = []
    for i,(u,v,xh,yh) in enumerate(controls):
        check,_ = fit([p for j,p in enumerate(controls) if j!=i])
        holdouts.append(round(math.dist(check(u,v),(xh,yh)),3))
    assert abs(scale-record['fit']['m_per_px'])<.0001
    assert math.hypot(x,y)<.02
    assert abs(road_residual-base['error_m'])<.01
    assert max(abs(x-y) for x,y in zip(holdouts,record['fit']['leave_one_out_m']))<.016
    return {'target_wgs84':[lon+x/east, lat+y/north],
            'metres_per_pixel':scale,
            'withheld_road_error_m':road_residual,
            'leave_one_building_out_m':holdouts}

if __name__=='__main__':
    print(json.dumps(read(),indent=2))
