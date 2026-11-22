"""Transfer the visible garden wings from the 690 × 821 photograph to two measured wall planes."""
from pathlib import Path
import json
import numpy as np

HERE=Path(__file__).resolve().parent
cameras=json.loads((HERE/'garden-corner-camera.json').read_bytes())
M=np.array(cameras['main_corner_projection'])
corn_x,corn_y=cameras['arranged_on_bay_datum_m']
def at(px,axis,offset):
    m=M[:2]-np.asarray(px)[:,None]*M[2]
    free=[v for v in range(3) if v!=axis]
    p=np.zeros(3);p[axis]=offset
    p[free]=np.linalg.solve(m[:,free],-m[:,axis]*offset-m[:,3])
    return p
def uv(p):
    q=M@[*p,1.]
    return q[:2]/q[2]
near_wall=float(at((102,429),0,corn_x)[1])
far_side=float(at((46,423),1,near_wall)[0])
rear_end=float(at((16,455),0,far_side)[1])
planes={'main_return':(0,corn_x),'main_front':(1,corn_y),'side_projection_front':(1,near_wall),'side_projection_side':(0,far_side)}
def opening(plane,kind,corners,cols,rows):
    axis,depth=planes[plane]
    along=1-axis
    pts=np.array([at(pt,axis,depth) for pt in corners])
    left,right=sorted([float(np.mean(pts[[0,3],along])),float(np.mean(pts[[1,2],along]))])
    base,head=sorted([float(np.mean(pts[:2,2])),float(np.mean(pts[2:,2]))])
    return dict(plane=plane,kind=kind,original_pixel_corners=corners,outer_trim_m=[round(v,5) for v in (left,right,base,head)],columns=cols,rows=rows)
rows=[
 opening('side_projection_front','garden-side second bay, upper',[(57,447),(99,451),(99,533),(55,528)],2,5),
 opening('side_projection_front','garden-side second bay, lower',[(55,590),(98,589),(97,669),(54,672)],2,5),
 opening('side_projection_side','garden-side second bay, upper side',[(20,474),(40,450),(41,527),(18,545)],2,4),
 opening('main_return','casement behind second terrace',[(53,356),(91,316),(91,414),(53,432)],3,4),
 opening('main_front','terrace left tall casement',[(346,188),(371,200),(371,303),(346,302)],2,6),
 opening('main_front','terrace broad casement',[(383,207),(426,228),(426,325),(383,314)],4,6),
 opening('main_front','terrace right partly screened casement',[(438,242),(464,256),(464,340),(438,333)],2,5),
 opening('main_front','garden frontage, right middle casement',[(554,433),(586,444),(586,519),(554,509)],2,4),
 opening('main_front','garden frontage, right upper casement',[(555,290),(582,303),(582,359),(555,351)],2,3),
 opening('main_front','garden frontage, lower shaded entrance',[(544,557),(595,562),(595,694),(544,694)],1,1)
]
data=dict(source=cameras['source_url'],source_sha256=cameras['source_sha256'],coordinate_system='Local garden bay drawing in metres, positive Z upward; the photographed garden corner is the primary reference.',
          estimated_scope='Extend only the visible garden-side wing. Second terrace depth, frames behind the balustrades, unseen edges of windows and shaded doorway are estimates. The roof surface ends just behind the visible eaves. Rear, interior, and unobserved roof geometry are omitted.',
          main_corner_projection=M.tolist(),main_corner_m=[corn_x,corn_y],side_projection=dict(wall_end_pixels=[102,429],corner_pixels=[46,423],far_end_pixels=[16,455],front_y_m=near_wall,outer_x_m=far_side,far_y_m=rear_end),
          aperture_observations=rows,outer_extent_m={'front_x_end':8.20,'side_y_end':11.45},roof=dict(eave_upper_z_m=10.025,exposed_depth_m=.93,estimated_pitch_degrees=21),
          ground_coverage='Front of the far return, risers and garden-side low window remain partly screened in the photograph. Clipped at the recorded visible section.')
(HERE/'garden-extensions.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
