#!/usr/bin/env python3
"""Small CPU-only plan sketch and numerical inputs; does not generate a model."""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import shape,LineString
from shapely.ops import transform
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
from curves import controls,sample,lower_roof_z,upper_band_z,lower_band_z
from build_model import Museum

c=json.loads((HERE/'calibration.json').read_text())
g=json.loads((HERE/'geometry-input.json').read_text())
e=c['estimated'];cv=c['curves']
base=sample(cv['lower_glass_knots_enu_m']);upper=sample(cv['upper_outer_knots_enu_m'])
lowroof=base.buffer(cv['lower_roof_overhang_m'],quad_segs=10)
upglass=upper.buffer(-cv['upper_glass_inset_m'],quad_segs=10)
m=Museum()
source=shape(g['model_geometry_local_east_north_m'])
assert base.is_valid and upper.is_valid and upglass.geom_type=='Polygon'
fig,(ax,el)=plt.subplots(1,2,figsize=(13,6),gridspec_kw={'width_ratios':[1,1.05]})
for poly,color,label,style in [(source,'#222','Frozen owner (identity only)','--'),(lowroof,'#ababab','Lower roof outline estimate','-'),(base,'#378f99','Lower curtain wall estimate','-'),(upper,'#596a80','Upper silver frame estimate','-'),(upglass,'#7856aa','Upper recessed glass estimate',':')]:
    a=np.asarray(poly.exterior.coords);ax.plot(a[:,0],a[:,1],style,color=color,lw=1.5,label=label)
knots=np.asarray(cv['lower_glass_knots_enu_m'])
for inset in c['estimated']['lower_glass_storey_insets_m'][1:]:
    p=np.asarray(base.buffer(-inset).exterior.coords);ax.plot(p[:,0],p[:,1],':',lw=.65,color='#378f99')
for poly in getattr(m.terrace,'geoms',[m.terrace]):
    p=np.asarray(poly.exterior.coords);ax.fill(p[:,0],p[:,1],color='#9cad7a',alpha=.35)
ax.plot(m.spine_path[:,0],m.spine_path[:,1],c='#534934',lw=3,label='Rounded slotted north wrapper')
ax.scatter(knots[:,0],knots[:,1],c='#378f99',s=8)
for i,p in enumerate(knots):ax.text(p[0]+.6,p[1],str(i),fontsize=7)
ax.scatter([-17],[9],marker='s',c='#bd5f27');ax.text(-17,9,' Entry estimate',fontsize=7)
ax.annotate('N',xy=(57,55),xytext=(57,39),arrowprops={'arrowstyle':'->'},ha='center')
ax.set_aspect('equal');ax.set_xlabel('East / m');ax.set_ylabel('North / m')
ax.set_title('Separate curved plans, not repeated source extrusion')
ax.legend(loc='lower left',fontsize=6);ax.grid(alpha=.2)
# A west-facing indicative elevation: this is not a matched photo projection.
y=np.linspace(-59,53,500);x=np.where(y>0,-14,-14-.70*np.maximum(0,-y))
u=-y;rz=np.array([lower_roof_z(xx,yy,e) for xx,yy in zip(x,y)])
el.fill_between(u,.18,rz,color='#c0dadd',alpha=.6)
el.plot(u,rz,c='#7a8794',lw=6)
for band in range(2):
    z=[lower_band_z(xx,yy,band,e) for xx,yy in zip(x,y)]
    el.plot(u,z,c='#d99b0c',lw=4)
uy=np.linspace(0,49.2,220);uu=-uy
el.fill_between(uu,e['upper_glass_bottom_m'],e['upper_glass_top_m'],color='#b8d4d4')
el.plot(uu,np.repeat(e['upper_roof_top_m']-.525,len(uy)),c='#a2a7ac',lw=6)
el.plot(uu,np.repeat(e['upper_lower_deck_top_m']-.475,len(uy)),c='#a2a7ac',lw=5)
el.plot(uu,[upper_band_z(-18,yy,e) for yy in uy],c='#d99b0c',lw=4)
cp=m.c_outer_profile();ci=LineString(cp).offset_curve(-.94,join_style=1)
cpoly=np.asarray([*cp,*list(ci.coords)[::-1]])
el.fill(-53-cpoly[:,0],cpoly[:,1],color='#a2a7ac')
for z in e['interior_plate_levels_m']:el.axhline(z,c='#506b72',lw=.5,ls=':',alpha=.65)
el.set_ylim(0,36);el.set_xlabel('Southward along west-view image / m')
el.set_ylabel('Elevation / m');el.set_aspect('equal')
el.set_title('Indicative west elevation (uncalibrated)');el.grid(alpha=.2)
version=c['model_revision'].split('-')[-1]
fig.tight_layout();png=HERE/'design'/f'plan-elevation-{version}.png';fig.savefig(png,dpi=130);plt.close(fig)
out={'schema':'museum-design-input-math-v1','model_generated':False,'curves_valid':True,
     'calibration_sha256':hashlib.sha256((HERE/'calibration.json').read_bytes()).hexdigest(),
     'source_area_m2':source.area,'lower_glass_plan_area_est_m2':base.area,
     'upper_frame_plan_area_est_m2':upper.area,'upper_glass_plan_area_est_m2':upglass.area,
     'lower_roof_area_outside_source_m2':lowroof.difference(source).area,
     'upper_frame_area_outside_source_m2':upper.difference(source).area,
     'lower_roof_z_range_m':[min(rz),max(rz)],
     'lower_glass_bezier_controls_enu_m':controls(cv['lower_glass_knots_enu_m']).tolist(),
     'upper_outer_bezier_controls_enu_m':controls(cv['upper_outer_knots_enu_m']).tolist(),
     'limits':'Input validity only. Not exported GLB, orientation, camera, contact, visual or browser acceptance.'}
(HERE/'design'/f'curve-input-report-{version}.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if 'controls' not in k},indent=2))
