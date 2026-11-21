"""Fit the three independently surveyed window axes in the two Commons photograph revisions."""
from pathlib import Path
import json,numpy as np

HERE=Path(__file__).absolute().parent
controls=json.loads((HERE/'416-measurement-work.json').read_bytes())
axis=np.array(json.loads((HERE/'frontage-controls.json').read_bytes())['facade_axis_relative_west_and_north_easting_northing'])
origin=np.array(controls['third_flat_upper_window_center_at_sill']['metres'])
def u(name):return float((np.asarray(controls[name]['metres'])-origin)@axis)
axes=['first_flat_upper_window_center_at_sill','second_flat_upper_window_center_at_sill','third_flat_upper_window_center_at_sill']
edges=['outer_front_fascia_left_edge_of_door','outer_front_fascia_right_edge_of_door','door_portal_left_outer_at_header','door_portal_right_outer_at_header']
plates=[
    dict(year=2014,pixels=[2136,1424],sha256='ba16548d70375447ea888ee91a1e9161d6fa92b65e5ce0e339abdacaa65d575e',
         x_axes=[632,875,1150],sash_row=565,edge_pixels=[[975,735],[1327,735],[999,765],[1299,765]]),
    dict(year=2020,pixels=[3323,2374],sha256='b77285cc38ed84222141103f12a7c6d0d48490fccecdbf443cb2ffd251027a2d',
         x_axes=[1094,1432,1779],sash_row=1115,edge_pixels=[[1560,1357],[1998,1357],[1594,1415],[1962,1415]])]
observations=[]
for plate in plates:
    x=np.array([u(name)for name in axes]);px=np.asarray(plate['x_axes'])
    scale,centre=np.linalg.lstsq(np.c_[x,np.ones(3)],px,rcond=None)[0]
    close=[dict(name=name,original_xy=xy,projected_x_px=round(float(scale*u(name)+centre),3),residual_px=round(float(xy[0]-scale*u(name)-centre),3))for name,xy in zip(edges,plate['edge_pixels'])]
    observations.append({**plate,'fitted_window_axes':axes,'scale_px_per_m':float(scale),'zero_x':float(centre),
                         'axis_fit_rms_px':float(np.sqrt(np.mean((scale*x+centre-px)**2))),'unused_portal_controls':close,
                         'portal_check_rms_px':float(np.sqrt(np.mean([c['residual_px']**2 for c in close])))})
result=dict(axes_wgs84=controls[axes[-1]]['wgs84'],method='Two independent 1-D affine fits on three flat window axes. Out-of-plane door piers and the projecting lintel are withheld. Pixel coordinates use the full original, top-left origin.',
            scope='Each fit describes the central plane over its three positions. The rounded end tower, canted stair window and roof ridge lie outside that plane. Heights are photographic estimates.',
            observations=observations)
out=HERE/'two-date-window-registration.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for a in observations:print(a['year'],a['scale_px_per_m'],a['axis_fit_rms_px'],a['portal_check_rms_px'])

