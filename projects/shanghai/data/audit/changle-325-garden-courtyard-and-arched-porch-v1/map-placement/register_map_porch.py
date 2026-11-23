"""Prepare a standalone city candidate row, keeping both courtyard components at the individual URL."""
import argparse,json,math,struct,hashlib,sys
from pathlib import Path
import numpy as np
from shapely.geometry import MultiPoint,Point,shape,mapping
from shapely.ops import unary_union,transform

def read_mesh(path):
 data=Path(path).read_bytes();n=struct.unpack_from('<I',data,12)[0];d=json.loads(data[20:20+n]);buf=memoryview(data)[28+n:]
 def values(i):
  a=d['accessors'][i];v=d['bufferViews'][a['bufferView']];t=np.dtype({5121:'u1',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
  return np.ndarray((a['count'],k),dtype=t,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',k*t.itemsize),t.itemsize))
 prims={}
 for part in d['meshes'][0]['primitives']:
  v=values(part['attributes']['POSITION']);idx=values(part['indices']).reshape(-1,3)
  mat=d['materials'][part['material']]['name'];prims[mat]=v[idx]
 return d,prims

def main(source,full,component,plot,output):
 take=lambda p:json.loads(Path(p).read_bytes());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 cams=take(source/'measurements/wing-cameras.json');frame=take(source/'measurements/porch-frame.json');registry=take(plot/'original-city-owners.json')
 X,Y=frame['frame_origin'][:2];lon0,lat0=cams['origin_wgs'];heading=cams['x_azimuth_deg']-90.;az=math.radians(cams['x_azimuth_deg']);e=111320*math.cos(math.radians(lat0));n=110860.
 def wgs(x,y):return lon0+(math.sin(az)*x-math.cos(az)*y)/e,lat0+(math.cos(az)*x+math.sin(az)*y)/n
 lng,lat=wgs(X,Y);my='xuhui-changle-325-garden-courtyard-and-arched-porch';dest='assets/models/candidates/'+my+'/';assets={};proof={};collision=[]
 for stage,key,filename in [('full','web','map-porch-web.glb'),('lod','lod','map-porch-lod.glb')]:
  raw=component/'whole'/(stage+'-source.glb');meta=take(raw.with_suffix('.geometry.json'));j,g=read_mesh(raw);_,alltris=read_mesh(full/(stage+'-source.glb'))
  maxd=0.;coverage=0;offset=np.array([X,0,-Y]);hi=0
  for mat,tri in alltris.items():
   idx=tri[:,:,0].mean(axis=1)<-7
   if not idx.any():continue
   t=g[mat];assert t.shape==tri[idx].shape,mat
   delta=np.abs(t+offset-tri[idx]);maxd=max(maxd,float(delta.max()));coverage+=int(idx.sum())
   if stage=='full' and mat in ['325 porch | sandy carved balustrade stone','325 porch | darker grey plinth course','325 garden | smoked entrance glass']:
    # A small section at +0.82 m above each newel foot, plus the actual door leaves.
    for h in [.82,2.23,3.12]:
     v=t[(t[:,:,1].min(1)<h)&(t[:,:,1].max(1)>h)]
     if len(v)==0:continue
     # Footprints of only the intersected triangles. Excludes the tiled canopy and stair walking faces.
     for f in v:
      ring=MultiPoint([(a,-z)for a,_,z in f]).convex_hull
      if ring.area>1e-8:collision.append(ring)
  assert maxd<.000004 and coverage==meta['triangles']
  packed=component/'assets'/filename;assets[key]={'file':dest+filename,'bytes':packed.stat().st_size,'sha256':sha(packed),'triangles':coverage}
  proof[key]={'complete_source':sha(full/(stage+'-source.glb')),'component_source':sha(raw),'packed':sha(packed),'component_triangles':coverage,'complete_triangles':sum(len(t)for t in alltris.values()),'restored_position_max_abs_m':maxd,'parts':meta['parts'],'source_matched':True}
  if stage=='full':bounds=meta['bounds_glb']
 g=unary_union(collision).buffer(.018,join_style=2).buffer(-.018,join_style=2).simplify(.025)
 kept=[h for h in getattr(g,'geoms',[g])if h.area>.005]; g=unary_union(kept)
 # Preserve long but thin closed leaves as blocking strips even when face projections have zero area.
 def add_door_strip(g):
  _,prims=read_mesh(component/'whole/full-source.glb');v=prims['325 garden | smoked entrance glass'].reshape(-1,3)
  return unary_union([g,MultiPoint([(a,-z)for a,y,z in v]).convex_hull.buffer(.012).simplify(.009)])
 g=add_door_strip(g);collision_geom=mapping(transform(lambda x,y:(wgs(np.asarray(x)+X,np.asarray(y)+Y)),g))
 r=math.radians(heading);ct=registry['near_origin_wgs84'];k=6378137*math.cos(math.radians(ct[1]));pX=k*math.radians(lng-ct[0]);pZ=-k*(math.asinh(math.tan(math.radians(lat)))-math.asinh(math.tan(math.radians(ct[1]))))
 note='长乐路325号石券廊与十级石阶按院内实拍定位。专页另展临窗弧翼。整院绝对位置含街站定位误差，原城附近楼体均保留。'
 row={'id':my,'name':'长乐路325号院内红瓦券廊与石阶','kind':'building','candidate_id':my,'detail_level':'architectural','districtId':'310104','district_name':'徐汇区','architecture_style':'外观候选 · 地图对齐','lng':lng,'lat':lat,'heading':heading,'scale':1,'altitude':0,'height_m':bounds['max'][1],'height_estimated':True,'bounds_glb':bounds,'assets':assets,'model':assets['web']['file'],'lod_model':assets['lod']['file'],'web_bytes':assets['web']['bytes'],'web_sha256':assets['web']['sha256'],'lod_bytes':assets['lod']['bytes'],'lod_sha256':assets['lod']['sha256'],'triangles':assets['web']['triangles'],'lod_triangles':assets['lod']['triangles'],'individual_page':'changle-325-garden-courtyard-and-arched-porch.html','candidate_manifest':dest+'manifest.json','navigation':{'listed':False},'overviewZoom':19.95,'overviewBearing':149,'overviewPitch':55,'maxDistance':840,'lod_switch_in_m':130,'lod_switch_out_m':180,'collision_geometry':collision_geom,'replacement_geometry':None,'partial_model':True,'model_scope':'院内券廊、红瓦坡、双门扇和十级石阶；弧翼另见同一建筑专页。','source_feature_ids':{'building':[],'building_part':[]},'placement':{'status':'estimated','note':note},'detail_note':note,'complete_photo_reconstruction_accepted':False}
 for k,obj in [('candidate-row.json',row),('placement.json',{v:row[v]for v in ('id','lng','lat','heading','scale','altitude','placement','navigation','collision_geometry','replacement_geometry','source_feature_ids','partial_model','model_scope','maxDistance','lod_switch_in_m','lod_switch_out_m','overviewZoom','overviewBearing','overviewPitch')}),('model-separation.json',{'map_meshes':proof,'source_to_map_pivot_m':[X,Y,0],'map_model_to_original_tile_colmajor':[math.cos(r),0,math.sin(r),0,0,1,0,0,-math.sin(r),0,math.cos(r),0,pX,0,pZ,1],'native_ids_hidden':[],'placement_uncertainty':'About 2–4 m absolute; neither the unusually high generalized 1869 wall nor the aerial roof edge was used to move the measured staircase.'})]:
  (output/k).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__)
 for n in ['source','full','component','plot','output']:a.add_argument(n,type=Path)
 c=a.parse_args();main(c.source,c.full,c.component,c.plot,c.output)
