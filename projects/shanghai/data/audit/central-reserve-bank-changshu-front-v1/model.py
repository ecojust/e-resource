"""Read all three delivered variants without caching a second uncompressed GLB and test the walkable entrance in the original city."""
from pathlib import Path
from hashlib import sha256
from urllib.request import urlopen
import json,math,gzip,runpy,sys,os,zstandard
import numpy as np
import shapely as g
from shapely import geometry as G
from shapely.geometry import Point,box
w=Path(os.environ.get('CHANGSHU_WORK',Path(__file__).parent));project=Path(os.environ.get('CHANGSHU_PROJECT',Path(__file__).resolve().parents[2]));assets=Path(sys.argv[1])if len(sys.argv)>1 else Path(os.environ['CHANGSHU_CHECKED'])
manifest=assets/'manifest.json';ri=lambda f:json.loads(f.read_bytes());sha=lambda data:sha256(data).hexdigest();save=lambda f,doc:f.write_text(json.dumps(doc,ensure_ascii=False,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else str(v))+'\n')
m=ri(manifest);bind=ri(w/'footprint-review.json');orig=ri(w/'original-near-far.json');crop=ri(w/'proposed-source-cut.json');heading=orig['inside_bearing'];lon=orig['anchor']['lng'];lat=orig['anchor']['lat'];k=6371008.8*math.cos(math.radians(lat));loglat=math.asinh(math.tan(math.radians(lat)));h=math.radians(heading);axes=np.array([[math.cos(h),-math.sin(h)],[math.sin(h),math.cos(h)]])
def wgs(x):
 e,n=(x@axes).T;return np.column_stack((lon+np.degrees(e/k),np.degrees(np.arctan(np.sinh(loglat+n/k)))))
def loc(x):
 return np.column_stack((np.radians(x[:,0]-lon)*k,(np.arcsinh(np.tan(np.radians(x[:,1])))-loglat)*k))@axes.T
def verify_host_asset(name,d,record):
 p=assets/name;packed=assets/(name+'.zst')
 if p.exists():b=p.read_bytes()
 else:
  physical=packed.read_bytes();assert sha(physical)==record[name]['archive_sha256'];b=zstandard.ZstdDecompressor().decompress(physical)
 assert len(b)==record[name]['bytes']and sha(b)==record[name]['sha256']
 if d:assert sha(b)==d['sha256'] and len(b)==d['bytes']
 return b
class Asset:
 def __init__(self,name,data):self.name=name;self.data=data
 def read_bytes(self):return self.data
def make_scenes():
 record=ri(assets/'six-source-backed-exports.json');caps=runpy.run_path(str(project/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'];out={}
 for v in ('raw','full','lod'):
  d=m['assets'][v];plain=verify_host_asset(d['file'],d,record)
  name=d['file']if v=='raw'else 'decoded-'+v+'.glb';dblob=plain if v=='raw'else verify_host_asset(name,None,record)
  scene=caps(Asset(name,dblob));assert len(scene.tri)==d['triangles'];out[v]=scene
 assert abs(out['full'].tri.max(axis=(0,1))[2]-20.45)<.1
 return out
def main():
 scenes=make_scenes();section=runpy.run_path(str(project/'data/audit/sino-french-school-v1/verify-placement.py'))['solid_section']
 forms={v:section(scene.tri,.605)for v,scene in scenes.items()};front=G.shape(crop['cut_local']);owner=G.Polygon(orig['original_vertices_in_model_frame'])
 interior=front.intersection(owner).intersection(box(-20,.44,20,15)).difference(box(-1.30,.44,1.30,2.78))
 collide=g.union_all([interior,*forms.values()],grid_size=.001).simplify(.002,preserve_topology=True)
 assert collide.is_valid
 points=[]
 def probe(name,x,y,solid):
  p=Point(x,y);here=collide.covers(p);mapblock=here or(not front.covers(p)and owner.covers(p));assert mapblock==solid,(name,x,y,here,mapblock,solid)
  points.append(dict(name=name,xy=[x,y],wgs84=wgs(np.array([[x,y]]))[0].tolist(),model_obstacle=here,source_cut=front.covers(p),expected_map='building'if mapblock else None))
 for x in (-.54,0,.54):
  for y in (-3.45,-2.84,-2.47,-1.80,-.20,.34,1.23,2.00,2.64):probe('Garden, steps and actual open central vestibule',x,y,False)
  for y in (2.825,3.24,5.70):probe('Measured back of vestibule and retained house',x,y,True)
 for x in (-5.14,5.14):
  probe('Garden in front of outside bay',x,-3.3,False);probe('Solid photographed outer bay',x,.16,True);probe('Registered original house behind outside bay',x,1.1,True)
 for x in (-4.86,4.86):probe('Stone stair end post',x,-2.52,True)
 for x in (-1.255,1.255):probe('Side of open door frame',x,.20,True)
 for xy in [(-11,9),(10.50,9),(0,12),(-5,29)]:probe('Uncut side wing or original back building',*xy,True)
 for side,ang in [(-1,67),(1,73)]:
  xx=side*(1.23-.58*math.cos(math.radians(ang)));yy=.24+.58*math.sin(math.radians(ang));assert any(forms[v].distance(Point(xx+dx,yy))<.022 for v in ('full','lod')for dx in (-.06,.06,0))
 ref=next(v for v in bind['owners']if v['local_id']==3343)
 r=ri(w/'metadata.json');caps=dict(geometry=g.geometry.mapping(g.transform(G.MultiLineString(crop['geometry']['far']['seams']),wgs)),base_m=0,roof_m=orig['mesh']['far']['roof_height'],height_reference=r['origin'],far_sha256=r['far']['sha256'])
 geom={v:dict(triangles=len(s.tri),shape_area_m2=forms[v].area,asset_sha256=m['assets'][v]['sha256'],decoded_sha256=s.asset['sha256'])for v,s in scenes.items()}
 glb=m['assets']['raw']['bounds_gltf_m']
 contract=dict(id=m['id'],owner=dict(macro_id=bind['frozen_macro'],feature_local_id=3343),source_feature_ids=dict(building=[ref['key'][9:]],building_part=[]),replacement_geometry=crop['cut_wgs'],collision_geometry=G.mapping(g.transform(collide,wgs)),source_section_caps=caps,lng=lon,lat=lat,heading=heading,scale=1,altitude=0,model_geometry_sha256={k:m['assets'][r]['sha256']for k,r in [('raw','raw'),('web','full'),('lod','lod')]},bounds_glb=dict(min=glb[0],max=glb[1]),overviewBearing=333,overviewPitch=48,overviewZoom=19.6,maxDistance=435,lod_switch_in_m=610,lod_switch_out_m=745,navigation=dict(listed=False,status='自东南花园望向门阶、三跨石栏及两侧退翼。'),placement=dict(status='map-aligned',note='4B021具名足印与原城3343吻合，仅将凸出三跨及回折接到保留两翼。'),partial_model=True,model_scope=m['scope'])
 # Rectangle and polygon validity are checked by the production builder.
 sys.path.insert(0,str(project/'tools'));from build_candidate_city_integrations import checked_geometry
 checked_geometry(contract['collision_geometry'],'Changshu open portal collision',collision=True);checked_geometry(contract['replacement_geometry'],'Changshu projecting front')
 save(w/'final-placement-contract.json',contract);save(w/'placement-geometry.json',dict(id=m['id'],manifest_sha256=sha(manifest.read_bytes()),source_sha256=sha((w/'footprint-review.json').read_bytes()),checker_sha256=sha(Path(__file__).read_bytes()),source_variants=crop['geometry'],cap_segments=len(crop['geometry']['far']['seams']),neighbors=crop['other_owners'],assets=geom,collision_m2=collide.area,collision_height_m=.605,ground_probes=points))
 print('ground',len(points),'collision',collide.area,'shapes',[(k,v['shape_area_m2'])for k,v in geom.items()])
if __name__=='__main__':main()
