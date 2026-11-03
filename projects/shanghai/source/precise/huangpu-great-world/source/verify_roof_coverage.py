"""Independent projected coverage of actual serialized horizontal roof faces.

This reads exported triangles, not Builder parts. It detects continuous gaps
between inward roof fields, wall caps, shrinking tower tiers and pavilion lids.
It does not certify interiors or historical dimensions.
"""
import argparse,json,math,hashlib
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from verify_serialized import load

def regular(c,r,n=6,a=math.pi/6):return Polygon([(c[0]+r*math.cos(a+i*math.tau/n),c[1]+r*math.sin(a+i*math.tau/n))for i in range(n)])
def check(path,lod=False,source_asset=None):
 t,tags,_=load(path,source_asset);params=json.loads(Path(__file__).with_name('model-parameters.json').read_text());xy=t[:,:,:2];zs=t[:,:,2];flat=np.ptp(zs,axis=1)<1e-5
 original=Polygon(params['plan_vertices_enu_m']);poly=original.difference(Polygon(params['theater_exclusion_enu_m']).buffer(.15,join_style=2));c=params['tower_center_enu_m']
 cases=[('main U roof and exterior wall cap',poly,20.30,20.41),('arched tower continuous ceiling',regular(c,5.12,12),25.70,26.13),('first straight tower continuous ceiling',regular(c,4.35),30.40,30.92),('second straight tower continuous ceiling',regular(c,3.67),34.77,35.29)]
 for i,p in enumerate(params['pavilions']):
  for level in range(p['levels']):
   top=20.4+(level+1)*(3.6 if p['levels']==2 else 3.5);cases.append((f'pavilion {i+1} level {level+1} ceiling',regular(p['center_enu_m'],p['radius_m'],8 if lod else 10,0),top-.31,top+.03))
 rows=[]
 for label,expected,low,high in cases:
  ids=np.flatnonzero(flat&(zs.mean(axis=1)>=low)&(zs.mean(axis=1)<=high));surface=unary_union([Polygon(xy[i])for i in ids if Polygon(xy[i]).area>1e-10]);test=expected.buffer(-.002);gap=test.difference(surface);rows.append({'label':label,'expected_area_m2':test.area,'uncovered_area_m2':gap.area,'horizontal_faces':len(ids),'z_interval_m':[low,high],'passed':gap.area<1e-4})
 # Gray roof top and stone wall cap intentionally differ by4cm. Test actual planes.
 grayids=np.flatnonzero(flat&(tags=='roof zinc')&(np.abs(zs.mean(axis=1)-20.36)<1e-4));stoneids=np.flatnonzero(flat&np.isin(tags,['warm stone','pale dressed stone'])&(np.abs(zs.mean(axis=1)-20.36)<1e-4));gray=unary_union([Polygon(xy[i])for i in grayids]);stone=unary_union([Polygon(xy[i])for i in stoneids]);overlap=gray.intersection(stone).area
 return {'id':params['id'],'asset':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'variant':'lod'if lod else'full','records':rows,'main_roof_coplanar_gray_stone_overlap_m2':overlap,'main_roof_cap_level_separation_m':.04,'passed':all(r['passed']for r in rows)and overlap<1e-6,'tolerance':'Expected polygons inward2mm to exclude FLOAT32 boundary noise; max uncovered0.0001sqm. These are coverage tests of bounded exterior roofs, not interior modeling.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--asset',type=Path,required=True);p.add_argument('--lod',action='store_true');p.add_argument('--source-asset',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();r=check(a.asset,a.lod,a.source_asset);a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(0 if r['passed'] else 1)
