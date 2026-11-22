"""Calibrate the architect's roof outline against the separately traced southern parapet."""
from pathlib import Path
import json,numpy as np
from math import degrees,atan2
m=Path(__file__).resolve().parent
roof=json.loads((m/'roof-terrace-survey.json').read_bytes());sat=json.loads((m/'south-parapet-aerial-measurements.json').read_bytes())
verts=np.array(roof['roof_plan_edges']['outer_south'],float)
length=sat['roof_chord_m'];scale=length/np.linalg.norm(verts[-1]-verts[0])
run=np.r_[0,np.cumsum(np.linalg.norm(np.diff(verts,axis=0),axis=1))]*scale;run_length=run[-1]
t=run/run_length
def point(at):return np.array([np.interp(at,t,verts[:,c]) for c in (0,1)])
# The centre under the middle window can be placed from the published working-floor plan.
door_station=(.49275+.51155)/2
origin=point(door_station)
west,east=point(door_station-.084),point(door_station+.084)
axis=east-west;axis/=np.linalg.norm(axis)
inside=np.array([axis[1],-axis[0]])
mat=np.vstack([axis,inside])*scale
local=(verts-origin)@mat.T
chord=verts[-1]-verts[0]
rot=degrees(atan2(axis[1],axis[0])-atan2(chord[1],chord[0]))
register=dict(plan_pixel_to_xy=np.column_stack((mat,-mat@origin)).tolist(),drawable_run_m=run_length,
    southern_chord_bearing_deg=sat['axis_bearing_degrees'],central_tangent_bearing_deg=sat['axis_bearing_degrees']+rot,
    native_door_centre=origin.tolist(),door_station=door_station,meters_per_plan_pixel=scale,
    outer_plan_stations=[dict(fraction=round(s,7),x=round(x,4),y=round(y,4)) for s,(x,y) in zip(t,local)],
    west_end_xy=local[0].round(5).tolist(),east_end_xy=local[-1].round(5).tolist(),
    central_nine_window_frame=dict(reference_pixel_to_xz=[[.03460,0,-542.75*.03460],[0,-.03500,738.5*.03500],[0,0,1]],tower_face_y=0.,
    basis='Finished entrance observation, scale of three middle jambs from the standard-floor plan in the traced roof frame. The vertical scale starts from the front-on image. Historic camera registration is tabulated separately.'))

survey=json.loads((m/'south-window-plan-layout.json').read_text())
portal=json.loads((m/'portal-stone-observations.json').read_text())
frame=register['central_nine_window_frame']
scale_x=.03460
frame['vertical_response']=dict(reference_v=738.5,numerator=.04040596,denominator=.00012320)
def z(v):
    q=738.5-v
    return round(.04040596*q/(1+.00012320*q),4)
def x(u):return round((u-542.75)*scale_x,4)
def x_at(f):return round(np.interp(f,t,local[:,0]),4)
def to_local(p):return np.round(mat@(np.array(p)-origin),5).tolist()
# On the side bays the holes are measured behind the projecting stones. Window heights
# are read across the nearest western wide bay in the present frontal photograph.
level_pixels={4:[302.0,365.0],3:[408.0,470.5],2:[517.5,599.5],1:[632.5,724.0]}
ops=[]
for item in survey['openings']:
 row={k:item[k]for k in ('key','bay','level','family')};bay=row['bay'];level=row['level']
 if bay[0]=='C':
  ij=('Cw','Cc','Ce').index(bay);u0,u1=portal['window_clear_cells'][ij];top,sill=portal['window_rows_top_sill'][4-level]
  left,right=x(u0),x(u1)
 else:
  top,sill=level_pixels[level];left,right=x_at(item['u_west']),x_at(item['u_east'])
 row.update(x0=left,x1=right,z0=z(sill),z1=z(top));ops.append(row)
def by(k):return next(a for a in ops if a['key']==k)
bays=[]
for wing,names,out,inside in [('west',['W5','W4','W3','W2','W1'],local[0,0],x(393.2)),('east',['E1','E2','E3','E4','E5'],local[-1,0],x(690.0))]:
 uppers=[by(n+'-F4') for n in names]
 boundaries=[out if wing=='west' else inside]+[(a['x1']+b['x0'])/2 for a,b in zip(uppers,uppers[1:])]+[inside if wing=='west' else out]
 for i,(bay,left,right) in enumerate(zip(names,boundaries,boundaries[1:])):
  bays.append(dict(bay=bay,x0=round(left,4),x1=round(right,4),y0=round(float(np.interp(left,local[:,0],local[:,1])),4),y1=round(float(np.interp(right,local[:,0],local[:,1])),4)))
# Keep the transition into the flat entrance face behind its primary stone towers.
for row in bays:
 if row['bay']=='W1':row['y1']=.06
 if row['bay']=='E1':row['y0']=.06
for e in ('west','east'):
 ends=roof['roof_plan_edges'][e+'_return_outer'];pa,pb=np.array(ends,float);u=pa+(pb-pa)*(419.-pa[1])/(pb[1]-pa[1]);register[e+'_return_xy']=[to_local(pa),to_local(u)]
# The westernmost horizontal window crosses the deck cut. Extend its supporting return
# to the intact length observed on the west bridge and the finished aerial view.
west_pair=np.array(register['west_return_xy']);dx=west_pair[1]-west_pair[0];dx/=np.linalg.norm(dx)
register['west_return_xy']=[west_pair[0].tolist(),(west_pair[0]+11.10*dx).round(5).tolist()]
layout=dict(survey=register,frame=frame,roof_deck_z=18.20,roof_front_chord_m=length,roof_deck_back_plan_v=419,outer_ends_xy=[local[0].round(5).tolist(),local[-1].round(5).tolist()],
    upper_storey_z={str(n):[z(sill),z(top)]for n,(top,sill)in level_pixels.items()},bay_wall_top=z(235),pier_shoulder_top=z(231),pier_peak_top=z(217),
    central_towers_x=[x(393.2),x(690.)],bays=bays,openings=ops,west_return=register['west_return_xy'],east_return=register['east_return_xy'],
    interpretation='Independent measured window locations on the working floor and roof plans, scaled to the observed 59.369 m roof chord. Window frame dimensions at the centre use the contemporary entrance photo. Photographs show some variation in finish and head/sill; the documented centre-to-side height difference is retained.')
layout['west_return_windows']=json.loads((m/'west-return-windows.json').read_bytes())['openings']
(m/'riverfront-layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
print('windows',len(ops),'bays',[(b['bay'],b['x0'],b['x1'])for b in bays],'sides',layout['west_return'],layout['east_return'])
