#!/usr/bin/env python3
"""Actual V3 only-addition proof and finite ridge-seat contacts, no generation.

Every V2 part's material and ordered directed POSITION/NORMAL triangle stream
must survive byte-exact after expanding indices. Only56 named seats may be new.
"""
from pathlib import Path
from collections import defaultdict,Counter
import argparse,hashlib,json,struct,time
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;V2=ROOT.parent/'v2'
BASELINE_SHA='a96343eef1f9c11a38dce37b113545a8abea720ffed3b58952024e51c76b73af'
def need(ok,message):
 if not ok:raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def filemeta(p):
 b=p.read_bytes();return {'file':str(p),'bytes':len(b),'sha256':sha(b)}
def loadraw(path):
 data=path.read_bytes();need(struct.unpack_from('<4sII',data)==(b'glTF',2,len(data)),'Bad GLB');n,k=struct.unpack_from('<II',data,12);need(k==0x4e4f534a,'Bad JSON chunk');doc=json.loads(data[20:20+n]);bn,bk=struct.unpack_from('<II',data,20+n);need(bk==0x004e4942 and 28+n+bn==len(data),'Bad BIN');binary=memoryview(data)[28+n:]
 sp=path.with_suffix('.geometry.json');sb=sp.read_bytes();side=json.loads(sb);need(side['sha256']==sha(data) and side['bytes']==len(data),'Sidecar/raw SHA mismatch')
 need(len(data)<100_000_000 and len(doc['nodes'])==1 and doc['nodes'][0].get('mesh')==0 and len(doc['meshes'])==1,'Unexpected size/scene');need(not any(x in doc['nodes'][0] for x in ['matrix','translation','rotation','scale']),'Node transform changed');need(not doc.get('images') and not doc.get('textures'),'Unexpected image payload')
 def acc(i):
  a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];need(not v.get('extensions') and not v.get('byteStride') and 'sparse' not in a,'Compressed/strided raw unsupported');w={'SCALAR':1,'VEC3':3}[a['type']];return np.frombuffer(binary,dtype={5125:'<u4',5126:'<f4'}[a['componentType']],offset=v.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']*w).reshape(-1,w)
 bymat=defaultdict(list)
 for row in side['part_summary']:bymat[row['material']].append(row)
 parts={};occurrences=Counter();mats={};triangles=0
 for pr in doc['meshes'][0]['primitives']:
  mat=doc['materials'][pr['material']];name=mat['name'];need(name not in mats,'Duplicate material name');mats[name]=mat;pos=acc(pr['attributes']['POSITION']);norm=acc(pr['attributes']['NORMAL']);ids=acc(pr['indices']).ravel().reshape(-1,3);cursor=0
  for row in bymat[name]:
   pair=(row['label'],name);ordinal=occurrences[pair];occurrences[pair]+=1;key=(*pair,ordinal);count=row['triangles'];parts[key]={'row':row,'pos':pos,'norm':norm,'indices':ids[cursor:cursor+count]};cursor+=count
  need(cursor==len(ids),'Part layout mismatch');triangles+=len(ids)
 need(triangles==side['triangles'] and len(parts)==side['parts'],'Global part counts differ')
 return {'path':path,'data':data,'doc':doc,'side':side,'parts':parts,'materials':mats,'side_sha256':sha(sb),'raw':{'file':str(path),'bytes':len(data),'sha256':sha(data)}}
def expanded(part):
 ids=part['indices'].ravel();return np.concatenate((part['pos'][ids],part['norm'][ids]),axis=1).astype('<f4',copy=False).tobytes()
def enu_tri(part):return part['pos'][part['indices']].astype(float)[:,:,[0,2,1]]*[1,-1,1]
def z(t,xy,top):
 a=t[:,0,:2];b=t[:,1,:2]-a;c=t[:,2,:2]-a;d=np.asarray(xy)-a;det=b[:,0]*c[:,1]-b[:,1]*c[:,0];ix=np.flatnonzero(det>1e-12 if top else det< -1e-12)
 if not len(ix):return None
 b,c,d,det,t=b[ix],c[ix],d[ix],det[ix],t[ix];u=(d[:,0]*c[:,1]-d[:,1]*c[:,0])/det;v=(b[:,0]*d[:,1]-b[:,1]*d[:,0])/det;ok=(u>=-1e-7)&(v>=-1e-7)&(u+v<=1+1e-7)
 if not ok.any():return None
 zz=t[:,0,2]+u*(t[:,1,2]-t[:,0,2])+v*(t[:,2,2]-t[:,0,2]);return float(max(zz[ok]) if top else min(zz[ok]))
def check(raw_path,baseline):
 start=time.monotonic();old=loadraw(baseline);new=loadraw(raw_path);need(old['raw']['sha256']==BASELINE_SHA,'Wrong frozenV2raw');need(len(old['parts'])==17983,'V2part count changed')
 need(old['materials']==new['materials'],'Existing material definitions changed')
 for name,field in [('geometry-input.json','source_geometry_sha256'),('calibration.json','calibration_sha256')]:
  need((ROOT/name).read_bytes()==(V2/name).read_bytes(),'Unrelated source/calibration changed');need(new['doc']['extras'][field]==sha((ROOT/name).read_bytes())==old['doc']['extras'][field],'Raw provenance differs')
 need(new['doc']['extras']['id']==old['doc']['extras']['id']=='xuhui-longhua-pagoda','Wrong building')
 lock=json.loads((ROOT/'build-source-files.json').read_text());locks={q['file']:q for q in lock['files']}
 for name in ['build_model.py','common/photo_architecture.py','geometry-input.json','calibration.json']:
  q=locks[name];b=(ROOT/name).read_bytes();need(len(b)==q['bytes'] and sha(b)==q['sha256'],'Final source lock changed: '+name)
 previous_proof=json.loads((V2/'independent-review/actual-raw-structure.json').read_text());need(previous_proof['structure_passed'] is True and previous_proof['raw']['sha256']==BASELINE_SHA,'Prior actual structure proof mismatch')
 h_old=hashlib.sha256();h_new=hashlib.sha256();mismatches=[];preserved=0
 for key,part in old['parts'].items():
  if key not in new['parts']:mismatches.append({'key':key,'reason':'missing'});continue
  a=expanded(part);b=expanded(new['parts'][key]);tag=json.dumps(key,separators=(',',':'),ensure_ascii=False).encode();h_old.update(tag);h_old.update(struct.pack('<Q',len(a)));h_old.update(a);h_new.update(tag);h_new.update(struct.pack('<Q',len(b)));h_new.update(b)
  if a!=b:mismatches.append({'key':key,'reason':'directed triangle position/normal stream changed'})
  else:preserved+=1
 extra=set(new['parts'])-set(old['parts']);expected={(f'L{L}/continuous-grey-ridge-seat{c}','tile 1',0) for L in range(1,8) for c in range(8)}
 need(extra==expected,'V3 additions are not exactly56 expected ridge seats');need(not mismatches,'Old geometry changed: '+str(mismatches[:5]))
 topology=[];cache={}
 def part(label,material=None):
  matches=[k for k in new['parts'] if k[0]==label and (material is None or k[1]==material)];need(len(matches)==1,'Ambiguous part '+label);key=matches[0]
  if key not in cache:cache[key]=enu_tri(new['parts'][key])
  return cache[key]
 for key in sorted(extra):
  p=new['parts'][key];t=enu_tri(p);_,inv=np.unique(t.reshape(-1,3),axis=0,return_inverse=True);ids=inv.reshape(-1,3);e=np.concatenate((ids[:,[0,1]],ids[:,[1,2]],ids[:,[2,0]]));_,ei,ec=np.unique(np.sort(e,axis=1),axis=0,return_inverse=True,return_counts=True);bal=np.bincount(ei,weights=np.where(e[:,0]<e[:,1],1,-1));x=t-t.mean(axis=(0,1));volume=float(np.einsum('ij,ij->i',x[:,0],np.cross(x[:,1],x[:,2])).sum()/6);area=np.linalg.norm(np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]),axis=1)
  # Compare stored GLB normals to actual GLB triangle winding, no axis ambiguity.
  gt=p['pos'][p['indices']].astype(float);gn=p['norm'][p['indices']].astype(float);cross=np.cross(gt[:,1]-gt[:,0],gt[:,2]-gt[:,0]);cross/=np.linalg.norm(cross,axis=1)[:,None];gn/=np.linalg.norm(gn,axis=2)[:,:,None];angle=np.degrees(np.arccos(np.clip(np.einsum('tj,tkj->tk',cross,gn),-1,1)))
  q={'label':key[0],'triangles':len(t),'non_two_edges':int((ec!=2).sum()),'unpaired_edges':int((bal!=0).sum()),'zero_area_triangles':int((area<=1e-12).sum()),'signed_volume_m3':volume,'max_normal_error_degrees':float(angle.max())};q['passed']=q['non_two_edges']==q['unpaired_edges']==q['zero_area_triangles']==0 and volume>0 and q['max_normal_error_degrees']<.001;topology.append(q)
 g=json.loads((ROOT/'geometry-input.json').read_text());cal=json.loads((ROOT/'calibration.json').read_text());ring=np.asarray(g['polygon_local_east_north'],float)
 if np.array_equal(ring[0],ring[-1]):ring=ring[:-1]
 summary={k:{'samples':0,'min_m':float('inf'),'max_m':-float('inf'),'nonpositive':0,'worst':None} for k in ['substrate_overlap','ridge_overlap','tile_above_seat_bottom','seat_top_above_tile']};negative={}
 def record(kind,value,loc):
  q=summary[kind];q['samples']+=1;q['max_m']=max(q['max_m'],value);q['nonpositive']+=int(value<=0)
  if value<q['min_m']:q['min_m']=value;q['worst']=loc
 for v in cal['levels']:
  L=v['level'];inner=v['wall_scale']*.945 if L<7 else .075;roof=part(f'L{L}/continuous-curved-roof')
  for corner in range(8):
   seat=part(f'L{L}/continuous-grey-ridge-seat{corner}');ridge=part(f'L{L}/continuous-upturned-corner-ridge{corner}');axis=ring[corner]/np.linalg.norm(ring[corner]);side=np.array([-axis[1],axis[0]])
   prev=(corner-1)%8;cols=max(8,round(np.linalg.norm((ring[(prev+1)%8]-ring[prev])*v['roof_scale'])/.32));prefixes=[f'L{L}/pan/e{corner}/c0/',f'L{L}/pan/e{prev}/c{cols-1}/'];panlabels=[key[0] for key in new['parts'] if any(key[0].startswith(prefix) for prefix in prefixes)];pans=[part(label) for label in panlabels]
   for tt in [.05,.20,.40,.60,.80,.95,.995]:
    center=ring[corner]*(inner*(1-tt)+v['roof_scale']*tt)
    for offset in [-.025,0,.025]:
     xy=center+side*offset;bottom=z(seat,xy,False);top=z(seat,xy,True);rb=z(ridge,xy,False);rs=z(roof,xy,True);need(None not in (bottom,top,rb,rs),'Contact ray miss')
     loc={'level':L,'corner':corner,'t':tt,'offset_m':offset};record('substrate_overlap',rs-bottom,loc);record('ridge_overlap',top-rb,loc)
     for kind,shift in [('substrate_overlap',rs-bottom+.005),('ridge_overlap',top-rb+.005)]:
      if kind not in negative:
       shifted=seat.copy();shifted[:,:,2]+=shift if kind=='substrate_overlap' else -shift;bad=rs-z(shifted,xy,False) if kind=='substrate_overlap' else z(shifted,xy,True)-rb;need(bad<-.0049,'Contact negative control failed');negative[kind]={'in_memory_seat_shift_m':shift,'gap_detected_m':bad,'rejected':True}
     tile_heights=[h for t in pans if (h:=z(t,xy,True)) is not None]
     if tile_heights:
      tz=max(tile_heights);record('tile_above_seat_bottom',tz-bottom,loc);record('seat_top_above_tile',top-tz,loc)
 contact=all(q['nonpositive']==0 and q['samples']>0 for q in summary.values());tp=all(q['passed'] for q in topology);passed=preserved==17983 and len(extra)==56 and tp and contact
 return {'schema':'longhua-v3-actual-preservation-and-ridge-contact-v1','passed':passed,'raw':new['raw'],'baseline_raw':old['raw'],'raw_part_manifest_sha256':new['side_sha256'],'baseline_part_manifest_sha256':old['side_sha256'],'preserved_old_parts_count':preserved,'new_ridge_seats_count':len(extra),'old_geometry_materials_byte_exact':not mismatches and old['materials']==new['materials'],'old_part_comparison':'Material definitions equal; every oldpart matched by(label,material,occurrence) and expanded ordered directed FLOAT32 POSITION+NORMAL triangle bytes. Bufferindex reordering ignored.','old_stream_aggregate_sha256':h_old.hexdigest(),'new_preserved_stream_aggregate_sha256':h_new.hexdigest(),'old_geometry_mismatches':mismatches[:20],'new_seat_topology_passed':tp,'new_seat_topology':topology,'finite_contact_passed':contact,'contact_scope':{'levels':[1,2,3,4,5,6,7],'corners':[0,1,2,3,4,5,6,7],'t':[.05,.20,.40,.60,.80,.95,.995],'lateral_offsets_m':[-.025,0,.025],'t_above_1_cantilever_not_checked':True},'contact_summary':summary,'negative_controls':negative,'source_lock':filemeta(ROOT/'build-source-files.json'),'geometry_input':filemeta(ROOT/'geometry-input.json'),'calibration':filemeta(ROOT/'calibration.json'),'elapsed_seconds':time.monotonic()-start,'model_appearance_accepted':False,'native_or_browser_accepted':False,'generated_geometry':False,'scope':'Actual exported V3 comparison against frozen V2 and finite actual triangle contacts. This does not prove continuous all-point contact, absence of unrelated self-intersections, material/shape realism, native visual approval or browser acceptance. ExistingV1/V2reports and allmodelbytes are unmodified.'}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--raw',type=Path,required=True);p.add_argument('--baseline',type=Path,default=V2/'run-v2/raw/xuhui-longhua-pagoda-raw.glb');p.add_argument('--output',type=Path,required=True);a=p.parse_args();dest=a.output.resolve();need(dest.is_relative_to(HERE) and not dest.exists(),'Use a new report in this independent-review directory');report=check(a.raw.resolve(),a.baseline.resolve());text=json.dumps(report,ensure_ascii=False,indent=2)+'\n';need(len(text.encode())<120000,'Unexpected report growth');dest.write_text(text);print(json.dumps({k:report[k] for k in ['passed','raw','preserved_old_parts_count','new_ridge_seats_count','new_seat_topology_passed','finite_contact_passed','contact_summary','elapsed_seconds']},indent=2));raise SystemExit(0 if report['passed'] else 1)
if __name__=='__main__':main()
