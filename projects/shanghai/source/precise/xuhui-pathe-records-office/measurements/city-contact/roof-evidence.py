"""Apply conservative visible-tile patches to the actual sampled building footprint."""
from pathlib import Path
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
import argparse, json, math
p=argparse.ArgumentParser();p.add_argument('sections',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
def load(path):return json.loads(path.read_bytes())
j=load(a.sections);maps=load(Path(__file__).with_name('aerial-controls.json'));out={}
origin=j['north_wall_midpoint_wgs84'];bx,by=map(math.radians,j['directions_degrees'])
for name,m in maps.items():
    frame=unary_union([Polygon(z) for z in m['visible_tile_patches']]);zoom=m['zoom'];x0,y0,width,height=m['crop'];w,h=m['display_size']
    rows=[]
    for n,(x,y) in enumerate(j['grid']):
        # Use latitude-dependent metre conversion, then the original provider zoom and the actual output raster dimensions.
        lon=origin[0]+math.degrees((x*math.sin(bx)+y*math.sin(by))/(6371008.8*math.cos(math.radians(origin[1]))))
        lat=origin[1]+math.degrees((x*math.cos(bx)+y*math.cos(by))/6371008.8)
        u=((lon+180)/360*2**(zoom+8)-x0)*w/width
        v=((1-math.asinh(math.tan(math.radians(lat)))/math.pi)*2**(zoom+7)-y0)*h/height
        if frame.covers(Point(u,v)):
            rows.append({'grid_index':n,'pixel':[round(u,2),round(v,2)],'model':j['first_roof_z']['full'][n],'old_near':j['first_roof_z']['old_near'][n],'old_far':j['first_roof_z']['old_far'][n]})
    out[name]={'points_on_clear_roof_material':len(rows),'model_misses_where_old_near_present':sum(r['model'] is None and r['old_near'] is not None for r in rows),'model_misses_where_old_far_present':sum(r['model'] is None and r['old_far'] is not None for r in rows),'samples':rows}
a.output.write_text(json.dumps(out,separators=(',',':'))+'\n')
print({k:{z:i for z,i in v.items()if z!='samples'}for k,v in out.items()})
