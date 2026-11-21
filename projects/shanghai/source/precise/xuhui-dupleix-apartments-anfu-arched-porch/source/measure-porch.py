"""Triangulate visible porch landmarks from two 2017 stations, without assigning the city rectangle to the front columns."""
from pathlib import Path
from math import radians,degrees,pi,sin,cos,tan,hypot,atan2
from statistics import mean
from hashlib import sha256
import json,sys
w=Path(__file__).resolve().parent
images=w/'street-measurement-inputs'
read=lambda p:json.loads(p.read_bytes())
def digest(p):return sha256(p.read_bytes()).hexdigest()
ref=[121.43809408,31.215542695]
scale=[6371008.8*radians(1)*cos(radians(ref[1])),6371008.8*radians(1)]
def xy(p):return [(v-a)*b for v,a,b in zip(p,ref,scale)]
def ll(p):return [a+v/b for v,a,b in zip(p,ref,scale)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
source={}
for key in ('497061Y','478021Y'):
 f=next(images.glob('street-*'+key+'.json'));data=read(f)
 if f.with_suffix('.jpg').exists():assert digest(f.with_suffix('.jpg'))==data['sha256']
 source[key]=data
coords={'east-pilaster-boss':[(364.0,389.5),(469.5,365.5)],'west-pilaster-boss':[(468.0,375.0),(740,387)],
        'west-pilaster-base':[(468,577),(740,652)],'west-window-on-main-brick-wall-head':[(599.5,409.5),(784.0,447)]}
def result(rs):
 rays=[]
 for p,(u,v) in zip(source.values(),rs):
  m=p['pano'];bearing=(p['xy'][0]+u+.5)*2*pi/p['sw']-radians(m['north'])
  dir_=[sin(bearing),cos(bearing)];el=pi/2-(p['xy'][1]+v+.5)*2*pi/p['sw'];rays.append((xy(m['ll']),dir_,el,m['height']))
 (o1,d1,*_),(o2,d2,*_)=rays;cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
 intersect=cross(sub(o2,o1),d2)/cross(d1,d2);pos=[a+b*intersect for a,b in zip(o1,d1)];heights=[h+hypot(*sub(pos,o))*tan(a) for o,d,a,h in rays]
 assert all(dot(sub(pos,o),d)>0 for o,d,a,h in rays)
 return dict(pixel_xy={q:p for q,p in zip(source,rs)},xy=pos,wgs84=ll(pos),heights_m=heights,average_m=mean(heights))
marks={k:result(v)for k,v in coords.items()}
left=marks['east-pilaster-boss']['xy'];right=marks['west-pilaster-boss']['xy'];rear=marks['west-window-on-main-brick-wall-head']['xy']
middle=[(a+b)/2 for a,b in zip(left,right)];delta=sub(right,left);span=hypot(*delta);axis=[v/span for v in delta]
street=[axis[1],-axis[0]];assert street[1]>.75
depth=dot(sub(middle,rear),street)
info={k:{'id':v['pano']['id'],'date':v['pano']['date'],'ll':v['pano']['ll'],'north':v['pano']['north'],'camera_height_m':v['pano']['height'],'metadata':v['pano']['meta'],'source_tiles':v['tiles'],'image_sha256':v['sha256'],'crop_offset':v['xy']}for k,v in source.items()}
out=dict(order=367,source=info,points=marks,station_baseline_m=hypot(*sub(xy(info['497061Y']['ll']),xy(info['478021Y']['ll']))),midpoint_wgs84=ll(middle),pilaster_axis_span_m=span,street_normal_deg=degrees(atan2(*street))%360,street_unit_east_north=street,boss_projection_from_back_brick_window_m=depth,boss_midpoint_vs_generic_north_line_m=dot(middle,street),source_bearing_checks='The west return has a narrow arched opening before the actual brick elevation. The separately identified rear arched window belongs to the street elevation of the main building.',source_limitation='Registered panorama centres and headings are from the 2017-09-04 imagery metadata. Washed-stone medallion faces project from the face of the porch and the rear window is measured at its reveal. The horizontal discrepancy with 1784 is retained.')
vertical=[a-b for a,b in zip(marks['west-pilaster-boss']['heights_m'],marks['west-pilaster-base']['heights_m'])]
out['boss_to_base_height_m_by_station']=vertical
out['two_station_median_height_m']=mean(vertical)
out['gauge']='Front and side figures come from the same 2017-09-04 vehicle session with a surveyed baseline of 11.26 m. Absolute camera estimates differ, so the two relative base-to-medallion heights are given separately.'
output=Path(sys.argv[1]) if len(sys.argv)>1 else w/'porch-2017-recalculated.json'
output.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print({k:v for k,v in out.items()if isinstance(v,(float,int))});print({k:v['heights_m']for k,v in marks.items()});print('center',out['midpoint_wgs84'])
