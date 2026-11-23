"""Relate two winter views and the city polygons to the lane-side street fragment."""
from pathlib import Path
import json,hashlib,math
import numpy as np
w=Path(__file__).absolute().parent
reg=w.parent/'registration';base=w.parent/'research/east'
load=lambda p:json.loads(p.read_bytes())
dg=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cam=load(reg/'street-cameras.json');tab=load(w/'feature-candidates.json')
observations={'2002-4':{'jamb-low-left':[696,665],'jamb-low-right':[896,691],'jamb-middle-left':[690,596],'jamb-middle-right':[880,601]},'1512-4':{'jamb-middle-left':[744,602],'jamb-middle-right':[990,602]}}
result={}
for station,clicks in observations.items():
 c=cam['cameras'][station];C=np.array(c['C']);K=np.array(c['K']);R=np.array(c['R'])
 placements=[]
 for y in [0,.20,.40]:
  segment={}
  for label,pix in clicks.items():
   ray=R.T@np.linalg.solve(K,[*pix,1]);q=C+(y-C[1])/ray[1]*ray;segment[label]=[round(v,3) for v in q]
  widths={k:round(segment['jamb-'+k+'-right'][0]-segment['jamb-'+k+'-left'][0],3) for k in ['middle','low'] if 'jamb-'+k+'-left' in segment}
  placements.append(dict(assumed_setback=y,points=segment,width_m=widths))
 result[station]={'pixels_1050x800':clicks,'image_sha256':dg(base/('view-'+station+'.jpg')),'planes':placements}
periods={}
for f in sorted(w.glob('release-*.json')):
 j=load(f);att=[r for m in j['metadata'] for r in m['records']]
 if not att:continue
 t=att[0];periods[f.stem]={'date':t['SRC_DATE'],'provider':t['NICE_DESC'],'image_source':t['SRC_DESC'],'native_gsd_m':t['SRC_RES'],'published_horizontal_accuracy_m':t['SRC_ACC'],'tile_urls':j['tiles'],'metadata_url':j['metadata'][0]['url'],'source_record_sha256':dg(f)}
report={'model_subject':'新乐路143-1号临街东楼可见红砖面及143弄入口一侧','local_reference':{'origin_wgs84':cam['origin_wgs84'],'axis_X_azimuth_degrees':cam['x_azimuth_degrees'],'axis_Y':'Into building, positive southeast','camera_file_sha256':dg(reg/'street-cameras.json'),'polygon_table_sha256':tab['sha256_table']},'street_owner_493':{'source_key':tab['rows'][0]['key'],'geometry':'one Polygon, one exterior ring with eight distinct corners and no holes','x_extent':[-29.03,-.40],'northern_long_edge_x_y':[[-28.68,5.81],[-.4,6.11]],'roofward_limits_station_frame':{'eastern_portion':{'x':[-29,-18.2],'back_y':15.6,'plan_depth':9.8},'middle_portion':{'x':[-18.2,-8.6],'back_y':10.6,'plan_depth':4.8},'lane_side_western_portion':{'x':[-8.04,-.45],'back_y':13.68,'plan_depth':7.57}},'protected_extent':'The feature covers a long street row and three different back limits. The photographed red wall extends from about X −8.7 to +2.387 on the measured pavement frame. Suppressing the whole original row would remove neighboring street frontage.'},'separate_footprints':{'opposite_side_of_lane':4001,'opposite_across_street':[424,3316],'detached_in_court':3674,'cadastral_aperture_between_two_frontages_m':5.32,'side_and_rear_addresses':'No numbered photograph assigns separate 1–4 to these footprints. No polygon number identifies the address without the photograph/street checks.'},'actual_clear_lane_m':{'estimate':3.1,'range':[2.8,3.6],'points':result,'definition':'Space between visible inside faces of the two jambs. The cadastral opening between outside building edges includes the masonry piers. The gate leaves and visibility of their lower edges differ in the two winters. The hard edge on the west side is partly obscured by the tree/parked car in 2015.'},'plan_alignment':{'street_side_offset_source_minus_photo_m':[5.8,6.2],'opposite_street_offset_source_minus_photo_m':[5.8,6.6],'true_street_width_m':[15.8,16.7],'assumption':'The shared offset across the two street fronts supports a nearly rigid translation. The east-west offset cannot be fixed from this baseline alone.'},'orthophotos':periods,'roof_reading':{'best_dates':['2019-11-09','2025-04-07'],'observations':'In both of the clearest mosaics the two front roofs on either side of the narrow opening have a separate second rank of warm tiled roof shapes behind a dark transverse break. On the lane-side part of 493 the visible individual front pitch covers approximately 9–12 m along the street and 7–10 m in depth. Calibration to the street photo includes eaves overhang, roof-height parallax, and lateral registration uncertainty. The independent middle and east portions of 493 continue along the street. The aerial image alone does not establish which interior door belongs to which roof.','local_reference_samples':'Pixel coordinates in roof-grid-base-*.jpg map to local metres by X=(u−270)/7, Y=(355−v)/7. The annotated two-by-two contact sheet groups the 2010, 2019, 2021 and 2025 acquisition records.','clip_recommendation':'Keep all native material outside the photographed street-side volume. For a city test, use a component- or triangle-level cut of the identified west end of 493 and draw the original remainder, with the roof and row to the east preserved. Feature 4001 and all distinct courtyard features require independent evidence before changing them.'}}
(w/'street-row-and-lane.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
