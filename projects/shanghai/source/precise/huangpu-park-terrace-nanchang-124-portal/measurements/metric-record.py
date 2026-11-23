import os
"""Reproduce the exterior wall arch intersection and the two projected street piers."""
import json,math,runpy,hashlib
from pathlib import Path
from shapely.geometry import Polygon,Point
w=Path(__file__).resolve().parent
lib=runpy.run_path(str(w/'solve-anchor.py'))
tri,xy,geo=[lib[k]for k in ('tri','xy','geo')]
read=lambda f:json.loads(f.read_bytes())
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
def save(f,x):f.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
station='portal-10-297';west='portal-west124';winter='portal-westwinter124-caps'
marks={
 'outer_arch_crown':((station,315,255),(west,440,237)),
 'inner_arch_crown':((station,318,266),(west,443,246)),
 'west_inner_impost':((station,280,294),(west,409,271)),
 'east_inner_impost':((station,348,289),(west,478,265)),
 'west_pier_cap':((station,257,360),(winter,420,303)),
 'east_pier_cap':((station,370,350),(winter,567,287)),
 'right_plate_midpoint':((station,370,416),(winter,570,372)),
}
results={k:dict(observations=obs,**tri(*obs))for k,obs in marks.items()}
H=math.radians(65.4);A=(math.sin(H),math.cos(H));I=(-math.cos(H),math.sin(H))
c=xy(*results['outer_arch_crown']['lnglat']);dot=lambda a,b:sum(x*y for x,y in zip(a,b))
def local(point):
 p=xy(*point);delta=[p[i]-c[i]for i in range(2)]
 return [dot(delta,A),dot(delta,I)]
for mark in results.values():mark['author_xy']=local(mark['lnglat'])
rows=read((Path(os.environ['SHANGHAI_SURVEY_ROOT']) / 'source-block.json'))['rows'];nearest=[]
for row in rows:
 poly=Polygon([local(v)for v in row['geometry']['coordinates'][0]])
 nearest.append(dict(id=row['localId'],key=row['key'],distance_m=poly.distance(Point(0,0)),polygon_square_m=poly.area))
nearest.sort(key=lambda i:i['distance_m']);assert nearest[0]['id']==3695 and nearest[0]['distance_m']<.32 and nearest[1]['distance_m']>13
ids={n:dict(camera=read(w/(n+'.json'))['station'],rectified=read(w/(n+'.json')),bytes_sha256=sha(w/(n+'.jpg')))for n in (station,west,winter)}
record=dict(anchors=results,source_records=ids,survey_notes=['两处2023年6月9日相向街站距券门约11米。站位、原球面瓦片及透视式分别在source_records列出，券顶光线交角约87度。','两座街柱在2023年西侧站被树干遮挡，采用该年东侧站和2020年2月20日另一站复算。树影遮住的柱帽以及设备高度与光学标定约带来0.3—0.5米分歧，以两站中值控制柱高。','Fayhoo于2014年10月31日上传的近街照片证实券套实有进深、后部横格气窗、独立方柱、柱帽和前方暗色活动门，门牌为124。'])
save(w/'triangulated.json',record)
m=dict(id='huangpu-park-terrace-nanchang-124-portal',wgs_anchor=results['outer_arch_crown']['lnglat'],azimuth_x_deg=65.4,axes=[A,I],original_neighbors=nearest[:12],owner=3695,dimensions_m=dict(arch_crown=4.02,intrados_crown=3.88,clear_width=1.20,impost=3.28,wall_depth=.39,transom_head=2.94,transom_sill=2.44,west_pier_x=-.35,east_pier_x=1.79,west_pier_y=-.68,east_pier_y=-.90,pier_width=.47,pier_depth=.48,pier_west_top=2.50,pier_east_top=2.59,plate_midpoint_height=1.77,front_gate_top=2.12),uncertainty_m=dict(arch_xy=.32,arch_z=.25,impost=.28,street_pier_xy=.44,street_pier_height=.28,gate_top=.20,door_recess=.28),photo_sha256=sha(w/'park-source.json'),measurements_sha256=sha(w/'triangulated.json'),exclusions=['相邻126号的另一券、132/134号门户及136弄主入口','东侧110弄上海別墅全体','整段沿街3695原屋、上层窗、墙外空调箱及树木、门内房间'])
save(w/'measured-facade.json',m)
print(m['wgs_anchor'],nearest[:2])
