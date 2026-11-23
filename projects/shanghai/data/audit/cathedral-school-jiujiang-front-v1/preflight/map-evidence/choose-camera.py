from pathlib import Path
from hashlib import sha256
import gzip,json,math,runpy
import numpy as np,shapely
from shapely.geometry import shape,LineString,Point,box
from shapely.strtree import STRtree
w=Path(__file__).parent;proj=Path('/workspace/e-resource/projects/shanghai');p=w.parent/'pilot';read=lambda f:json.loads(f.read_bytes());sign=lambda f:sha256(f.read_bytes()).hexdigest()
ref=read(w/'original-review.json');place=read(w/'ground-placement-fragment.json');mf=read(p/'manifest.json');cam=read(w/'camera-choices.json');SS=runpy.run_path(str(proj/'data/audit/postal-office-v1/independent-glb-review-helpers.py'))['SerialScene'];sc=SS(p/'raw.glb')
h=math.radians(place['heading']);c=math.cos(h);s=math.sin(h);lat=place['lat'];lon=place['lng'];mn=math.pi*6371008.8/180;me=mn*math.cos(math.radians(lat));north0=math.asinh(math.tan(math.radians(lat)))
def en(xy):return np.column_stack(((xy[:,0]-lon)*me,(np.arcsinh(np.tan(np.radians(xy[:,1])))-north0)*me*180/math.pi))
def local(q):return np.column_stack([q[:,0]*c-q[:,1]*s,q[:,0]*s+q[:,1]*c])
def tolocal(q):return local(en(q))
def vector(q):x,y,z=q;return np.array([c*x+s*y,-s*x+c*y,z])
mask=shapely.transform(shape(place['replacement_geometry']),tolocal);table=json.loads(gzip.decompress((w/'inputs/feature-table.json.gz').read_bytes()))['features'];ob=[]
for f in table:
 poly=shape(f['geometry'])
 if poly.distance(Point(lon,lat))>.0020:continue
 geom=shapely.transform(poly,tolocal)
 if geom.distance(Point(38.3,0))>145:continue
 if f['localId']==1810:geom=geom.difference(mask)
 ob.append((f['localId'],float(f['height']),geom))
polys=np.array([x[2]for x in ob],dtype=object);height=np.array([x[1]for x in ob]);tree=STRtree(polys)
test=read(w.parent/'physical-rays.json')['models']['raw'];assert test['asset_sha256']==sign(p/'raw.glb')
rows=test['tests'];names=['west deep service door','recessed double door','east deep service door','bronze vertical plaque','bronze vertical plaque','west red brick gable','east red brick gable','west row 1 clear light 1','east row 1 clear light 1','west row 3 clear light 1','east row 3 clear light 1','central bay 1 row 2 clear light 1','central bay 2 row 3 raised stone mullion','central bay 3 row 2 clear light 1','portal dressed stone behind crest','jamb projecting arris'];seen={};targets=[];pts=[]
for label in names:
 opts=[item for item in rows if item['target']==label];num=seen.get(label,0);seen[label]=num+1;item=opts[num];point=item['surface']['point_enu_m'];targets.append((label+(' '+str(num+1) if len(opts)>1 else ''),point[0],point[2]));pts.append(point)
pts=np.array(pts);enu=np.array([vector(p)for p in pts]);trg=shapely.points(pts[:,:2]);labels=[r[0]for r in targets]
def evaluate(q,save=False,mesh=False):
 name,width,height_px=q['name'],q['width'],q['height'];m=q['camera'];be,pii=np.deg2rad([m['bearing'],m['pitch']]);f=height_px/(2*math.tan(math.radians(36.87)/2));di=f*(2*math.pi*6371008.8*math.cos(math.radians(m['center'][1])))/(512*2**m['zoom'])
 center=np.r_[en(np.array([m['center']]))[0],m['elevation']];eye=center+di*np.array([-math.sin(be)*math.sin(pii),-math.cos(be)*math.sin(pii),math.cos(pii)]);el=np.r_[local(np.array(eye[:2])[None,:])[0],eye[2]]
 d=enu-center;forward=d[:,0]*math.sin(be)+d[:,1]*math.cos(be);depth=di+forward*math.sin(pii)-d[:,2]*math.cos(pii);pa=m['padding'];px=(width+pa['left']-pa['right'])/2+(d[:,0]*math.cos(be)-d[:,1]*math.sin(be))*f/depth;py=(height_px+pa['top']-pa['bottom'])/2-(forward*math.cos(pii)+d[:,2]*math.sin(pii))*f/depth
 on=(px>=pa['left']+3)&(px<=width-pa['right']-3)&(py>=pa['top']+3)&(py<=height_px-pa['bottom']-3);lines=shapely.linestrings(np.stack((pts[:,:2],np.broadcast_to(el[:2],(len(pts),2))),axis=1));segix,obix=tree.query(lines,predicate='intersects');blocked=[[]for _ in pts]
 if len(segix):
  seg=shapely.intersection(lines[segix],polys[obix]);ent=shapely.distance(trg[segix],seg)/shapely.length(lines[segix]);z=pts[segix,2]+(el[2]-pts[segix,2])*ent
  for i,j,g in zip(segix,obix,height[obix]-z):
   if g>.05:blocked[i].append((ob[j][0],round(float(g),3)))
 visible=on&np.array([not r for r in blocked]);occlusion={}
 if mesh:
  for i in np.where(visible)[0]:
   d=pts[i]-el;l=np.linalg.norm(d);hit=sc.ray(el,d,l+.025);delta=None if hit is None else l-hit['distance_m'];visible[i]=delta is not None and abs(delta)<.05;occlusion[labels[i]]=dict(target_material=sc.ray([pts[i,0],2.2,pts[i,2]],[0,-1,0],4)['material'],first_material=hit['material']if hit else None,gap_m=round(float(delta),4)if delta is not None else None)
 a=list(map(int,visible));counts=dict(doors=sum(a[:3]),plaques=sum(a[3:5]),gables=sum(a[5:7]),windows=sum(a[7:14]),stone=sum(a[14:]),total=sum(a))
 result={'screen':name,'counts':counts,'camera':m,'camera_local':el.tolist(),'horizontal_projected_span_pixels':round(float(np.ptp(px)),2),'vertical_surface_span_pixels':round(float(np.ptp(py)),2)}
 if save:result.update(probes=[dict(feature=label,point_local=pt.tolist(),px=[round(float(x),2),round(float(y),2)],inside=bool(on[i]),blocked_by=blocked[i],self_check=occlusion.get(label),visible=bool(visible[i]))for i,(label,pt,x,y)in enumerate(zip(labels,pts,px,py))])
 return result
def score(q):
 r=q['scores'];a=[v['counts']for v in r];mn=lambda k:min(v[k]for v in a);return (mn('total'),mn('doors'),mn('gables'),mn('plaques'),min(v['vertical_surface_span_pixels'] for v in r),min(v['horizontal_projected_span_pixels']for v in r),-abs(q['bearing']-163))
short=[]
for q in cam['cases']:
 scores=[evaluate(v)for v in q['views']];short.append({**q,'scores':scores})
short.sort(key=score,reverse=True);final=[]
for q in short[:35]:
 q['scores']=[evaluate(v,save=True,mesh=True)for v in q['views']];final.append(q)
final.sort(key=score,reverse=True);q=final[0];print(q['id'],q['bearing'],q['pitch'],[(v['screen'],v['counts'])for v in q['scores']],flush=True)
res=dict(test_note='True signed overview module used for each candidate. Vertex-transformed archived raw GLB surface first intersections plus retained frozen source footprints/heights for occlusion. Compare both actual panel screen insets. Polygons/table volumes for nonsourced neighbors are conservative.',signed_camera_source_sha=cam['module_sha256'],model_sha256=sign(p/'raw.glb'),signed_city_table_sha=sign(w/'inputs/feature-table.json.gz'),retained_original_buildings=len(ob),grid_candidates=len(cam['cases']),second_stage_model_triangle_rays=len(final),winner={k:q[k]for k in ['id','bearing','pitch','focus','scores']},alternatives=[{k:x[k]for k in ['id','bearing','pitch','focus']}|{'counts':[r['counts']for r in x['scores']]}for x in final[1:8]])
(w/'map-camera-proof.json').write_text(json.dumps(res,ensure_ascii=False,indent=1)+'\n')
contract={**place,'partial_model':True,'overviewBearing':q['bearing'],'overviewPitch':q['pitch'],'overviewZoom':18.9,'maxDistance':680,'lod_switch_in_m':350,'lod_switch_out_m':435,'navigation':{'listed':False,'status':'从九江路观察原校舍尖券入口和两座山墙。'},'placement':{'status':'map-matched-photo-adjusted','source':'具名OSM 292718777 v4北墙西端、原城1810、市名录4A019、2018修缮实录与七个街景机位。门窗进深按现场影像估计。'},'model_scope':mf['scope']}
if q['focus']:contract['overview_focus_bounds_glb']=q['focus']
(w/'final-placement-contract.json').write_text(json.dumps(contract,ensure_ascii=False,indent=2)+'\n');print(sign(w/'final-placement-contract.json'))
